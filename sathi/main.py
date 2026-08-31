"""Entry point.

    python3 -m sathi.main                 # one screening in the terminal
    python3 -m sathi.main --telegram      # run the bot (needs TELEGRAM_TOKEN)
    python3 -m sathi.main --no-db         # don't write to the event log

# ! The terminal mode is the week-6 acceptance test, not a toy: with
# ! LLM_API_KEY unset it must carry a worker from consent to application pack
# ! using numbered choices only. If that works, the hybrid design holds.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path

from sathi.conversation.flow import Conversation
from sathi.core.schemes import SchemeError, load_all
from sathi.metrics.events import EventLog
from sathi.render import audio, llm


def startup_report(schemes: dict) -> None:
    """Say out loud what is verified and what is not, every single start."""
    print(f"schemes loaded: {len(schemes)}")
    for code, sc in schemes.items():
        if sc.stubs:
            # ! Not a warning to be silenced. These schemes are served as
            # ! UNKNOWN, which is the whole point of the stub mechanism.
            print(f"  {code}: {len(sc.stubs)} unresearched value(s) → served as UNKNOWN")
        else:
            print(f"  {code}: verified {sc.verified_on}")
    print(f"LLM: {'on' if llm.is_available() else 'off (buttons + templated Hindi)'}")
    print(f"TTS: {'on' if audio.is_available() else 'off (text only)'}")


def run_cli(schemes: dict, log: EventLog | None) -> int:
    convo = Conversation(schemes, log, channel="cli")
    replies = convo.start()
    while True:
        buttons: tuple = ()
        for reply in replies:
            print("\n" + reply.text)
            if reply.buttons:
                buttons = reply.buttons
                for i, b in enumerate(reply.buttons, start=1):
                    print(f"  [{i}] {b.label}")
            if reply.document is not None:
                # * Terminal mode only: on a channel the pack is streamed to the
                # * worker and never written to disk. Here the operator needs a
                # * file they can open, so it goes to a temp dir.
                name, blob = reply.document
                out = Path(tempfile.gettempdir()) / name
                out.write_bytes(blob)
                print(f"  → pack written to {out}")
            if reply.end:
                return 0
        try:
            raw = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        # * A number picks a button; anything else is passed through as typed text.
        if raw.isdigit() and buttons and 1 <= int(raw) <= len(buttons):
            answer = buttons[int(raw) - 1].value
        else:
            answer = raw
        replies = convo.handle(answer)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Scheme Sathi")
    ap.add_argument("--telegram", action="store_true", help="run the Telegram bot")
    ap.add_argument("--schemes", default="data/schemes")
    ap.add_argument("--db", default=os.environ.get("DB_PATH", "./sathi.db"))
    ap.add_argument("--no-db", action="store_true", help="run without the event log")
    args = ap.parse_args(argv)

    try:
        schemes = load_all(args.schemes)
    except SchemeError as e:
        # ! Structural problems stop the app. A scheme file we cannot parse is
        # ! not something to work around at runtime in front of a worker.
        print(f"scheme files are broken, refusing to start:\n  {e}", file=sys.stderr)
        return 2
    if not schemes:
        print(f"no scheme files in {args.schemes}", file=sys.stderr)
        return 2

    startup_report(schemes)
    log = None if args.no_db else EventLog(args.db)
    try:
        if args.telegram:
            from sathi.channels.telegram import TelegramBot, TelegramError

            try:
                TelegramBot(schemes, log).run_forever()
            except TelegramError as e:
                print(e, file=sys.stderr)
                return 2
            return 0
        return run_cli(schemes, log)
    finally:
        if log is not None:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
