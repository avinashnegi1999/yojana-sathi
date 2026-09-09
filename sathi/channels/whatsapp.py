"""WhatsApp Cloud API adapter. Thin: translates Reply/ChannelMessage.

# * Push, not poll. Telegram hands us updates when we ask; Meta posts them at a
# * public HTTPS endpoint, so this module carries an HTTP server the Telegram
# * adapter never needed. TLS is NOT here — it belongs to whatever fronts this
# * on the VM. See deploy/RUNBOOK.md.
#
# * urllib and http.server only, like everything else. A webhook receiver that
# * verifies one HMAC and parses one JSON shape does not justify a web
# * framework, and a container that installs nothing cannot fail to install.
#
# ! The worker's WhatsApp id IS their phone number. That makes it the most
# ! identifying channel key this project has ever handled, and it must never be
# ! printed, logged or persisted: the event log's session id is an unrelated
# ! uuid4 (sathi/metrics/events.py) and every diagnostic line here uses
# ! _tag() instead. Nothing in this file writes a phone number anywhere.
#
# ! Meta retries a webhook it thinks failed, so the same message can arrive
# ! twice. We enqueue before answering 200, process afterwards, and drop ids we have
# ! already handled — a replayed answer would otherwise be recorded twice.
"""

import hashlib
import hmac
import html.parser
import http.client
import json
import os
import queue
import signal
import threading
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from sathi.channels.base import Button, Reply
from sathi.channels.router import Router
from sathi.core.content import DEFAULT_LANG, s
from sathi.core.schemes import Scheme
from sathi.metrics.events import EventLog


class WhatsAppError(Exception):
    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


GRAPH = "https://graph.facebook.com/{version}/{path}"
_TIMEOUT_S = 30

# ! Cloud API limits, and they are much tighter than Telegram's. Exceeding any
# ! of them is a 400 with a message the worker never sees, so the renderer
# ! enforces them here rather than discovering them in production.
_MAX_BUTTONS = 3        # * reply buttons per message
_BUTTON_TITLE = 20      # * characters in a reply button label
_MAX_ROWS = 10          # * rows in a list message, across all sections
_ROW_TITLE = 24
_ROW_DESC = 72
_LIST_BUTTON = 20
_TEXT_MAX = 4096
_BODY_MAX = 1024        # ! an interactive message's body is a QUARTER of a text

# ! ponytail: only the latest 500 ids survive in memory; restart/eviction loses
# ! deduplication. A durable hashed receipt store is needed for stronger delivery.
_SEEN_MAX = 500
_WEBHOOK_MAX = 256 * 1024
_QUEUE_MAX = 128
_LOG_SALT = os.urandom(32)

# ! WhatsApp accepts a narrow list of audio types and .wav is not among them,
# ! but TTS_CMD's example produces exactly that. Rather than shell out to a
# ! converter — a dependency, and a new way for an ENHANCEMENT to break the
# ! message it decorates — an unsupported voice note is simply not sent.
# ? Getting voice on WhatsApp means pointing TTS_CMD at something that writes
# ? .ogg (opus) or .mp3. Noted in .env.example; not worth a hard requirement.
_AUDIO_TYPES = {
    ".ogg": "audio/ogg", ".mp3": "audio/mpeg", ".m4a": "audio/mp4",
    ".aac": "audio/aac", ".amr": "audio/amr",
}

# * Documents are a whitelist too, and text/html is not on it — which is what
# * the application pack is. The pack is flattened to plain text before it is
# * sent, so the worker still receives the whole thing.
# ? A real PDF would keep the layout. The stdlib has no PDF writer, so that is
# ? the same fpdf2 decision pack.py already parked until users ask for it.
_PACK_TEXT_MIME = "text/plain"


def _api_version() -> str:
    # * Env-overridable: Graph versions are retired on a schedule and a pinned
    # * constant in a deployed file is a future outage.
    return os.environ.get("WHATSAPP_API_VERSION", "v21.0")


# * Cloud API failures split the same way Telegram's do, and the difference
# * decides whether a worker keeps their answers: 429 and 5xx mean "busy, try
# * again shortly", a 400/403 means we sent something it refused.


def _is_transient(err: WhatsAppError) -> bool:
    return err.status == 429 or (err.status is not None and 500 <= err.status < 600)


def _request(req: urllib.request.Request, what: str) -> dict:
    """Classify failures at the wire boundary, for JSON and uploads alike."""
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_S) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # ! Provider descriptions can echo phone numbers, IDs or credentials.
        # ! Status is sufficient to classify retryable failures without PII.
        raise WhatsAppError(f"WhatsApp request failed: HTTP {e.code}", e.code) from e
    except (OSError, http.client.HTTPException, ValueError) as e:
        # ! A reset or truncated response is a network failure. Catch it here so
        # ! a genuine file or parsing error in a handler still takes the reset
        # ! path and abandons the half-applied turn.
        raise urllib.error.URLError(f"{what}: {type(e).__name__}") from e


def _post(token: str, path: str, payload: dict) -> dict:
    req = urllib.request.Request(
        GRAPH.format(version=_api_version(), path=path),
        data=json.dumps(payload).encode("utf-8"),
        headers={"content-type": "application/json",
                 "authorization": f"Bearer {token}"},
    )
    return _request(req, path)


def _upload(token: str, phone_number_id: str, filename: str,
            blob: bytes, mime: str) -> str:
    """Put one file in Meta's media store and return its id.

    # * multipart/form-data by hand — two uploads do not need a library, and
    # * this is the same shape the Telegram adapter already builds.
    """
    boundary = f"----sathi{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for key, value in (("messaging_product", "whatsapp"), ("type", mime)):
        parts += [
            f"--{boundary}\r\n".encode(),
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(),
            value.encode("utf-8"),
            b"\r\n",
        ]
    parts += [
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'.encode(),
        f"Content-Type: {mime}\r\n\r\n".encode(),
        blob,
        f"\r\n--{boundary}--\r\n".encode(),
    ]
    req = urllib.request.Request(
        GRAPH.format(version=_api_version(), path=f"{phone_number_id}/media"),
        data=b"".join(parts),
        headers={"content-type": f"multipart/form-data; boundary={boundary}",
                 "authorization": f"Bearer {token}"},
    )
    media_id = _request(req, "media upload").get("id")
    if not media_id:
        raise WhatsAppError("media upload returned no id")
    return str(media_id)


# * --------------------------------------------------------------- rendering


def _trim(text: str, limit: int) -> str:
    """Cut to a length WhatsApp accepts, on a word boundary where one is near."""
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    cut = text[:limit - 1]
    space = cut.rfind(" ")
    # ! Only honour a space in the last third. Breaking "Aadhaar card" after
    # ! "Aadhaar" is fine; breaking a 30-character label after its first word
    # ! throws away most of the option.
    if space > limit * 2 // 3:
        cut = cut[:space]
    return cut.rstrip() + "…"


def _row(button: Button, index: int) -> dict:
    """One list row. A label too long for the title spills into the description.

    # ! Nothing is discarded: a row's title and description together hold 96
    # ! characters, and the longest label in the flow today is 89 (the English
    # ! document line about an Aadhaar-linked mobile number).
    """
    label = " ".join(button.label.split())
    row = {"id": button.value[:200] or f"row:{index}"}
    if len(label) <= _ROW_TITLE:
        row["title"] = label
        return row
    head = label[:_ROW_TITLE]
    space = head.rfind(" ")
    if space > _ROW_TITLE // 2:
        head, tail = label[:space], label[space + 1:]
    else:
        tail = label[_ROW_TITLE:]
    row["title"] = head.rstrip()
    row["description"] = _trim(tail, _ROW_DESC)
    return row


def interactive(text: str, buttons: tuple[Button, ...], lang: str) -> dict:
    """The `interactive` object for a question, or a plain text body without one.

    # ! Three options fit on buttons. Anything more has to become a list behind
    # ! a "Choose" button — an extra tap, and the reason the conversation layer
    # ! is where WhatsApp trouble was expected.
    """
    if not buttons:
        return {"type": "text", "text": {"preview_url": False, "body": text[:_TEXT_MAX]}}

    if len(buttons) <= _MAX_BUTTONS:
        return {
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": text[:_BODY_MAX]},
                "action": {"buttons": [
                    {"type": "reply", "reply": {"id": b.value[:256],
                                                "title": _trim(b.label, _BUTTON_TITLE)}}
                    for b in buttons
                ]},
            },
        }

    if len(buttons) > _MAX_ROWS:
        # ! Fail loudly rather than silently dropping an option a worker needs.
        # ! No screen in the flow reaches eleven today and a self-check keeps it
        # ! that way; if one ever does, it needs paging designed, not truncation.
        raise WhatsAppError(
            f"{len(buttons)} options exceed WhatsApp's list limit of {_MAX_ROWS}")

    label = _trim(s("buttons.choose", lang), _LIST_BUTTON)
    return {
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": text[:_BODY_MAX]},
            "action": {
                "button": label,
                "sections": [{"title": label[:_ROW_TITLE],
                              "rows": [_row(b, i) for i, b in enumerate(buttons)]}],
            },
        },
    }


class _PackText(html.parser.HTMLParser):
    """The application pack as plain text, because WhatsApp refuses text/html.

    # * Not a general HTML converter. It knows the tags pack.py emits and turns
    # * them into line breaks and bullets; anything else is dropped to text.
    """

    _BLOCK = {"p", "div", "h1", "h2", "h3", "section", "tr", "br", "ul", "li"}

    def __init__(self) -> None:
        super().__init__()
        self.out: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip += 1
        elif tag in self._BLOCK:
            self.out.append("\n")
            if tag == "li":
                self.out.append("• ")

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._skip = max(0, self._skip - 1)
        elif tag in self._BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self.out.append(data)

    def text(self) -> str:
        lines = [" ".join(line.split()) for line in "".join(self.out).splitlines()]
        kept: list[str] = []
        for line in lines:
            # * Collapse the runs of blank lines the block tags leave behind.
            if not (line or (kept and kept[-1])):
                continue
            # * The pack's <h1> and the page <title> carry the same words, so
            # * the sheet used to open with its own name twice, with a blank
            # * line between - which is why comparing to kept[-1] alone missed
            # * it. Compare to the last line that had anything on it.
            if line:
                previous = next((x for x in reversed(kept) if x), "")
                if line == previous:
                    continue
            kept.append(line)
        return _lay_out("\n".join(kept).strip())


# ! A phone screen is about 40 characters wide in a monospaced document viewer,
# ! and this sheet is read on one, by someone who may be reading slowly. Runs of
# ! bullets are pulled tight, headings get a rule above them, and nothing is
# ! wrapped by us — the viewer wraps, and guessing its width would produce
# ! ragged text on every screen that is not the one we guessed.
_RULE = "─" * 34


def _sentences(line: str) -> list[str]:
    """Split a long paragraph after each sentence, in either language.

    # * A danda ends a Hindi sentence and a full stop an English one. Decimals
    # * and "Rs.436" must not be split on, so a break needs whitespace after it
    # * and a non-digit next.
    """
    out, start = [], 0
    for i, ch in enumerate(line):
        if ch not in ".।":
            continue
        rest = line[i + 1:]
        if not rest.startswith(" ") or not rest[1:2] or rest[1:2].isdigit():
            continue
        out.append(line[start:i + 1].strip())
        start = i + 2
    tail = line[start:].strip()
    if tail:
        out.append(tail)
    return out or [line]


def _lay_out(text: str) -> str:
    """Give the flat conversion the shape of a handout."""
    out: list[str] = []
    for line in text.splitlines():
        if not line:
            continue
        bullet = line.startswith("•")
        numbered = len(line) > 2 and line[0].isdigit() and line[1] in ".)"
        if numbered:
            # A scheme heading: rule above it, so the eye finds the next one.
            if out:
                out += ["", _RULE, ""]
            out.append(line)
            out.append("")
        elif bullet:
            # Bullets belong together; a blank line between each made the
            # document three times longer than the words in it.
            out.append(line)
        else:
            if out and out[-1].startswith("•"):
                out.append("")
            # ! One sentence per line. This is read on a phone, where a
            # ! 400-character benefit summary is a ten-line wall of text and a
            # ! worker loses her place in it. The viewer still wraps each
            # ! sentence; the gaps give her somewhere to stop.
            out.extend(_sentences(line) if len(line) > 150 else [line])
            out.append("")
    while out and not out[-1]:
        out.pop()
    return "\n".join(out) + "\n"


# ! A plain .txt carries no declared encoding, so the reader guesses. Android's
# ! document viewer guessed Windows-1252 and every rupee sign in a real worker's
# ! sheet arrived as "â‚¹2 lakh". The Hindi sheet would have been unreadable from
# ! end to end — the sheet a worker carries to a bank, in the language she chose.
# !
# ! A BOM is how a text file says "I am UTF-8" to a viewer that has no other way
# ! to know. It is three bytes and it fixes ₹, the dashes, the emoji and every
# ! Devanagari character at once.
_BOM = "\ufeff"


def pack_as_text(filename: str, blob: bytes) -> tuple[str, bytes]:
    """(filename, bytes) an HTML pack turned into something WhatsApp will carry."""
    if not filename.lower().endswith((".htm", ".html")):
        return filename, blob
    parser = _PackText()
    parser.feed(blob.decode("utf-8", "replace"))
    parser.close()
    return filename.rsplit(".", 1)[0] + ".txt", (_BOM + parser.text()).encode("utf-8")


def _tag(key: str) -> str:
    """A process-local log handle; a secret prevents phone-number guessing."""
    return hmac.new(_LOG_SALT, key.encode("utf-8"), hashlib.sha256).hexdigest()[:8]


def valid_signature(secret: str, body: bytes, header: str) -> bool:
    """Meta signs every webhook body. An unsigned request is not from Meta.

    # ! compare_digest, never ==. A byte-at-a-time comparison leaks the
    # ! expected signature to anyone patient enough to measure the answer.
    """
    if not header.isascii() or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):])


class WhatsAppBot(Router):
    """Sessions, commands and languages come from Router. This is the wire."""

    channel = "whatsapp"

    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None,
                 token: str | None = None, phone_number_id: str | None = None,
                 app_secret: str | None = None, verify_token: str | None = None) -> None:
        super().__init__(schemes, log)
        env = os.environ.get
        self.token = token or env("WHATSAPP_TOKEN", "")
        self.phone_number_id = phone_number_id or env("WHATSAPP_PHONE_NUMBER_ID", "")
        self.app_secret = app_secret or env("WHATSAPP_APP_SECRET", "")
        self.verify_token = verify_token or env("WHATSAPP_VERIFY_TOKEN", "")
        missing = [name for name, value in (
            ("WHATSAPP_TOKEN", self.token),
            ("WHATSAPP_PHONE_NUMBER_ID", self.phone_number_id),
            # ! Not optional, and not "the endpoint is obscure enough". Without
            # ! the app secret anyone who finds the URL can post whatever they
            # ! like, and the endpoint's whole job is to be reachable.
            ("WHATSAPP_APP_SECRET", self.app_secret),
            ("WHATSAPP_VERIFY_TOKEN", self.verify_token),
        ) if not value]
        if missing:
            raise WhatsAppError(f"{', '.join(missing)} not set — see .env.example")
        # ! Ids Meta may redeliver. A list keeps insertion order so the oldest
        # ! can be dropped; the set is what gets asked.
        self._seen: list[str] = []
        self._seen_set: set[str] = set()
        self._work: queue.Queue = queue.Queue(maxsize=_QUEUE_MAX)

    # * ------------------------------------------------------------- sending

    def send(self, key: str, reply: Reply) -> None:
        lang = self._lang.get(key, DEFAULT_LANG)
        text = reply.text
        if len(text) > (_BODY_MAX if reply.buttons else _TEXT_MAX):
            # ! An interactive body holds a quarter of what a text message does,
            # ! and a result message can exceed it. Send the long part as text,
            # ! then a short prompt that carries the options.
            for start in range(0, len(text), _TEXT_MAX):
                sent = self._deliver(key, {"type": "text", "text": {
                    "preview_url": False, "body": text[start:start + _TEXT_MAX]}})
            text = s("errors.pick_from_list", lang) if reply.buttons else ""

        if text or reply.buttons:
            sent = self._deliver(key, interactive(text, reply.buttons, lang))
        if reply.buttons:
            self._active_keyboard.pop(key, None)
            wamid = self._wamid(sent)
            if wamid:
                self._active_keyboard[key] = wamid

        if reply.audio is not None:
            self._send_audio(key, reply.audio)
        if reply.document is not None:
            filename, blob = pack_as_text(*reply.document)
            media_id = _upload(self.token, self.phone_number_id, filename,
                               blob, _PACK_TEXT_MIME)
            self._deliver(key, {"type": "document",
                                "document": {"id": media_id, "filename": filename}})

    def _deliver(self, key: str, message: dict) -> dict:
        return _post(self.token, f"{self.phone_number_id}/messages", {
            "messaging_product": "whatsapp", "recipient_type": "individual",
            "to": key, **message,
        })

    @staticmethod
    def _wamid(sent: dict) -> str | None:
        messages = sent.get("messages") or []
        return messages[0].get("id") if messages else None

    def _send_audio(self, key: str, path: Path) -> None:
        """Voice is an enhancement; nothing here may invalidate delivered text."""
        mime = _AUDIO_TYPES.get(path.suffix.lower())
        if mime is None:
            print(f"[whatsapp] skipped {path.suffix} voice note — "
                  f"WhatsApp accepts {'/'.join(sorted(_AUDIO_TYPES))}")
            return
        try:
            media_id = _upload(self.token, self.phone_number_id, path.name,
                               path.read_bytes(), mime)
            self._deliver(key, {"type": "audio", "audio": {"id": media_id}})
        except Exception:  # noqa: BLE001 — optional audio cannot invalidate delivered text
            pass  # * the text already carried the message

    # * ----------------------------------------------------------- receiving

    @staticmethod
    def _answer(message: dict) -> tuple[str, str | None]:
        """(what the worker said, the id of the message they tapped).

        # * The second value is None for typed text: only a tap can be stale.
        """
        kind = message.get("type")
        if kind == "text":
            return (message.get("text") or {}).get("body", ""), None
        if kind == "interactive":
            block = message.get("interactive") or {}
            reply = block.get("button_reply") or block.get("list_reply") or {}
            # ! Missing context is an unbound tap, never an ordinary typed answer.
            return reply.get("id", ""), (message.get("context") or {}).get("id") or ""
        if kind == "button":
            # * A template quick-reply. Not used by the flow today, but it
            # * arrives in the same shape and costs one line to accept.
            return (message.get("button") or {}).get("payload", ""), None
        # ! An image, a voice note, a location. The flow only understands text
        # ! and taps, and an empty answer makes it re-ask rather than guess.
        return "", None

    def handle_update(self, value: dict) -> None:
        """One webhook `value` object: zero or more messages, or a status."""
        for message in value.get("messages") or []:
            wamid = message.get("id") or ""
            if wamid and wamid in self._seen_set:
                # ! Meta redelivers anything it thinks failed. Replaying an
                # ! answer would record the same event twice and, worse, advance
                # ! the intake past a question the worker answered once.
                print(f"[whatsapp] duplicate {_tag(wamid)} ignored")
                continue
            if wamid:
                self._seen.append(wamid)
                self._seen_set.add(wamid)
                if len(self._seen) > _SEEN_MAX:
                    self._seen_set.discard(self._seen.pop(0))

            key = str(message.get("from") or "")
            if not key:
                continue
            answer, tapped = self._answer(message)
            if tapped is not None:
                if (key not in self.sessions
                        or tapped != self._active_keyboard.get(key)):
                    # ! An old keyboard must not answer the current question.
                    # ! WhatsApp has no toast, so the refusal is a message.
                    lang = self._lang.get(key, DEFAULT_LANG)
                    self._deliver(key, interactive(s("errors.stale_button", lang), (), lang))
                    continue
                # ! Retire before dispatch: a duplicate tap on a multi-select
                # ! stays in the SAME state, and a later session can revisit it.
                self._active_keyboard.pop(key, None)
            self.turn(key, answer)

    def enqueue(self, value: dict) -> None:
        """Hand a verified webhook body to the worker thread and return."""
        self._work.put_nowait(value)

    def work_once(self, block: bool = True, timeout: float | None = None) -> bool:
        """Process one queued webhook. One thread, so sessions need no lock."""
        try:
            value = self._work.get(block=block, timeout=timeout)
        except queue.Empty:
            return False
        try:
            if value is None:
                return False
            # ! One failed recipient must not discard the rest of a Meta batch.
            for message in value.get("messages") or []:
                self._process_message(message)
        finally:
            self._work.task_done()
        return True

    def _process_message(self, message: dict) -> None:
        value = {"messages": [message]}
        try:
            self.handle_update(value)
        except (urllib.error.URLError, TimeoutError):
            # ! Meta is unreachable. That says nothing about this worker's
            # ! conversation, so their answers stay. Nothing to back off here —
            # ! the next webhook arrives when it arrives.
            print("[whatsapp] send failed: network unreachable — session kept")
        except WhatsAppError as e:
            if _is_transient(e):
                print(f"[whatsapp] HTTP {e.status} — session kept")
            else:
                print(f"[whatsapp] send failed: HTTP {e.status}")
                self._abandon(value)
        except Exception as e:  # noqa: BLE001
            # ! One broken conversation must never stop the worker thread while
            # ! other workers are mid-session.
            print(f"[whatsapp] update failed: {type(e).__name__}")
            self._abandon(value)

    def _abandon(self, value: dict) -> None:
        """Find the worker behind a failed webhook, then let the router drop it."""
        try:
            for message in value.get("messages") or []:
                key = str(message.get("from") or "")
                if key:
                    self.abandon(key)
        except Exception as recovery_error:  # noqa: BLE001 — recovery must not stop the thread
            print(f"[whatsapp] recovery notice failed: {type(recovery_error).__name__}")

    # * -------------------------------------------------------------- server

    def serve_forever(self, port: int | None = None) -> None:
        port = int(os.environ.get("WHATSAPP_PORT", "8080")) if port is None else port
        # ! Loopback by default. Plain HTTP on purpose — Meta requires HTTPS, so
        # ! this must sit behind a proxy that terminates TLS (deploy/RUNBOOK.md);
        # ! a self-signed certificate here would be refused by Meta while
        # ! looking like it worked. Binding every interface would also publish
        # ! an unencrypted copy of the endpoint beside the encrypted one.
        host = os.environ.get("WHATSAPP_BIND", "127.0.0.1")
        server = ThreadingHTTPServer((host, port), _webhook_handler(self))
        # ! Finish accepting active requests before putting the stop sentinel
        # ! behind the last accepted batch. Otherwise an HTTP thread can enqueue
        # ! after the worker has exited and still tell Meta it accepted the work.
        server.daemon_threads = False
        worker = threading.Thread(target=self._drain, daemon=True, name="sathi-whatsapp")
        worker.start()

        def stop(signum, frame):
            raise KeyboardInterrupt

        main_thread = threading.current_thread() is threading.main_thread()
        previous_term = signal.signal(signal.SIGTERM, stop) if main_thread else None
        try:
            print(f"[whatsapp] listening on {host}:{server.server_address[1]}, "
                  f"{len(self.schemes)} scheme(s) loaded")
            server.serve_forever()
        finally:
            try:
                server.server_close()
                self._work.put(None)
                # ! main.py closes the shared event database after this returns.
                # ! Join first so no worker can write through a closed connection.
                worker.join()
            finally:
                if main_thread:
                    signal.signal(signal.SIGTERM, previous_term)

    def _drain(self) -> None:
        while self.work_once():
            pass


def _webhook_messages(payload: dict, phone_number_id: str) -> list[dict]:
    """Validate a whole batch before acceptance; retain no contact-name objects."""
    def objects(value):
        if not isinstance(value, list) or any(not isinstance(v, dict) for v in value):
            raise ValueError("expected object list")
        return value

    if not isinstance(payload, dict):
        raise ValueError("expected object")
    messages = []
    for entry in objects(payload.get("entry", [])):
        for change in objects(entry.get("changes", [])):
            value = change.get("value", {})
            if not isinstance(value, dict):
                raise ValueError("expected value object")
            metadata = value.get("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError("expected metadata object")
            if metadata.get("phone_number_id", phone_number_id) != phone_number_id:
                continue
            for message in objects(value.get("messages", [])):
                for field in ("id", "from", "type"):
                    if not isinstance(message.get(field), str) or not 0 < len(message[field]) <= 256:
                        raise ValueError("invalid message identity")
                if not message["from"].isascii() or not message["from"].isdigit():
                    raise ValueError("invalid sender")
                for field in ("text", "interactive", "context", "button"):
                    if field in message and not isinstance(message[field], dict):
                        raise ValueError("invalid message object")
                for field in ("button_reply", "list_reply"):
                    block = message.get("interactive", {})
                    if field in block and not isinstance(block[field], dict):
                        raise ValueError("invalid interactive reply")
                answer, tapped = WhatsAppBot._answer(message)
                if not isinstance(answer, str) or len(answer) > _TEXT_MAX:
                    raise ValueError("invalid answer")
                if tapped is not None and (not isinstance(tapped, str) or len(tapped) > 256):
                    raise ValueError("invalid context")
                messages.append({k: message[k] for k in (
                    "id", "from", "type", "text", "interactive", "context", "button") if k in message})
                if len(messages) > 100:
                    raise ValueError("too many messages")
    return messages


def _webhook_handler(bot: WhatsAppBot) -> type[BaseHTTPRequestHandler]:
    """The HTTP surface: one verification GET, one signed POST, nothing else."""

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def setup(self) -> None:
            self.request.settimeout(5)
            super().setup()

        def _respond(self, status: int, body: bytes = b"") -> None:
            # ! Close after every request, including rejected bodies left unread.
            self.close_connection = True
            self.send_response(status)
            self.send_header("connection", "close")
            self.send_header("content-type", "text/plain; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            if body:
                self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802 — BaseHTTPRequestHandler's naming
            from urllib.parse import parse_qs, urlparse

            query = parse_qs(urlparse(self.path).query)
            mode = (query.get("hub.mode") or [""])[0]
            token = (query.get("hub.verify_token") or [""])[0]
            challenge = (query.get("hub.challenge") or [""])[0]
            # ! compare_digest here too: this token is a shared secret and the
            # ! endpoint answers strangers.
            if mode == "subscribe" and hmac.compare_digest(
                    token.encode("utf-8"), bot.verify_token.encode("utf-8")):
                self._respond(200, challenge.encode("utf-8"))
            else:
                self._respond(403)

        def do_POST(self) -> None:  # noqa: N802
            try:
                lengths = self.headers.get_all("content-length") or []
                if len(lengths) != 1 or self.headers.get("transfer-encoding"):
                    raise ValueError("ambiguous body length")
                length = int(lengths[0])
                if length < 0:
                    raise ValueError("negative body length")
            except ValueError:
                self._respond(400)
                return
            if length > _WEBHOOK_MAX:
                self._respond(413)
                return
            try:
                body = self.rfile.read(length)
            except TimeoutError:
                self._respond(408)
                return
            if len(body) != length:
                self._respond(400)
                return
            signature = self.headers.get("x-hub-signature-256", "")
            if not valid_signature(bot.app_secret, body, signature):
                # ! Say nothing useful. An attacker probing the endpoint learns
                # ! only that it exists.
                self._respond(403)
                return
            try:
                payload = json.loads(body.decode("utf-8"))
                messages = _webhook_messages(payload, bot.phone_number_id)
            except (ValueError, RecursionError):
                self._respond(400)
                return
            # ! Acknowledge acceptance, not processing. If capacity is exhausted,
            # ! Meta must retry; a 200 followed by failed enqueue loses answers.
            try:
                if messages:
                    bot.enqueue({"messages": messages})
            except queue.Full:
                self._respond(503)
                return
            self._respond(200)

        def log_message(self, *args) -> None:
            # ! Silence. The default access log writes the request line and the
            # ! client address, and this endpoint's traffic is workers.
            pass

    return Handler


def _self_check() -> None:
    """Runs offline: the network is stubbed, the translation is what we test."""
    import sys

    from sathi.core.schemes import Criterion as C

    mod = sys.modules[__name__]

    # * ---------------------------------------------------------- rendering
    assert interactive("q", (), "en")["type"] == "text"

    three = tuple(Button(f"option {i}", f"v{i}") for i in range(3))
    block = interactive("q", three, "en")["interactive"]
    assert block["type"] == "button" and len(block["action"]["buttons"]) == 3

    four = tuple(Button(f"option {i}", f"v{i}") for i in range(4))
    block = interactive("q", four, "en")["interactive"]
    assert block["type"] == "list", "four options must become a list"
    assert block["action"]["button"] == "Choose"

    try:
        interactive("q", tuple(Button(str(i), str(i)) for i in range(11)), "en")
        raise AssertionError("eleven options were rendered as a ten-row list")
    except WhatsAppError:
        pass

    # * Every real screen is rendered through these limits in both languages by
    # * tests/test_all_paths.py, which walks 486 paths per language. Doing it
    # * here as well would be a second, weaker copy of that gate.

    # ! A long label spills into the description instead of being cut off.
    long_label = ("Aadhaar-linked mobile number (if you have none, a centre can "
                  "register you by fingerprint)")
    row = _row(Button(long_label, "doc:4"), 4)
    assert len(row["title"]) <= _ROW_TITLE and row["description"]
    assert "fingerprint" in row["description"], row

    # * --------------------------------------------------------- signatures
    secret, body = "s3cret", b'{"entry":[]}'
    good = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert valid_signature(secret, body, good)
    assert not valid_signature(secret, body + b" ", good)
    assert not valid_signature(secret, body, good[:-1] + "0")
    assert not valid_signature(secret, body, "")
    assert not valid_signature("wrong", body, good)

    # * ------------------------------------------------------------- pack
    name, blob = pack_as_text("pack.html", b"<html><head><style>p{}</style></head>"
                                           b"<body><h1>Title</h1><ul><li>One</li>"
                                           b"<li>Two</li></ul><p>Tail</p></body></html>")
    text = blob.decode("utf-8")
    assert name == "pack.txt"
    assert "p{}" not in text, "stylesheet leaked into the pack text"
    assert "Title" in text and "• One" in text and "Tail" in text, text
    assert "<" not in text, text
    assert pack_as_text("note.txt", b"x") == ("note.txt", b"x")

    # * ------------------------------------------------------- conversation
    schemes = {"A": Scheme(
        code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
        verified_on="2026-09-01", verified_by="a",
        benefit={"annual_value_inr": 1000, "value_basis": "annual_payout", "summary_hi": "प"},
        criteria=(C("age", "between", [18, 40], "u", pass_hi="ok", fail_hi="no"),),
        exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
    )}
    credentials = dict(token="t", phone_number_id="1", app_secret="s", verify_token="v")

    real_post, real_upload = mod._post, mod._upload
    sent: list[dict] = []
    uploads: list[tuple[str, str]] = []

    def _wire(token, path, payload):
        sent.append(payload)
        return {"messages": [{"id": f"wamid.{len(sent)}"}]}

    def _fake_upload(token, phone_id, filename, blob, mime):
        uploads.append((filename, mime))
        return "media-1"

    mod._post, mod._upload = _wire, _fake_upload
    try:
        bot = WhatsAppBot(schemes, **credentials)

        def _incoming(text=None, tap=None, context=None, wamid=None, sender="911"):
            message = {"id": wamid or f"in.{len(sent)}.{time.time()}", "from": sender}
            if tap is None:
                message |= {"type": "text", "text": {"body": text}}
            else:
                message |= {"type": "interactive",
                            "interactive": {"type": "button_reply",
                                            "button_reply": {"id": tap, "title": tap}}}
                if context:
                    message["context"] = {"id": context}
            bot.handle_update({"messages": [message]})

        _incoming("/start")
        assert "Choose your language" in sent[-1]["interactive"]["body"]["text"]
        language_keyboard = bot._active_keyboard["911"]

        # ! A tap from a keyboard we never sent must not answer anything.
        before = len(sent)
        _incoming(tap="lang:en", context="wamid.does-not-exist")
        assert "911" not in bot.sessions or bot.sessions["911"].state.value == "language"
        assert s("errors.stale_button", "hi") in sent[-1]["text"]["body"]
        assert len(sent) == before + 1

        _incoming(tap="lang:en", context=language_keyboard)
        assert "Yojana Sathi" in sent[-1]["interactive"]["body"]["text"], sent[-1]
        assert bot.sessions["911"].state.value == "consent"

        # ! A duplicate delivery of the SAME message id changes nothing. Meta
        # ! retries whenever it doubts our 200.
        consent_keyboard = bot._active_keyboard["911"]
        _incoming(tap="consent_yes", context=consent_keyboard, wamid="dup.1")
        after_first = bot.sessions["911"].state.value
        count = len(sent)
        _incoming(tap="consent_yes", context=consent_keyboard, wamid="dup.1")
        assert len(sent) == count, "a redelivered webhook was processed twice"
        assert bot.sessions["911"].state.value == after_first

        # ! And a second tap on the retired keyboard cannot answer the NEXT
        # ! question — the bug that cost a screening on Telegram.
        _incoming(tap="consent_yes", context=consent_keyboard, wamid="dup.2")
        assert bot.sessions["911"].state.value == after_first
        assert s("errors.stale_button", "en") in sent[-1]["text"]["body"]

        # * An image or a voice note is not an answer; the flow re-asks.
        state_keyboard = bot._active_keyboard["911"]
        bot.handle_update({"messages": [{"id": "img.1", "from": "911", "type": "image",
                                         "image": {"id": "x"}}]})
        assert bot.sessions["911"].state.value == after_first

        # * A status callback carries no messages and must be ignored entirely.
        count = len(sent)
        bot.handle_update({"statuses": [{"id": "wamid.1", "status": "delivered"}]})
        assert len(sent) == count

        # ! A long body plus buttons is split, because an interactive body holds
        # ! a quarter of what a text message does.
        count = len(sent)
        bot.send("911", Reply(text="x" * (_BODY_MAX + 50),
                              buttons=(Button("Yes", "yes"), Button("No", "no"))))
        assert len(sent) == count + 2, "a long question was not split"
        assert sent[-2]["type"] == "text" and len(sent[-2]["text"]["body"]) > _BODY_MAX
        assert len(sent[-1]["interactive"]["body"]["text"]) <= _BODY_MAX

        # * The pack is flattened and uploaded as text, never as HTML.
        bot.send("911", Reply(text="pack", document=("pack.html", b"<p>hello</p>")))
        assert uploads[-1] == ("pack.txt", _PACK_TEXT_MIME), uploads[-1]
        assert sent[-1]["document"]["filename"] == "pack.txt"

        # ! A .wav voice note is skipped, not sent and not fatal.
        count = len(sent)
        bot.send("911", Reply(text="hi", audio=Path("/tmp/sathi.wav")))
        assert len(sent) == count + 1, "an unsupported voice note was sent anyway"
        bot.send("911", Reply(text="hi", audio=Path(__file__)))  # * .py: also skipped

        # ! The phone number never reaches a log line.
        assert "911" not in _tag("911")

        # * A permanent failure abandons the turn and tells the worker; a
        # * transient one keeps their answers.
        for status, survives in ((400, False), (429, True), (503, True)):
            recovering = WhatsAppBot(schemes, **credentials)
            mod._post = _wire
            recovering.handle_update({"messages": [
                {"id": "r.1", "from": "922", "type": "text", "text": {"body": "/start"}}]})
            assert "922" in recovering.sessions

            def _failing(token, path, payload):
                raise WhatsAppError(f"send failed: {status}", status)

            mod._post = _failing
            recovering.enqueue({"messages": [
                {"id": "r.2", "from": "922", "type": "text", "text": {"body": "lang:en"}}]})
            assert recovering.work_once(block=False) is True
            assert ("922" in recovering.sessions) is survives, status
            mod._post = _wire
        assert recovering.work_once(block=False) is False, "the queue was not drained"

        # ! A network failure is not a broken conversation.
        keep = WhatsAppBot(schemes, **credentials)
        mod._post = _wire
        keep.handle_update({"messages": [
            {"id": "k.1", "from": "933", "type": "text", "text": {"body": "/start"}}]})

        def _offline(token, path, payload):
            raise urllib.error.URLError("offline")

        mod._post = _offline
        keep.enqueue({"messages": [
            {"id": "k.2", "from": "933", "type": "text", "text": {"body": "lang:en"}}]})
        keep.work_once(block=False)
        assert "933" in keep.sessions, "a network blip discarded a worker's answers"
    finally:
        mod._post, mod._upload = real_post, real_upload

    # * ------------------------------------------------------- credentials
    for absent in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_NUMBER_ID",
                   "WHATSAPP_APP_SECRET", "WHATSAPP_VERIFY_TOKEN"):
        partial = {k: v for k, v in credentials.items()
                   if k != absent.removeprefix("WHATSAPP_").lower()}
        saved = os.environ.pop(absent, None)
        try:
            WhatsAppBot(schemes, **partial)
            raise AssertionError(f"started without {absent}")
        except WhatsAppError as e:
            assert absent in str(e), e
        finally:
            if saved is not None:
                os.environ[absent] = saved

    # * ---------------------------------------------------------- transport
    for status, transient in ((429, True), (500, True), (503, True),
                              (400, False), (403, False)):
        assert _is_transient(WhatsAppError("x", status)) is transient, status

    import io

    real_urlopen = urllib.request.urlopen
    try:
        def _http_failure(req, timeout):
            body = json.dumps({"error": {"message": "Unsupported post request"}}).encode()
            raise urllib.error.HTTPError(req.full_url, 400, "Bad Request", {},
                                         io.BytesIO(body))

        urllib.request.urlopen = _http_failure
        try:
            _post("t", "1/messages", {"to": "911"})
            raise AssertionError("an HTTP failure was swallowed")
        except WhatsAppError as e:
            assert e.status == 400 and "Unsupported post request" not in str(e), e

        class _BrokenRead:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                raise ConnectionResetError("connection reset")

        urllib.request.urlopen = lambda *a, **k: _BrokenRead()
        try:
            _post("t", "1/messages", {"to": "911"})
            raise AssertionError("a broken response was swallowed")
        except urllib.error.URLError:
            pass  # * the worker keeps their answers
    finally:
        urllib.request.urlopen = real_urlopen

    print("whatsapp.py OK")


if __name__ == "__main__":
    _self_check()
