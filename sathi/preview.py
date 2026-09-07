"""Drive a channel's real renderer in the terminal. Run:

    python3 -m sathi.main --preview whatsapp
    python3 -m sathi.main --preview telegram

# ! `python3 -m sathi.main` already screens a worker in the terminal, but it
# ! renders with the terminal's own printer. What it cannot show is what the
# ! CHANNEL does to that same reply: WhatsApp's three-button ceiling and the
# ! list it falls back to, a body truncated at 1024 rather than 4096, Telegram's
# ! inline keyboard rows. Those bugs only appeared on a real phone.
#
# ! So this runs the actual bot object with the actual renderer, and stubs the
# ! one function that touches the network — telegram._call, whatsapp._post.
# ! Nothing is sent. What prints is what Meta or Telegram would have received.
#
# ! Credentials are dummies on purpose. Both constructors refuse to start
# ! without them, and preview must not need a real token to draw a keyboard.
"""

import sys

from sathi.core.schemes import Scheme

_DUMMY = "preview"


# * ------------------------------------------------------------------ render

def _rows(payload: dict) -> list[tuple[str, str]]:
    """Every tappable thing in an outbound payload, as (label, value)."""
    out: list[tuple[str, str]] = []

    markup = payload.get("reply_markup") or {}
    for row in markup.get("inline_keyboard") or []:
        for b in row:
            out.append((b.get("text", ""), b.get("callback_data", "")))

    block = payload.get("interactive") or {}
    action = block.get("action") or {}
    for b in action.get("buttons") or []:
        reply = b.get("reply") or {}
        out.append((reply.get("title", ""), reply.get("id", "")))
    for section in action.get("sections") or []:
        for r in section.get("rows") or []:
            out.append((r.get("title", ""), r.get("id", "")))
    return out


def _body(payload: dict) -> str:
    if "text" in payload and isinstance(payload["text"], dict):
        return payload["text"].get("body", "")          # * whatsapp text
    if isinstance(payload.get("text"), str):
        return payload["text"]                          # * telegram
    block = payload.get("interactive") or {}
    return (block.get("body") or {}).get("text", "")    # * whatsapp interactive


def _shape(payload: dict) -> str:
    """The label that tells you WHICH WhatsApp form the renderer chose."""
    block = payload.get("interactive") or {}
    if block:
        return f"interactive/{block.get('type', '?')}"
    if payload.get("type"):
        return str(payload["type"])
    return "message"


def _show(payload: dict, limit: int) -> list[tuple[str, str]]:
    """Print one outbound message the way the channel will carry it."""
    body = _body(payload)
    print(f"\n  ── {_shape(payload)} ─ {len(body)} chars", end="")
    # ! The ceiling is the point of this tool. A body at the limit is one
    # ! edit away from being cut on a worker's screen, silently.
    print(f"  \033[33m(at the {limit} limit)\033[0m" if len(body) >= limit else "")
    for line in body.splitlines() or [""]:
        print(f"  │ {line}")
    buttons = _rows(payload)
    for i, (label, value) in enumerate(buttons, 1):
        flag = "  \033[33m← 20+ chars, WhatsApp truncates\033[0m" if len(label) > 20 else ""
        print(f"  │ [{i}] {label}{flag}")
    return buttons


# * ------------------------------------------------------------------- drive

def run(channel: str, schemes: dict[str, Scheme], log=None) -> int:
    sent: list[dict] = []

    if channel == "whatsapp":
        from sathi.channels import whatsapp as mod
        from sathi.channels.whatsapp import WhatsAppBot

        bot = WhatsAppBot(schemes, log, token=_DUMMY, phone_number_id=_DUMMY,
                          app_secret=_DUMMY, verify_token=_DUMMY)
        mod._post = lambda token, path, payload: (
            sent.append(payload) or {"messages": [{"id": f"wamid.{len(sent)}"}]})
        mod._upload = lambda *a, **k: sent.append({"type": "document",
                                                   "text": "<pack.pdf>"}) or {"id": "media.1"}
        limit = mod._BODY_MAX

        def feed(text: str | None, tap: str | None) -> None:
            message = {"id": f"in.{len(sent)}", "from": "911"}
            if tap is None:
                message |= {"type": "text", "text": {"body": text}}
            else:
                # ! No context id: a tap without one skips the stale-keyboard
                # ! check, which is what we want when there is no real phone.
                message |= {"type": "interactive", "interactive": {
                    "type": "button_reply", "button_reply": {"id": tap, "title": tap}}}
            bot.handle_update({"messages": [message]})

    elif channel == "telegram":
        from sathi.channels import telegram as mod
        from sathi.channels.telegram import TelegramBot

        bot = TelegramBot(schemes, log, token=_DUMMY)
        state = {"mid": 0}

        def _call(token, method, payload):
            state["mid"] += 1
            if method in ("sendMessage", "editMessageText"):
                sent.append(payload)
            return {"ok": True, "result": {"message_id": state["mid"]}}

        mod._call = _call
        mod._upload = lambda *a, **k: sent.append({"text": "<pack.pdf>"}) or {"ok": True}
        limit = 4096

        def feed(text: str | None, tap: str | None) -> None:
            if tap is None:
                bot.handle_update({"message": {
                    "chat": {"id": 1}, "message_id": state["mid"] + 1, "text": text}})
            else:
                bot.handle_update({"callback_query": {
                    "id": "1", "data": tap,
                    "message": {"chat": {"id": 1}, "message_id": state["mid"]}}})
    else:
        print(f"unknown channel {channel!r} — use telegram or whatsapp", file=sys.stderr)
        return 2

    print(f"\npreview: {channel} — nothing is sent, this is what the wire would carry.")
    print("type text, or a button number. blank line or ctrl-d quits.\n")

    buttons: list[tuple[str, str]] = []
    seen = 0
    feed("/start", None)
    for payload in sent[seen:]:
        buttons = _show(payload, limit) or buttons
    seen = len(sent)

    while True:
        try:
            raw = input("\nyou > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not raw:
            return 0

        if raw.isdigit() and buttons and 1 <= int(raw) <= len(buttons):
            label, value = buttons[int(raw) - 1]
            print(f"      (tapped {label!r} → {value!r})")
            feed(None, value)
        else:
            feed(raw, None)

        fresh = sent[seen:]
        seen = len(sent)
        if not fresh:
            print("  (the channel sent nothing back)")
            continue
        for payload in fresh:
            got = _show(payload, limit)
            if got:
                buttons = got


def _self_check() -> None:
    """The parsing is the only logic here — the rest is print()."""
    # * Telegram: an inline keyboard is rows of rows.
    tg = {"chat_id": "1", "text": "pick", "reply_markup": {
        "inline_keyboard": [[{"text": "हिंदी", "callback_data": "lang:hi"}],
                            [{"text": "English", "callback_data": "lang:en"}]]}}
    assert _body(tg) == "pick"
    assert _rows(tg) == [("हिंदी", "lang:hi"), ("English", "lang:en")]
    assert _shape(tg) == "message"

    # * WhatsApp: three or fewer options are buttons.
    wa_btn = {"type": "interactive", "interactive": {
        "type": "button", "body": {"text": "pick"},
        "action": {"buttons": [{"type": "reply", "reply": {"id": "a", "title": "A"}}]}}}
    assert _body(wa_btn) == "pick"
    assert _rows(wa_btn) == [("A", "a")]
    assert _shape(wa_btn) == "interactive/button"

    # ! Four or more become a list, and the rows live somewhere else entirely.
    # ! Reading only `buttons` is how a preview silently shows an empty question.
    wa_list = {"type": "interactive", "interactive": {
        "type": "list", "body": {"text": "state?"},
        "action": {"sections": [{"rows": [{"id": "UK", "title": "उत्तराखंड"},
                                          {"id": "UP", "title": "उत्तर प्रदेश"}]}]}}}
    assert _rows(wa_list) == [("उत्तराखंड", "UK"), ("उत्तर प्रदेश", "UP")]
    assert _shape(wa_list) == "interactive/list"

    # * A plain WhatsApp text message carries its body one level deeper.
    assert _body({"type": "text", "text": {"preview_url": False, "body": "hi"}}) == "hi"
    assert _rows({"type": "text", "text": {"body": "hi"}}) == []

    print("preview.py OK")
