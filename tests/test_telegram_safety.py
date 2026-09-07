"""Offline Telegram privacy/delivery regressions, run by check.py.

# * Stubs only the wire; real routing, polling and clearing run below.
# ! No credentials or real messaging identifiers are used.
"""

import contextlib
import io
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sathi.channels import telegram


def test_group_messages_cannot_share_a_worker_profile():
    bot = telegram.TelegramBot({}, token="offline")
    with patch.object(telegram, "_call") as wire:
        bot.handle_update({"message": {"chat": {"id": -123, "type": "group"},
                                        "message_id": 1, "text": "/start"}})
    assert not bot.sessions and not wire.called


def test_operational_logs_do_not_echo_identifiers_or_exception_payloads():
    bot = telegram.TelegramBot({}, token="offline")
    output = io.StringIO()
    with patch.object(telegram, "_call", return_value={"ok": True}), contextlib.redirect_stdout(output):
        bot.clear_chat("synthetic-private-chat", from_message_id=3, deep=True)
    update = {"update_id": 1, "message": {"chat": {"id": 123}, "text": "x"}}
    with patch.object(telegram, "_call", return_value={"result": [update]}), \
            patch.object(bot, "handle_update", side_effect=ValueError("synthetic-private-payload")), \
            patch.object(bot, "_abandon"), contextlib.redirect_stdout(output):
        bot.poll_once()
    assert "synthetic-private" not in output.getvalue()


def test_repeated_update_id_is_not_applied_twice():
    bot = telegram.TelegramBot({}, token="offline")
    update = {"update_id": 4, "message": {"chat": {"id": 123}, "text": "x"}}
    with patch.object(telegram, "_call", return_value={"result": [update, update]}), \
            patch.object(bot, "handle_update") as handle:
        bot.poll_once()
    assert handle.call_count == 1 and bot._offset == 5


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_telegram_safety.py OK")
