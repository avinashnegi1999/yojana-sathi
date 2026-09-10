"""Telegram adapter. Thin: translates Reply/ChannelMessage, holds no logic.

# * Long polling (getUpdates), not a webhook. A webhook needs a public URL, TLS
# * termination and a platform that stays awake — three ways for deploy day to
# * fail. Long polling needs an outbound connection and nothing else, which is
# * why the deploy gate can be hit in week 6 instead of debugged in week 6.
#
# * urllib only. One JSON POST and one multipart upload do not justify a
# * dependency; a container that installs nothing cannot fail to install.
#
# ! The Telegram chat id routes messages and never leaves this file. The event
# ! log's session id is an unrelated uuid4 — see sathi/metrics/events.py.
"""

import http.client
import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid

from sathi.channels.base import Button, Reply
from sathi.channels.router import Router
from sathi.core.content import DEFAULT_LANG, s
from sathi.core.schemes import Scheme
from sathi.metrics.events import EventLog
from sathi.pack import links

class TelegramError(Exception):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT_S = 65  # must exceed the long-poll timeout below
_POLL_S = 50

# ! run_forever used to retry with no delay at all. A recoverable blip was fine
# ! — getUpdates blocks for _POLL_S, so the loop paced itself. A PERMANENT
# ! error does not block: a revoked token returns 401 immediately, and the loop
# ! became a hot spin burning a core and writing the same line to the log
# ! forever. Back off on repeated failure, reset the moment a poll succeeds.
_BACKOFF_START_S = 1.0
_BACKOFF_MAX_S = 60.0

# ! Telegram only lets a bot delete a message less than 48 hours old, so /clear
# ! can never wipe everything. We track ids per chat and cap the list — a
# ! long-running chat must not grow memory without bound.
_CLEAR_WINDOW_H = 48
_MAX_TRACKED = 400

# ! Tracking alone is not enough: it lives in memory, so every restart forgets
# ! messages that are still well inside the 48-hour window. /clearall therefore
# ! also walks message ids backwards from the command itself. In a private chat
# ! ids are sequential, so this reaches messages this process never saw.
#
# ! deleteMessages takes up to 100 ids per call, so a 1000-message window costs
# ! 10 requests instead of 1000. One-at-a-time made /clearall unusable on a long
# ! chat — a real complaint on the first day of use.
_CLEAR_SCAN_BACK = 1000
_DELETE_BATCH = 100
# ! Bounds on the fallback path, so one /clearall cannot cost a thousand
# ! requests and leave the bot flood-limited for minutes afterwards. Both count
# ! FUTILE work only — deleting messages that are really there is the job.
_WASTED_DELETE_BUDGET = 25     # consecutive deletes that found nothing
_EMPTY_CHUNKS_BEFORE_STOP = 2  # consecutive fruitless chunks before giving up
# * Past the 48-hour edge Telegram refuses every delete, so a run of REFUSALS
# * means we have walked off the end and can stop instead of burning 400 calls.
# ! A gap of already-deleted ids is not a refusal and must not stop the walk.
# ! Telegram says "message to delete not found" for those, and "message can't be
# ! deleted" once a message is too old — different answers to different
# ! questions. Conflating them made /clearall stop dead after a /clear, which is
# ! exactly the case a second clear is for.
_CLEAR_REFUSAL_STREAK = 40

def _call(token: str, method: str, payload: dict) -> dict:
    # ! Drop keys we have no value for. Telegram rejects an explicit null
    # ! reply_markup with a bare "400 Bad Request" — omitting the key is the
    # ! documented way to send a message with no keyboard.
    payload = {k: v for k, v in payload.items() if v is not None}
    req = urllib.request.Request(
        API.format(token=token, method=method),
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json"},
    )
    return _request(req, method)


def _request(req: urllib.request.Request, method: str) -> dict:
    """Classify failures at the wire boundary, for JSON and uploads alike."""
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # ! Telegram puts the actual reason in the body. A bare "400 Bad Request"
        # ! in the log costs an hour; the description costs nothing to keep.
        try:
            body = json.loads(e.read().decode("utf-8"))
        except (ValueError, OSError, http.client.HTTPException):
            body = {}
        if not isinstance(body, dict):
            body = {}
        detail = body.get("description", "")
        parameters = body.get("parameters") or {}
        retry_after = parameters.get("retry_after") if isinstance(parameters, dict) else None
        # ! Wait here so even optional audio or callback acknowledgements cannot
        # ! swallow a 429 and immediately issue another request. No delivery retry.
        if e.code == 429 and isinstance(retry_after, int) and retry_after > 0:
            time.sleep(retry_after)
        raise TelegramError(f"{method} failed: {e.code} {detail or e.reason}", e.code) from e
    except (OSError, http.client.HTTPException, ValueError) as e:
        # ! A reset/truncated response is a network failure. Catch it here so a
        # ! genuine file or parsing error in a handler still takes the reset path.
        raise urllib.error.URLError(f"{method}: {type(e).__name__}") from e


def _upload(token: str, chat_id: str, filename: str, blob: bytes, caption: str) -> dict:
    """multipart/form-data by hand — one upload does not need a library."""
    boundary = f"----sathi{uuid.uuid4().hex}"
    ctype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    parts: list[bytes] = []
    for key, value in (("chat_id", chat_id), ("caption", caption[:1024])):
        parts += [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            value.encode("utf-8"),
            b"\r\n",
        ]
    parts += [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="document"; filename="{filename}"\r\n'.encode(),
        f"Content-Type: {ctype}\r\n\r\n".encode(),
        blob,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    body = b"".join(parts)
    req = urllib.request.Request(
        API.format(token=token, method="sendDocument"),
        data=body,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"},
    )
    return _request(req, "sendDocument")


# * Telegram failures split in two, and the difference decides whether a worker
# * keeps their answers. "Too Many Requests" and the 5xx family mean the API is
# * busy or broken and will work again shortly — the conversation is fine. A 400
# * means we sent something Telegram refused, which leaves the turn half-applied.
# * Use the HTTP status, never a number that happens to occur in its description.


def _is_transient(err: TelegramError) -> bool:
    """True when retrying later is the right response and the session should live."""
    return err.status == 429 or (err.status is not None and 500 <= err.status < 600)


def keyboard(buttons: tuple[Button, ...]) -> dict | None:
    """Two per row: big tap targets for a worker on a cheap phone outdoors."""
    if not buttons:
        return None
    rows = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
    return {
        "inline_keyboard": [
            [{"text": b.label[:64], "callback_data": b.value[:64]} for b in row]
            for row in rows
        ]
    }


class TelegramBot(Router):
    """Sessions, commands and languages come from Router. This is the wire."""

    channel = "telegram"

    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None,
                 token: str | None = None) -> None:
        super().__init__(schemes, log)
        self.token = token or os.environ.get("TELEGRAM_TOKEN", "")
        if not self.token:
            raise TelegramError("TELEGRAM_TOKEN is not set — see .env.example")
        # ! chat_id -> [(message_id, sent_at)] so /clear has something to delete.
        # ! In memory only: it dies with the process, like the profiles do.
        self._sent: dict[str, list[tuple[int, float]]] = {}
        # ! chat_id -> pack tokens handed to that chat. /clear deletes the
        # ! messages; without this it would leave the LINK readable, which is
        # ! the one part of the conversation that outlives the chat.
        self._tokens: dict[str, list[str]] = {}
        self._offset = 0

    # * ------------------------------------------------------------- sending

    def send(self, chat_id: str, reply: Reply) -> None:
        payload = {"chat_id": chat_id, "text": reply.text}
        markup = keyboard(reply.buttons)
        if markup is not None:
            # ! Only include the key when there IS a keyboard. A message with no
            # ! buttons — the age question, every info command — must not carry
            # ! "reply_markup": null, which Telegram answers with a bare 400.
            payload["reply_markup"] = markup
        sent = _call(self.token, "sendMessage", payload)
        message_id = (sent.get("result") or {}).get("message_id")
        self._track(chat_id, message_id)
        if markup is not None:
            self._active_keyboard.pop(chat_id, None)
            if message_id:
                self._active_keyboard[chat_id] = message_id
        if reply.audio is not None:
            try:
                up = _upload(self.token, chat_id, reply.audio.name,
                             reply.audio.read_bytes(), "")
                # ! Track the upload too, or /clear leaves it behind. _track
                # ! ignores a missing id, so a malformed response is harmless.
                self._track(chat_id, (up.get("result") or {}).get("message_id"))
            except Exception:  # noqa: BLE001 — optional audio cannot invalidate delivered text
                pass  # * audio is an extra; the text already carried the message
        if reply.document is not None:
            filename, blob = reply.document
            up = _upload(self.token, chat_id, filename, blob, "")
            # ! The pack carries the answer recap. An untracked pack survives
            # ! /clear, which is the one thing /clear exists to prevent.
            self._track(chat_id, (up.get("result") or {}).get("message_id"))
            # ! The file is sent FIRST and always. The link is an addition, not
            # ! a replacement: it dies in an hour and dies on restart, while a
            # ! saved file survives both. Betting the whole delivery on a link
            # ! nobody has field-tested is how a worker ends up with nothing.
            self._send_pack_link(chat_id, blob)

    def _send_pack_link(self, chat_id: str, blob: bytes) -> None:
        """Offer the same sheet as a link. Silent no-op when links are off."""
        if not links.base_url():
            return
        lang = self._lang.get(chat_id, DEFAULT_LANG)
        try:
            token = links.publish(blob)
            sent = _call(self.token, "sendMessage", {
                "chat_id": chat_id,
                "text": s("link.ready", lang, url=links.url_for(token)),
                # ! Telegram fetches a link to build a preview card, which would
                # ! open the worker's sheet on Telegram's servers before she
                # ! touches it — and paste a piece of it into the chat.
                "link_preview_options": {"is_disabled": True},
            })
            self._tokens.setdefault(chat_id, []).append(token)
            self._track(chat_id, (sent.get("result") or {}).get("message_id"))
        except Exception as e:  # noqa: BLE001 — the file already went; a link is a bonus
            print(f"[telegram] pack link failed: {type(e).__name__}")

    # * -------------------------------------------------------------- /clear

    def _track(self, chat_id: str, message_id: int | None) -> None:
        """Remember a message id so /clear can delete it later."""
        if not message_id:
            return
        seen = self._sent.setdefault(chat_id, [])
        seen.append((message_id, time.time()))
        if len(seen) > _MAX_TRACKED:
            del seen[:-_MAX_TRACKED]

    def _delete(self, chat_id: str, message_id: int) -> str:
        """Delete one message. Returns 'deleted' | 'absent' | 'refused' | 'error'.

        # ! The distinction is load-bearing for /clearall. 'absent' means the id
        # ! is a hole — already deleted, or never existed — and the walk should
        # ! carry on past it. 'refused' means Telegram will not delete it, which
        # ! in practice means it is older than 48 hours and everything further
        # ! back will be too.
        """
        try:
            ok = _call(self.token, "deleteMessage",
                       {"chat_id": chat_id, "message_id": message_id}).get("ok")
            return "deleted" if ok else "error"
        except TelegramError as e:
            if _is_transient(e):
                raise  # ! Stop clearing on an outage; let the poller back off.
            detail = str(e).lower()
            if "not found" in detail:
                return "absent"
            if "can't be deleted" in detail or "cant be deleted" in detail:
                return "refused"
            return "error"
        except urllib.error.URLError:
            raise
        except OSError:
            return "error"

    def _delete_batch(self, chat_id: str, ids: list[int]) -> bool:
        """Delete up to 100 messages in one call. Telegram skips what it cannot.

        # ! It returns a plain True and never says WHICH ids went, so this is
        # ! fast but uncountable. That trade is why the deep clear reports what
        # ! it did in words rather than with a number it did not measure.
        """
        if not ids:
            return True
        try:
            return bool(_call(self.token, "deleteMessages",
                              {"chat_id": chat_id, "message_ids": ids}).get("ok"))
        except TelegramError as e:
            if _is_transient(e):
                raise  # ! A busy API must not trigger per-message fallback.
            return False
        except urllib.error.URLError:
            raise
        except OSError:
            return False

    def clear_chat(self, chat_id: str, lang: str = DEFAULT_LANG,
                   from_message_id: int | str | None = None,
                   deep: bool = False) -> Reply:
        """Delete this chat's messages, ours and the worker's, within 48 hours.

        # ! Best effort by design, and the reply says so. Telegram refuses
        # ! anything older than 48 hours — someone clearing a chat about their
        # ! own poverty deserves to know exactly what is and is not gone.
        #
        # ! Two modes, because tracking alone is not enough and scanning alone
        # ! is wasteful:
        # !   /clear    — ids this process tracked. Exact, a few API calls, but
        # !               it forgets everything from before the last restart,
        # !               since the tracking table lives in memory.
        # !   /clearall — additionally walks message ids backwards from the
        # !               command itself. In a private chat ids are sequential,
        # !               so this reaches messages this process never saw. Costs
        # !               one API call per id and stops once deletes stop working.
        """
        cutoff = time.time() - _CLEAR_WINDOW_H * 3600
        deleted, tried = 0, set()

        for message_id, ts in self._sent.get(chat_id, []):
            if ts < cutoff or message_id in tried:
                continue
            tried.add(message_id)
            deleted += self._delete(chat_id, message_id) == "deleted"

        if deep and from_message_id:
            floor = max(1, int(from_message_id) - _CLEAR_SCAN_BACK)
            candidates = [m for m in range(int(from_message_id), floor - 1, -1)
                          if m not in tried]
            tried.update(candidates)
            batches, singles, empty_runs, wasted = 0, 0, 0, 0
            for start in range(0, len(candidates), _DELETE_BATCH):
                chunk = candidates[start:start + _DELETE_BATCH]
                batches += 1
                if self._delete_batch(chat_id, chunk):
                    empty_runs = 0
                    continue

                # ! A refused batch used to fall back to one call per id — a
                # ! hundred of them, for every failed chunk, up to a thousand
                # ! requests for one /clearall. All of it on the polling thread,
                # ! so the worker's next answer waited behind it, and each 429
                # ! slept on that thread too. Telegram then flood-limits the bot
                # ! for minutes afterwards, which is why the whole conversation
                # ! stayed slow long after the command finished.
                # !
                # ! Probe with a few ids instead of retrying the chunk. Almost
                # ! always the batch failed because those ids are older than 48
                # ! hours or never existed, and no amount of retrying changes
                # ! that.
                # ! The budget counts FAILED deletes, not deletes. An old Bot
                # ! API with no deleteMessages has nothing but this path, and
                # ! capping successful work there would quietly stop clearing
                # ! the window. What has to be bounded is futile work: ids that
                # ! are gone, or older than 48 hours, hammered one at a time.
                hit = False
                for message_id in chunk:
                    if wasted >= _WASTED_DELETE_BUDGET:
                        break
                    singles += 1
                    if self._delete(chat_id, message_id) == "deleted":
                        deleted += 1
                        hit = True
                        wasted = 0
                    else:
                        wasted += 1

                # ! Ids run backwards from the command, so once two chunks in a
                # ! row yield nothing we are past the window and everything
                # ! older is unreachable. Walking the remaining hundreds costs
                # ! requests and deletes nothing. The docstring always claimed
                # ! this stopped; the batched path never did.
                empty_runs = 0 if hit else empty_runs + 1
                if empty_runs >= _EMPTY_CHUNKS_BEFORE_STOP or wasted >= _WASTED_DELETE_BUDGET:
                    break
            print(f"[telegram] /clearall scanned={len(candidates)} "
                  f"batches={batches} singles={singles}")

        self._sent[chat_id] = []
        # ! Revoke before replying. A worker who reads "cleared" and then opens
        # ! an older link would have been told something untrue.
        for token in self._tokens.pop(chat_id, []):
            links.revoke(token)
        if deep:
            # ! No count: deleteMessages does not report which ids it removed,
            # ! and a number we did not measure is exactly the kind of claim
            # ! this project refuses to make anywhere else.
            return Reply(text=self._bilingual("commands.cleared_all", lang))
        if not deleted:
            return Reply(text=self._bilingual("commands.clear_nothing", lang))
        return Reply(text=self._bilingual("commands.cleared", lang, count=deleted))

    # * ------------------------------------------------------------ receiving

    def handle_update(self, update: dict) -> None:
        """One update in, replies out. Pure translation plus a dict lookup."""
        message = (update.get("message") or
                   (update.get("callback_query") or {}).get("message") or {})
        # ! A group chat would merge different workers into one sensitive profile.
        if (message.get("chat") or {}).get("type", "private") != "private":
            return
        if "callback_query" in update:
            cq = update["callback_query"]
            chat_id = str(cq["message"]["chat"]["id"])
            answer = cq.get("data", "")
            message_id = cq["message"].get("message_id")
            self._track(chat_id, message_id)
            stale = (not message_id or chat_id not in self.sessions
                     or message_id != self._active_keyboard.get(chat_id))
            ack = {"callback_query_id": cq["id"]}
            if stale:
                ack["text"] = s("errors.stale_button", self._lang.get(chat_id, DEFAULT_LANG))
            else:
                # ! Retire before dispatch: duplicate toggles stay in the SAME
                # ! state, and a later session can revisit that state too.
                self._active_keyboard.pop(chat_id, None)
            # ! Stops the client's spinner, and nothing more — so NOTHING here
            # ! may abort the update. This caught only URLError, but Telegram
            # ! rejects a stale query with HTTP 400 ("query is too old"), which
            # ! `_call` raises as TelegramError. That escaped, the whole update
            # ! was dropped, and a worker's tap did nothing at all.
            # !
            # ! Query expiry is separate from keyboard retirement. A failed
            # ! acknowledgement must neither drop a current answer nor revive
            # ! a retired one.
            try:
                _call(self.token, "answerCallbackQuery", ack)
            except (urllib.error.URLError, TelegramError, OSError, ValueError):
                pass
            if stale:
                return
        elif "message" in update:
            chat_id = str(update["message"]["chat"]["id"])
            answer = update["message"].get("text", "")
            message_id = update["message"].get("message_id")
            # * The worker's own messages are tracked too: a clear should remove
            # * both sides of the conversation, not just our half.
            self._track(chat_id, message_id)
        else:
            return

        self.turn(chat_id, answer, message_id)

    def poll_once(self) -> int:
        updates = _call(self.token, "getUpdates", {
            "offset": self._offset, "timeout": _POLL_S,
        }).get("result", [])
        for update in updates:
            if update["update_id"] < self._offset:
                continue
            self._offset = update["update_id"] + 1
            try:
                self.handle_update(update)
            except (urllib.error.URLError, TimeoutError):
                # ! Telegram is unreachable. That says nothing about this worker's
                # ! conversation, so do NOT discard it. Re-raise so run_forever
                # ! backs off. Answers stay in memory, but a failed question send
                # ! leaves no live keyboard; preserving state is not redelivery.
                # * Caught before the OSError family below on purpose: URLError is
                # * an OSError, but a plain OSError is usually ours (a missing pack
                # * file, a bad handle) and that DOES leave the turn half-applied.
                raise
            except TelegramError as e:
                # ! 429 and 5xx mean "busy, try shortly" — the worker's answers are
                # ! fine and must survive. A 400/403 means we sent something bad,
                # ! which is our bug and leaves the turn partly applied.
                if _is_transient(e):
                    raise
                print(f"[telegram] update failed: TelegramError status={e.status}")
                self._abandon(update, e)
                continue
            except Exception as e:  # noqa: BLE001
                # ! One broken conversation must never take the bot down while
                # ! other workers are mid-session. Log it and keep serving.
                print(f"[telegram] update failed: {type(e).__name__}")
                self._abandon(update, e)
        return len(updates)

    def _abandon(self, update: dict, cause: Exception) -> None:
        """Find the chat behind a failed update, then let the router drop it.

        # ! Recovery must never stop the poller: a chat we cannot even address
        # ! is a reason to log and carry on, not to take the bot down while
        # ! other workers are mid-session.
        """
        try:
            message = (update.get("message") or
                       (update.get("callback_query") or {}).get("message") or {})
            chat_id = (message.get("chat") or {}).get("id")
            if chat_id is None:
                return  # * No destination for a recovery notice.
            self.abandon(str(chat_id))
        except Exception as recovery_error:  # noqa: BLE001 — recovery must not stop polling
            print(f"[telegram] recovery notice failed: {type(recovery_error).__name__}")

    def run_forever(self) -> None:
        print(f"[telegram] polling, {len(self.schemes)} scheme(s) loaded")
        backoff = _BACKOFF_START_S
        while True:
            try:
                self.poll_once()
            except (urllib.error.URLError, TimeoutError, OSError, TelegramError,
                    json.JSONDecodeError) as e:
                # ! A wrong token and a dropped Wi-Fi look identical from here,
                # ! and both are worth retrying — the operator may be fixing the
                # ! token right now. What is never worth doing is retrying flat
                # ! out. Say how long we are waiting so a misconfiguration is
                # ! readable in the log instead of drowning in it.
                print(f"[telegram] poll failed ({type(e).__name__}, "
                      f"status={getattr(e, 'status', None)}) — retrying in {backoff:.0f}s")
                time.sleep(backoff)
                backoff = min(backoff * 2, _BACKOFF_MAX_S)
            else:
                backoff = _BACKOFF_START_S


def _self_check() -> None:
    """Runs offline: the network is stubbed, the translation is what we test."""
    import sys

    from sathi.core.schemes import Criterion as C

    # * Patch THIS module object. Running as __main__ makes a second copy of the
    # * module, so patching the imported name would patch the wrong one.
    mod = sys.modules[__name__]
    _original_call, _original_upload = mod._call, mod._upload

    kb = keyboard((Button("क", "a"), Button("ख", "b"), Button("ग", "c")))
    assert len(kb["inline_keyboard"]) == 2 and len(kb["inline_keyboard"][0]) == 2
    assert keyboard(()) is None

    schemes = {"A": Scheme(
        code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
        verified_on="2026-09-01", verified_by="a",
        benefit={"annual_value_inr": 1000, "value_basis": "annual_payout", "summary_hi": "प"},
        criteria=(C("age", "between", [18, 40], "u", pass_hi="ok", fail_hi="no"),),
        exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
    )}

    sent: list[tuple[str, dict]] = []
    real_call, real_upload = mod._call, mod._upload
    mod._call = lambda token, method, payload: (
        sent.append((method, payload)) or {"result": {"message_id": len(sent) + 1}}
    )
    mod._upload = lambda *a, **k: sent.append(("sendDocument", {"filename": a[2]})) or {}
    try:
        bot = TelegramBot(schemes, token="test-token")
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 1, "text": "/start"}})
        assert sent[-1][0] == "sendMessage" and "Choose your language" in sent[-1][1]["text"]
        assert sent[-1][1]["reply_markup"]["inline_keyboard"]

        bot.handle_update({
            "callback_query": {"id": "1", "data": "lang:en",
                               "message": {"chat": {"id": 42}, "message_id": 2}},
        })
        assert "Yojana Sathi" in sent[-1][1]["text"], sent[-1][1]["text"]
        assert "42" in bot.sessions
        assert any(m == "answerCallbackQuery" for m, _ in sent)

        # * Commands answer without disturbing the conversation.
        for cmd, needle in (("/help", "/schemes"), ("/about", "myScheme"),
                            ("/privacy", "Aadhaar"), ("/schemes", "Source:")):
            bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 3, "text": cmd}})
            assert needle in sent[-1][1]["text"], (cmd, sent[-1][1]["text"])
        assert bot.sessions["42"].state.value == "consent", "a command advanced the flow"

        # * /language toggles back to Hindi and re-asks the same question.
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 4, "text": "/language"}})
        assert bot.sessions["42"].lang == "hi"

        # ! /clear deletes what it tracked, and reports the count honestly.
        deletes = []
        prev = mod._call
        mod._call = lambda token, method, payload: (
            deletes.append(payload["message_id"]) or {"ok": True}
        ) if method == "deleteMessage" else prev(token, method, payload)
        # * Unique ids: the same message can be tracked twice (we send it, then
        # * see it again on a callback), and clear_chat deletes each id once.
        tracked = len({mid for mid, _ in bot._sent["42"]})
        assert tracked > 0
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 99, "text": "/clear"}})
        shallow = len(deletes)
        assert shallow >= tracked, (shallow, tracked)
        assert len(deletes) == len(set(deletes)), "an id was deleted twice"
        # ! /clear must NOT walk ids — that is the whole difference between the
        # ! two commands, and a scan of 400 ids on every clear is not free.
        assert shallow < 50, f"/clear scanned ids like /clearall would ({shallow})"

        # ! /clearall reaches ids this process never tracked — the messages from
        # ! before the last restart, which is what tracking alone always misses.
        # !
        # ! It must also stay BOUNDED. This fake refuses every batch, which is
        # ! the worst case, and the old code answered that by trying all 1000
        # ! ids one at a time — on the polling thread, so the worker's next
        # ! answer queued behind a thousand requests, and Telegram flood-limited
        # ! the bot for minutes afterwards. Reported from a real chat: /clearall
        # ! at 6:37, the reply to the next /start at 6:39.
        deletes.clear()
        bot._sent["42"] = []
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 900, "text": "/clearall"}})
        assert deletes, "/clearall deleted nothing at all"
        walked = len(deletes)
        assert walked > 50, f"/clearall did not walk back ({walked})"
        # * A ceiling, not exact accounting: the tracked-message pass deletes a
        # * few before the walk begins. What matters is the order of magnitude —
        # * tens, not the thousand this used to issue.
        assert max(deletes) == 900 and min(deletes) < 900

        # ! The flood case, and the reason this bug was reported: every id is
        # ! refused because it is older than the 48-hour window. The old code
        # ! answered that by trying all 1000 one at a time, on the polling
        # ! thread, and Telegram then throttled the bot for minutes - /clearall
        # ! at 6:37, the reply to the next /start at 6:39. It must give up.
        refused = []

        def _all_refused(token, method, payload):
            if method == "deleteMessages":
                raise TelegramError("deleteMessages failed: 400 Bad Request")
            if method == "deleteMessage":
                refused.append(payload["message_id"])
                raise TelegramError("message can't be deleted", status=400)
            return prev_call(token, method, payload)

        prev_call = mod._call
        mod._call = _all_refused
        try:
            bot._sent["42"] = []
            bot.clear_chat("42", "en", from_message_id=5000, deep=True)
        finally:
            mod._call = prev_call
        assert len(refused) < 100, (
            f"/clearall issued {len(refused)} futile deletes against a chat with "
            f"nothing deletable. The budget is {_WASTED_DELETE_BUDGET} consecutive "
            f"misses; hundreds means the flood-limit bug is back.")

        # ! The clear receipt may be the last message standing in the chat, so
        # ! it carries both languages.
        bot._sent["42"] = []  # * No tracked messages, including clear receipts.
        nothing = bot.clear_chat("42", "en")
        assert "nothing to delete" in nothing.text and "कुछ नहीं" in nothing.text, nothing.text
        deep_reply = bot.clear_chat("42", "en", from_message_id=3, deep=True)
        assert "48 hours" in deep_reply.text and "48 घंटे" in deep_reply.text, deep_reply.text

        # ! Language survives the end of a session. A fresh Conversation used to
        # ! default to Hindi, so an English worker's next command answered in
        # ! Hindi for no reason they could see.
        bot._lang["42"] = "en"
        bot.sessions.pop("42", None)
        assert bot._conversation("42").lang == "en"
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 7, "text": "/about"}})
        assert "myScheme" in sent[-1][1]["text"], sent[-1][1]["text"]

        # ! Speed: one call per message made /clearall unusable on a long chat.
        # ! A 1000-message window must cost ~10 calls, not ~1000.
        calls, seen = [], []
        def _batched(token, method, payload):
            if method != "deleteMessages":
                return prev(token, method, payload)
            calls.append(len(payload["message_ids"]))
            seen.extend(payload["message_ids"])
            assert len(payload["message_ids"]) <= 100, "batch over Telegram's limit of 100"
            return {"ok": True}
        mod._call = _batched
        bot._sent["42"] = []
        bot.clear_chat("42", "en", from_message_id=5000, deep=True)
        assert len(calls) <= 12, f"{len(calls)} calls for one clear — batching is not working"
        assert len(seen) > 900, f"only {len(seen)} ids covered"
        assert max(seen) == 5000

        # ! An API that rejects the batch method must still clear the chat, one
        # ! message at a time, rather than silently doing nothing.
        singles = []
        def _no_batch(token, method, payload):
            if method == "deleteMessages":
                raise TelegramError("deleteMessages failed: 400 Bad Request: method not found")
            if method == "deleteMessage":
                singles.append(payload["message_id"])
                return {"ok": True}
            return prev(token, method, payload)
        mod._call = _no_batch
        bot._sent["42"] = []
        bot.clear_chat("42", "en", from_message_id=150, deep=True)
        assert len(singles) > 100, f"fallback deleted only {len(singles)}"
        mod._call = prev

        # ! Regression: the age question — and every info command — sends a
        # ! message with no keyboard. Carrying "reply_markup": null there got a
        # ! bare 400 from Telegram and the session silently stopped dead.
        no_buttons = [p for m, p in sent if m == "sendMessage" and "reply_markup" not in p]
        assert no_buttons, "no button-less message was exercised"
        for method, payload in sent:
            assert None not in payload.values(), (method, payload)

        # * A message older than the 48h window is never even attempted.
        bot._sent["42"] = [(7, time.time() - 49 * 3600)]
        deletes.clear()
        reply = bot.clear_chat("42")
        assert not deletes and "कुछ नहीं" in reply.text

        # ! A failed acknowledgement of the CURRENT keyboard must not abort
        # ! its answer. Query expiry and keyboard retirement are different.
        stale = []
        prev_call = mod._call
        bot.handle_update({"message": {"chat": {"id": 77}, "text": "/start"}})
        language_keyboard = len(sent) + 1

        def _stale_ack(token, method, payload):
            if method == "answerCallbackQuery":
                raise TelegramError(
                    "answerCallbackQuery failed: 400 Bad Request: query is too old "
                    "and response timeout expired or query ID is invalid"
                )
            stale.append((method, payload))
            return prev_call(token, method, payload)

        mod._call = _stale_ack
        try:
            bot.handle_update({
                "callback_query": {"id": "stale", "data": "lang:hi",
                                   "message": {"chat": {"id": 77}, "message_id": language_keyboard}},
            })
        finally:
            mod._call = prev_call
        assert any(m == "sendMessage" for m, _ in stale), \
            "a stale callback ack aborted the update — the worker's tap did nothing"

        # ! The retry loop must SLEEP and back off. A revoked token returns a
        # ! 401 instantly, so a delay-free loop pegs a core and floods the log.
        class _Stop(Exception):
            pass

        slept: list[float] = []
        attempts = []

        def _always_fails():
            attempts.append(1)
            if len(attempts) > 4:
                raise _Stop
            raise TelegramError("401 Unauthorized: bot token is invalid")

        real_sleep, bot.poll_once = time.sleep, _always_fails
        time.sleep = slept.append
        try:
            bot.run_forever()
        except _Stop:
            pass
        finally:
            time.sleep = real_sleep
            del bot.poll_once
        assert slept == [1.0, 2.0, 4.0, 8.0], f"backoff did not double: {slept}"

        # ! A failed turn needs both a reset and a visible restart instruction.
        # ! Exercise the poll boundary, including a second chat in the same batch.
        for lang in ("hi", "en"):
            for failure in ("handler", "question", "document", "notice"):
                attempts, delivered, pending = [], [], []
                armed = False

                def _recovery_wire(token, method, payload):
                    if method == "getUpdates":
                        batch = pending[:]
                        pending.clear()
                        return {"ok": True, "result": batch}
                    if method == "answerCallbackQuery":
                        return {"ok": True, "result": True}
                    assert method == "sendMessage", method
                    attempts.append(payload)
                    if armed and payload["chat_id"] == "42":
                        if failure == "notice" or (failure == "question" and
                                payload["text"] == s("questions.state", lang)):
                            raise TelegramError("sendMessage failed: injected failure")
                    mid = 1000 + len(attempts)
                    delivered.append((mid, payload))
                    return {"ok": True, "result": {"message_id": mid}}

                def _fail_handler(answer):
                    raise RuntimeError("injected handler failure")

                def _fail_upload(*args, **kwargs):
                    raise OSError("injected upload failure")

                mod._call, mod._upload = _recovery_wire, _fail_upload
                recovering = TelegramBot(schemes, token="test-token")
                for chat in (42, 99):
                    for answer in ("/start", f"lang:{lang}"):
                        recovering.handle_update({"message": {
                            "chat": {"id": chat}, "text": answer}})
                affected = recovering.sessions["42"]
                neighbour = recovering.sessions["99"]
                assert affected.state.value == neighbour.state.value == "consent"
                answer = "consent_yes"
                if failure in ("handler", "notice"):
                    affected.handle = _fail_handler
                elif failure == "document":
                    for answer in ("consent_yes", "state:UK", "30", "occ:construction",
                                   "inc:upto_5000", "land:landless", "fam:4", "yes",
                                   "no", "no", "no", "next", "next"):
                        recovering.handle_update({"message": {
                            "chat": {"id": 42}, "text": answer}})
                    assert affected.state.value == "pack"
                    answer = "yes"
                keyboard_id = next(mid for mid, p in reversed(delivered)
                                   if p["chat_id"] == "42" and "reply_markup" in p)
                pending.extend([
                    {"update_id": 7, "callback_query": {
                        "id": "failure", "data": answer,
                        "message": {"chat": {"id": 42}, "message_id": keyboard_id}}},
                    {"update_id": 8, "message": {"chat": {"id": 99}, "text": "consent_yes"}},
                ])
                armed = True
                assert recovering.poll_once() == 2
                assert "42" not in recovering.sessions, f"{failure}: broken session survived"
                assert "42" not in recovering._active_keyboard
                notice = s("errors.screening_stopped", lang)
                assert "/start" in notice
                assert sum(p["chat_id"] == "42" and p["text"] == notice for p in attempts) == 1
                assert any(p["chat_id"] == "42" and p["text"] == notice
                           for _, p in delivered) == (failure != "notice")
                assert recovering.sessions["99"] is neighbour
                assert neighbour.state.value == "state", "another chat stopped progressing"
                assert delivered[-1][1]["text"] == s("questions.state", lang)
                assert recovering._offset == 9
                before = len(attempts)
                assert recovering.poll_once() == 0 and len(attempts) == before, "delivery was retried"

                armed = False
                recovering.handle_update({"message": {"chat": {"id": 42}, "text": "/start"}})
                restarted = recovering.sessions["42"]
                assert restarted is not affected and restarted.state.value == "language"
                assert restarted.lang == lang
                assert restarted.profile.age is None
                assert recovering._active_keyboard["42"] == delivered[-1][0]

        # ! Audio is optional even when its response is malformed. The real
        # ! question handler still runs; only the upload crosses a fake wire.
        from pathlib import Path

        for audio_error in (OSError, TelegramError, ValueError):
            attempts, delivered, pending = [], [], []
            armed = False
            mod._call = _recovery_wire
            recovering = TelegramBot(schemes, token="test-token")
            for answer in ("/start", "lang:en"):
                recovering.handle_update({"message": {"chat": {"id": 42}, "text": answer}})
            current = recovering.sessions["42"]
            real_handle = current.handle
            uploaded = []

            def _with_audio(answer):
                replies = real_handle(answer)
                replies[0].audio = Path(__file__)  # * Existing bytes; no generated test file.
                return replies

            def _broken_audio(*args, **kwargs):
                uploaded.append(True)
                raise audio_error("injected audio failure")

            current.handle = _with_audio
            mod._upload = _broken_audio
            pending.append({"update_id": 10, "message": {
                "chat": {"id": 42}, "text": "consent_yes"}})
            before = len(delivered)
            assert recovering.poll_once() == 1
            assert uploaded == [True], "the audio failure was never reached"
            assert recovering.sessions.get("42") is current, "optional audio reset the session"
            assert current.state.value == "state"
            assert len(delivered) == before + 1
            assert delivered[-1][1]["text"] == s("questions.state", "en")
            assert recovering._active_keyboard["42"] == delivered[-1][0]

        # ! A delivered pack carries the answer recap. It used to survive /clear
        # ! because send() threw away the id _upload() hands back.
        mod._upload = lambda *a, **k: {"result": {"message_id": 9911}}
        mod._call = lambda token, method, payload: {"result": []}
        bot._sent.pop("77", None)
        bot.send("77", Reply(text="pack", document=("pack.html", b"<html></html>")))
        assert 9911 in [mid for mid, _ in bot._sent.get("77", [])], \
            "an uploaded pack must be tracked, or /clear cannot delete it"

        # * A malformed upload response must not raise — _track ignores no id.
        mod._upload = lambda *a, **k: {}
        bot.send("77", Reply(text="pack", document=("pack.html", b"x")))

        # ! The pack link. Three things have gone wrong here before in spirit:
        # ! the link replacing the file instead of joining it, Telegram opening
        # ! the sheet itself to build a preview card, and /clear wiping the chat
        # ! while leaving the link readable.
        from sathi.pack import links as _links

        os.environ["PACK_BASE_URL"] = "https://links.test"
        try:
            _links.clear()
            link_calls, uploads = [], []
            mod._upload = lambda *a, **k: uploads.append(a[2]) or {"result": {"message_id": 5001}}
            mod._call = lambda token, method, payload: (
                link_calls.append((method, payload)) or {"result": {"message_id": 5002}})
            bot._sent.pop("78", None)
            bot._tokens.pop("78", None)
            bot.send("78", Reply(text="pack", document=("pack.html", b"<html>sheet</html>")))

            assert uploads == ["pack.html"], "the file must still be sent, not replaced"
            link_msg = [p for m, p in link_calls if m == "sendMessage"][-1]
            assert link_msg["link_preview_options"] == {"is_disabled": True},                 "Telegram would fetch the sheet to build a preview card"
            token = bot._tokens["78"][-1]
            assert token in link_msg["text"], "the link message must carry the token"
            assert _links.fetch(token) == b"<html>sheet</html>"

            # /clear must take the link back, not just the messages.
            mod._call = lambda token, method, payload: {"result": True}
            bot.clear_chat("78", "en", None, deep=False)
            assert _links.fetch(token) is None, "/clear left the pack link readable"

            # ! A failed link must not lose the pack — the file already went.
            def _link_explodes(token, method, payload):
                # * Only the link message fails; the ordinary text still goes,
                # * which is what makes this test about the link and not send().
                if "link_preview_options" in payload:
                    raise TelegramError("injected sendMessage failure")
                return {"result": {"message_id": 5003}}

            mod._call = _link_explodes
            bot.send("79", Reply(text="pack", document=("pack.html", b"y")))
            assert 5001 in [mid for mid, _ in bot._sent.get("79", [])],                 "a failed link must not stop the file from being tracked"
        finally:
            del os.environ["PACK_BASE_URL"]
            _links.clear()
            mod._call = _original_call
            mod._upload = _original_upload

        # ! Use the keyboard IDs actually returned by the wire stub. Fabricated
        # ! callbacks cannot prove which question the worker is answering.
        delivered, acknowledgements = [], []
        fail_ack = False

        def _keyboard_wire(token, method, payload):
            if method == "answerCallbackQuery":
                acknowledgements.append(payload)
                if fail_ack:
                    raise TelegramError("answerCallbackQuery failed: query is too old")
                return {"ok": True, "result": True}
            assert method == "sendMessage", method
            mid = len(delivered) + 100
            delivered.append((mid, payload))
            return {"ok": True, "result": {"message_id": mid}}

        mod._call = _keyboard_wire
        guarded = TelegramBot(schemes, token="test-token")

        def _message(text):
            guarded.handle_update({"message": {"chat": {"id": 88}, "text": text}})

        def _tap(value, mid=None):
            if mid is None:
                mid = delivered[-1][0]
            guarded.handle_update({"callback_query": {
                "id": str(len(acknowledgements)), "data": value,
                "message": {"chat": {"id": 88}, "message_id": mid},
            }})

        def _reach_bank():
            _message("/start")
            _tap("lang:en")
            _tap("consent_yes")
            _tap("state:UK")
            _message("30")
            for answer in ("occ:construction", "inc:upto_5000", "land:landless", "fam:4"):
                _tap(answer)
            assert guarded.sessions["88"].state.value == "has_bank_account"
            return delivered[-1][0]

        # ! Double bank Yes must not answer the unseen tax question.
        bank_keyboard = _reach_bank()
        _tap("yes", bank_keyboard)
        tax_keyboard = delivered[-1][0]
        count = len(delivered)
        _tap("yes", bank_keyboard)
        current = guarded.sessions["88"]
        assert current.profile.has_bank_account is True
        assert current.profile.is_income_tax_payer is None, "duplicate bank tap answered tax"
        assert current.state.value == "is_income_tax_payer" and len(delivered) == count
        assert acknowledgements[-1].get("text") == s("errors.stale_button", "en")

        # ! Info messages must not replace the live question keyboard.
        for command in ("/help", "/about", "/privacy", "/schemes"):
            _message(command)
        _tap("no", tax_keyboard)
        assert current.profile.is_income_tax_payer is False
        assert current.state.value == "is_epfo_or_esic_member"

        # ! A repeated checkbox tap must not toggle a selection back off.
        _tap("no")
        _tap("no")
        assert current.state.value == "known_schemes"
        known_keyboard = delivered[-1][0]
        _tap("known:A", known_keyboard)
        _tap("known:A", known_keyboard)
        assert current._known == {"A"}, "duplicate tap unselected a known scheme"
        _tap("next")
        assert current.state.value == "documents"
        docs_keyboard = delivered[-1][0]
        _tap("doc:0", docs_keyboard)
        _tap("doc:0", docs_keyboard)
        assert current._have_docs == {"आधार"}, "duplicate tap unselected a document"

        # ! The same state in a new session must not revive an old keyboard.
        new_bank_keyboard = _reach_bank()
        current = guarded.sessions["88"]
        _tap("yes", bank_keyboard)
        assert current.profile.has_bank_account is None
        assert current.state.value == "has_bank_account"

        # ! Even a failed stale toast must leave the retired tap rejected.
        fail_ack = True
        _tap("yes", bank_keyboard)
        assert current.profile.has_bank_account is None
        assert current.state.value == "has_bank_account"
        fail_ack = False
        _tap("yes", new_bank_keyboard)
        assert current.profile.has_bank_account is True

        # ! Typed advancement, language replacement and cancellation retire
        # ! old keyboards too; the toast uses the current language.
        tax_keyboard = delivered[-1][0]
        _message("no")
        _tap("yes", tax_keyboard)
        assert current.profile.is_epfo_or_esic_member is None
        epfo_keyboard = delivered[-1][0]
        _message("/language")
        _tap("yes", epfo_keyboard)
        assert current.profile.is_epfo_or_esic_member is None
        assert acknowledgements[-1].get("text") == s("errors.stale_button", "hi")
        last_keyboard = delivered[-1][0]
        _message("/cancel")
        _tap("yes", last_keyboard)
        assert "88" not in guarded.sessions, "a stale tap recreated a cancelled session"

        # ! Normal completion retires the pack offer, including its No button.
        _reach_bank()
        for answer in ("yes", "no", "no", "no", "next", "next"):
            _tap(answer)
        assert guarded.sessions["88"].state.value == "pack"
        pack_keyboard = delivered[-1][0]
        _tap("no", pack_keyboard)
        # ! The pack answer no longer ends the conversation - two optional
        # ! questions follow it - so the session is still live here. The point
        # ! of the test is the retired keyboard, and a second tap on it must
        # ! still do nothing.
        assert guarded.sessions["88"].state.value == "rating"
        before = guarded.sessions["88"].state
        _tap("no", pack_keyboard)
        assert guarded.sessions["88"].state is before, "a stale tap moved the session on"
        skip_keyboard = delivered[-1][0]
        _tap("skip", skip_keyboard)
        _tap("skip", delivered[-1][0])
        assert "88" not in guarded.sessions, "a completed session was not dropped"
    finally:
        mod._call, mod._upload = real_call, real_upload
    # ! A busy Telegram must not cost a worker their answers. 429 and the 5xx
    # ! family mean "try again shortly", not "this conversation is broken" —
    # ! before this split, a 30-second rate limit discarded a half-finished
    # ! screening AND the notice explaining it was rate-limited too, so the
    # ! worker lost everything and was told nothing.
    for code, transient in (("429 Too Many Requests: retry after 30", True),
                            ("502 Bad Gateway", True),
                            ("500 Internal Server Error", True),
                            ("400 Bad Request: message is too long", False),
                            ("403 Forbidden: bot was blocked by the user", False)):
        assert _is_transient(TelegramError(f"sendMessage failed: {code}",
                                         int(code.split()[0]))) is transient, code

    class _Stub:
        """A session that answers normally, so the failure lands on the SEND."""
        lang = DEFAULT_LANG
        state = type("S", (), {"value": "consent"})()
        def handle(self, answer):
            return [Reply(text="next question", buttons=(Button("a", "a"),))]

    keep = TelegramBot(schemes, token="test-token")
    keep.sessions["31"] = _Stub()
    keep._active_keyboard["31"] = 7
    update = {"update_id": 1, "callback_query": {"id": "z", "data": "land:landless",
              "message": {"chat": {"id": 31}, "message_id": 7}}}
    mod._call = lambda token, method, payload: ({"result": [update]} if method == "getUpdates"
        else (_ for _ in ()).throw(TelegramError("sendMessage failed: 429 Too Many Requests", 429)))
    try:
        keep.poll_once()
        raise AssertionError("a rate limit must reach run_forever, which backs off")
    except TelegramError:
        pass
    assert "31" in keep.sessions, "a rate limit must not discard a worker's answers"
    # ! The keyboard stays retired, and that is deliberate. The handler already
    # ! ran before the send failed, so the conversation may have advanced even
    # ! though the worker never saw the next question. Putting the old keyboard
    # ! back would let its buttons answer the NEW state — the exact bug the
    # ! message_id guard exists to stop. Dead buttons plus a "no longer active"
    # ! toast is the honest outcome; the worker restarts with /start.
    # ! Known limitation: the update's offset has already advanced, so the lost
    # ! reply is not redelivered. Retrying delivery separately could leave the
    # ! offset and events alone, but delivery retries/queues are outside this
    # ! change. Preserving answers in memory does not restore the missing prompt.
    assert keep._active_keyboard.get("31") is None

    # ! Exercise the real JSON and multipart boundaries, not an invented
    # ! TelegramError from a mock: HTTPError itself is also a URLError.
    import io
    import http.client

    real_urlopen, real_sleep = urllib.request.urlopen, time.sleep
    mod._call, mod._upload = real_call, real_upload
    try:
        for wire in (
            lambda: real_call("test-token", "sendMessage", {"chat_id": "31", "text": "x"}),
            lambda: real_upload("test-token", "31", "pack.html", b"x", ""),
        ):
            for status in (400, 403, 429, 500, 501, 502, 503, 504):
                def _http_failure(req, timeout):
                    # ! A number in the description must not become the status.
                    body = json.dumps({"description": "request 502 failed",
                                       "parameters": {"retry_after": 30}}).encode()
                    raise urllib.error.HTTPError(req.full_url, status, "failure", {},
                                                 io.BytesIO(body))

                urllib.request.urlopen = _http_failure
                pauses = []
                time.sleep = pauses.append
                try:
                    wire()
                    raise AssertionError("HTTP failure was swallowed")
                except TelegramError as error:
                    assert _is_transient(error) == (status == 429 or status >= 500), status
                assert pauses == ([30] if status == 429 else []), (status, pauses)

            for failure in (ConnectionResetError("connection reset"),
                            http.client.IncompleteRead(b"partial")):
                class _BrokenRead:
                    def __enter__(self):
                        return self
                    def __exit__(self, *args):
                        pass
                    def read(self):
                        raise failure

                urllib.request.urlopen = lambda *args, **kwargs: _BrokenRead()
                try:
                    wire()
                    raise AssertionError("broken response was swallowed")
                except urllib.error.URLError:
                    pass  # * The poller preserves sessions for network failures.

        # ! Trace those wire failures through a real, advancing conversation.
        for status in (400, 403, None):
            recovering = TelegramBot(schemes, token="test-token")
            current = recovering._conversation("31")
            current.handle("lang:en")
            assert current.state.value == "consent"
            real_handle = current.handle

            def _with_document(answer):
                replies = real_handle(answer)
                replies[0].document = ("pack.html", b"x")
                return replies

            current.handle = _with_document
            recovering._active_keyboard["31"] = 7
            delivered, failures = [], []

            def _recovering_wire(req, timeout):
                method = req.full_url.rsplit("/", 1)[1]
                if method == "getUpdates":
                    result = [{"update_id": 1, "message": {
                        "chat": {"id": 31}, "text": "consent_yes"}}]
                else:
                    target = "sendMessage" if status is None else "sendDocument"
                    if method == target and not failures:
                        failures.append(method)
                        if status is None:
                            raise ConnectionResetError("connection reset")
                        raise urllib.error.HTTPError(req.full_url, status, "failure", {},
                                                     io.BytesIO(b'{}'))
                    if method == "sendMessage":
                        delivered.append(json.loads(req.data)["text"])
                    result = {"message_id": 8}
                return io.BytesIO(json.dumps({"ok": True, "result": result}).encode())

            urllib.request.urlopen = _recovering_wire
            try:
                recovering.poll_once()
                assert status is not None, "connection reset did not reach backoff"
            except urllib.error.URLError:
                assert status is None, "permanent upload failure bypassed recovery"
            assert failures, "wire failure was never exercised"
            assert current.state.value == "state", "test never advanced the intake"
            assert recovering._offset == 2
            assert "31" not in recovering._active_keyboard
            if status is None:
                assert recovering.sessions.get("31") is current
                assert not delivered, "network outage caused a restart notice"
            else:
                assert "31" not in recovering.sessions
                assert delivered[-1] == s("errors.screening_stopped", "en")
    finally:
        urllib.request.urlopen, time.sleep = real_urlopen, real_sleep
        mod._call, mod._upload = real_call, real_upload

    # ! A failed batch must not turn a rate limit/outage into 1000 more requests.
    try:
        for deep in (False, True):
            for failure in (TelegramError("busy", 429), TelegramError("unavailable", 503),
                            urllib.error.URLError("offline")):
                clearing = TelegramBot(schemes, token="test-token")
                if not deep:
                    clearing._track("31", 1200)
                attempts = []

                def _failed_delete(token, method, payload):
                    attempts.append(method)
                    raise failure

                mod._call = _failed_delete
                try:
                    clearing.clear_chat("31", from_message_id=1200, deep=deep)
                    raise AssertionError("clear swallowed a temporary API failure")
                except (TelegramError, urllib.error.URLError):
                    pass
                assert attempts == ["deleteMessages" if deep else "deleteMessage"], attempts
                if not deep:
                    assert clearing._sent["31"], "failed deletion forgot tracked messages"
    finally:
        mod._call = real_call

    print("telegram.py OK")


if __name__ == "__main__":
    _self_check()
