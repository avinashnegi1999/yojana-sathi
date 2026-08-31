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

import json
import mimetypes
import os
import time
import urllib.error
import urllib.request
import uuid

from sathi.channels.base import Button, Reply
from sathi.conversation.flow import Conversation
from sathi.core.content import DEFAULT_LANG, LANGS, s
from sathi.core.schemes import Scheme
from sathi.metrics.events import EventLog

class TelegramError(Exception):
    pass


API = "https://api.telegram.org/bot{token}/{method}"
_TIMEOUT_S = 65  # must exceed the long-poll timeout below
_POLL_S = 50

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
# * Past the 48-hour edge Telegram refuses every delete, so a run of REFUSALS
# * means we have walked off the end and can stop instead of burning 400 calls.
# ! A gap of already-deleted ids is not a refusal and must not stop the walk.
# ! Telegram says "message to delete not found" for those, and "message can't be
# ! deleted" once a message is too old — different answers to different
# ! questions. Conflating them made /clearall stop dead after a /clear, which is
# ! exactly the case a second clear is for.
_CLEAR_REFUSAL_STREAK = 40

# * Commands are handled here, not in the flow, because they are a channel
# * affordance. The flow exposes plain methods; this maps slash words onto them.
COMMANDS = {
    "/start": "start", "/restart": "start",
    "/language": "language", "/lang": "language",
    "/help": "help", "/about": "about", "/privacy": "privacy",
    "/schemes": "schemes", "/cancel": "cancel", "/stop": "cancel",
    "/clear": "clear", "/clearall": "clearall", "/clear_all": "clearall",
}


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
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # ! Telegram puts the actual reason in the body. A bare "400 Bad Request"
        # ! in the log costs an hour; the description costs nothing to keep.
        try:
            detail = json.loads(e.read().decode("utf-8")).get("description", "")
        except Exception:  # noqa: BLE001 — the error path must not raise
            detail = ""
        raise TelegramError(f"{method} failed: {e.code} {detail or e.reason}") from e


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
    with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
        return json.loads(resp.read().decode("utf-8"))


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


class TelegramBot:
    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None,
                 token: str | None = None) -> None:
        self.token = token or os.environ.get("TELEGRAM_TOKEN", "")
        if not self.token:
            raise TelegramError("TELEGRAM_TOKEN is not set — see .env.example")
        self.schemes = schemes
        self.log = log
        self.sessions: dict[str, Conversation] = {}
        # ! chat_id -> [(message_id, sent_at)] so /clear has something to delete.
        # ! In memory only: it dies with the process, like the profiles do.
        self._sent: dict[str, list[tuple[int, float]]] = {}
        # ! The language outlives the session. A Conversation is rebuilt whenever
        # ! one ends — after /cancel, after a completed screening — and a fresh
        # ! one defaults to Hindi, so an English worker's /help or /clear came
        # ! back in Hindi. The choice is a preference, not session state.
        self._lang: dict[str, str] = {}
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
        self._track(chat_id, (sent.get("result") or {}).get("message_id"))
        if reply.audio is not None:
            try:
                _upload(self.token, chat_id, reply.audio.name,
                        reply.audio.read_bytes(), "")
            except (OSError, urllib.error.URLError):
                pass  # * audio is an extra; the text already carried the message
        if reply.document is not None:
            filename, blob = reply.document
            _upload(self.token, chat_id, filename, blob, "")

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
            detail = str(e).lower()
            if "not found" in detail:
                return "absent"
            if "can't be deleted" in detail or "cant be deleted" in detail:
                return "refused"
            return "error"
        except (urllib.error.URLError, OSError):
            return "error"

    @staticmethod
    def _bilingual(key: str, lang: str, **fmt) -> str:
        """The same message in both languages, the worker's own first.

        # ! Used for the clear receipts. After a clear this may be the only
        # ! message left standing in the chat, with no earlier screen to give it
        # ! context — so it has to be readable whichever language the reader
        # ! has. Same reasoning as the language picker.
        """
        first = s(key, lang, **fmt)
        second = next(s(key, other, **fmt) for other in LANGS if other != lang)
        return f"{first}\n\n{second}" if first != second else first

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
        except (TelegramError, urllib.error.URLError, OSError):
            return False

    def clear_chat(self, chat_id: str, lang: str = "hi",
                   from_message_id: int | None = None, deep: bool = False) -> Reply:
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
            batches = 0
            for start in range(0, len(candidates), _DELETE_BATCH):
                chunk = candidates[start:start + _DELETE_BATCH]
                batches += 1
                if not self._delete_batch(chat_id, chunk):
                    # * Older Bot API, or a chunk it refused wholesale. Fall back
                    # * to one-at-a-time for this chunk only, so a single bad
                    # * batch does not lose the rest of the window.
                    for message_id in chunk:
                        deleted += self._delete(chat_id, message_id) == "deleted"
            print(f"[telegram] /clearall chat={chat_id} scanned={len(candidates)} "
                  f"batches={batches}")

        self._sent[chat_id] = []
        if deep:
            # ! No count: deleteMessages does not report which ids it removed,
            # ! and a number we did not measure is exactly the kind of claim
            # ! this project refuses to make anywhere else.
            return Reply(text=self._bilingual("commands.cleared_all", lang))
        if not deleted:
            return Reply(text=self._bilingual("commands.clear_nothing", lang))
        return Reply(text=self._bilingual("commands.cleared", lang, count=deleted))

    # * ------------------------------------------------------------ receiving

    def _conversation(self, chat_id: str, fresh: bool = False) -> Conversation:
        if fresh or chat_id not in self.sessions:
            convo = Conversation(self.schemes, self.log, channel="telegram")
            convo.lang = self._lang.get(chat_id, DEFAULT_LANG)
            self.sessions[chat_id] = convo
        return self.sessions[chat_id]

    def handle_update(self, update: dict) -> None:
        """One update in, replies out. Pure translation plus a dict lookup."""
        if "callback_query" in update:
            cq = update["callback_query"]
            chat_id = str(cq["message"]["chat"]["id"])
            answer = cq.get("data", "")
            message_id = cq["message"].get("message_id")
            self._track(chat_id, message_id)
            # * Stops the client's spinner. Failure here is cosmetic.
            try:
                _call(self.token, "answerCallbackQuery", {"callback_query_id": cq["id"]})
            except urllib.error.URLError:
                pass
        elif "message" in update:
            chat_id = str(update["message"]["chat"]["id"])
            answer = update["message"].get("text", "")
            message_id = update["message"].get("message_id")
            # * The worker's own messages are tracked too: a clear should remove
            # * both sides of the conversation, not just our half.
            self._track(chat_id, message_id)
        else:
            return

        replies = self._dispatch(chat_id, answer, message_id)
        # * Remember the language for whatever comes after this session ends.
        convo = self.sessions.get(chat_id)
        if convo is not None:
            self._lang[chat_id] = convo.lang

        for reply in replies:
            self.send(chat_id, reply)
            if reply.end:
                # ! Session over: drop the profile from memory immediately. It is
                # ! never written anywhere, and now it is not held anywhere either.
                self.sessions.pop(chat_id, None)

    def _dispatch(self, chat_id: str, answer: str,
                  message_id: int | None = None) -> list[Reply]:
        """Slash command, or an answer to the question we asked."""
        word = answer.strip().split()[0].lower() if answer.strip() else ""
        command = COMMANDS.get(word)
        if command is None:
            return self._conversation(chat_id).handle(answer)

        if command == "start":
            return self._conversation(chat_id, fresh=True).start()

        convo = self._conversation(chat_id)
        if command == "language":
            # * Toggle. Two languages means a switch needs no submenu.
            return convo.set_language("en" if convo.lang == "hi" else "hi")
        if command == "cancel":
            replies = convo.cancel()
            self.sessions.pop(chat_id, None)
            return replies
        if command in ("clear", "clearall"):
            # * /clear is exact and cheap: only what this process tracked.
            # * /clearall also walks ids backwards to reach messages from before
            # * the last restart — more thorough, many more API calls.
            return [self.clear_chat(chat_id, convo.lang, message_id,
                                    deep=command == "clearall")]
        if command == "schemes":
            return convo.scheme_list()
        return convo.info(command)  # help | about | privacy

    def poll_once(self) -> int:
        updates = _call(self.token, "getUpdates", {
            "offset": self._offset, "timeout": _POLL_S,
        }).get("result", [])
        for update in updates:
            self._offset = update["update_id"] + 1
            try:
                self.handle_update(update)
            except Exception as e:  # noqa: BLE001
                # ! One broken conversation must never take the bot down while
                # ! other workers are mid-session. Log it and keep serving.
                print(f"[telegram] update {update.get('update_id')} failed: {e}")
        return len(updates)

    def run_forever(self) -> None:
        print(f"[telegram] polling, {len(self.schemes)} scheme(s) loaded")
        while True:
            try:
                self.poll_once()
            except (urllib.error.URLError, TimeoutError, OSError, TelegramError) as e:
                print(f"[telegram] network hiccup, retrying: {e}")
            except json.JSONDecodeError as e:
                print(f"[telegram] bad response, retrying: {e}")


def _self_check() -> None:
    """Runs offline: the network is stubbed, the translation is what we test."""
    import sys

    from sathi.core.schemes import Criterion as C

    # * Patch THIS module object. Running as __main__ makes a second copy of the
    # * module, so patching the imported name would patch the wrong one.
    mod = sys.modules[__name__]

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
    mod._call = lambda token, method, payload: (sent.append((method, payload)), {"result": []})[1]
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
        deletes.clear()
        bot._sent["42"] = []
        bot.handle_update({"message": {"chat": {"id": 42}, "message_id": 900, "text": "/clearall"}})
        assert len(deletes) > 50, f"/clearall did not walk back ({len(deletes)})"
        assert max(deletes) == 900 and min(deletes) < 900

        # ! The clear receipt may be the last message standing in the chat, so
        # ! it carries both languages.
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

        # ! A crash inside one conversation must not escape the poll loop.
        bot.sessions["42"].handle = lambda a: (_ for _ in ()).throw(RuntimeError("boom"))
        mod._call = lambda token, method, payload: {"result": [
            {"update_id": 7, "message": {"chat": {"id": 42}, "text": "x"}}
        ]} if method == "getUpdates" else {"result": []}
        bot.poll_once()  # must not raise
    finally:
        mod._call, mod._upload = real_call, real_upload
    print("telegram.py OK")


if __name__ == "__main__":
    _self_check()
