"""Entry point.

    python3 -m sathi.main                 # one screening in the terminal
    python3 -m sathi.main --telegram      # run the bot (needs TELEGRAM_TOKEN)
    python3 -m sathi.main --whatsapp      # serve the webhook (needs WHATSAPP_*)
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
    servable = 0
    for code, sc in schemes.items():
        # ! Not warnings to be silenced. Anything printed here as UNKNOWN is
        # ! served to workers as UNKNOWN — that is the whole point.
        if sc.stubs:
            print(f"  {code}: {len(sc.stubs)} unresearched value(s) → served as UNKNOWN")
        elif not sc.is_human_verified:
            # ! Never print "verified" off a file that says PENDING. The word
            # ! used to appear here for exactly the schemes the README told
            # ! people not to trust.
            print(f"  {code}: PENDING HUMAN VERIFICATION → served as UNKNOWN")
        else:
            servable += 1
            print(f"  {code}: verified {sc.verified_on} by {sc.verified_by}")
    if servable == 0:
        print("  ! no scheme is signed off yet — every worker gets UNKNOWN for all of them.")
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
    # ! One process, one channel. Two pollers on one Telegram token steal each
    # ! other's updates, and one process serving both would take both down
    # ! together; deploy/ runs a unit per channel.
    ap.add_argument("--whatsapp", action="store_true",
                    help="serve the WhatsApp webhook (behind a TLS proxy)")
    ap.add_argument("--preview", metavar="CHANNEL", default=None,
                    help="render a screening as telegram or whatsapp would, "
                         "in the terminal, sending nothing")
    ap.add_argument("--port", type=int, default=None,
                    help="webhook port (default WHATSAPP_PORT, else 8080)")
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
    # ! Preview traffic is synthetic and must never enter the impact database.
    log = None if args.no_db or args.preview else EventLog(args.db)
    try:
        if args.preview:
            # ! Before the channels, and before either token is required: the
            # ! whole point is to see a keyboard without credentials.
            from sathi.preview import run as preview_run

            return preview_run(args.preview, schemes, log)
        if args.telegram and args.whatsapp:
            print("pick one channel per process — see deploy/RUNBOOK.md", file=sys.stderr)
            return 2
        if args.telegram:
            from sathi.channels.telegram import TelegramBot, TelegramError
            from sathi.pack import links

            # ! Only this process serves /p/<token>. The store is a dict in
            # ! memory, so the process that PUBLISHES a pack is the only one
            # ! that can serve it — a second copy in the WhatsApp process would
            # ! answer 410 for half the links. See deploy/RUNBOOK.md for the
            # ! Caddy route that sends /p/* here.
            # ! Off unless PACK_BASE_URL is set: a link to a host nobody can
            # ! reach is worse than no link, and a laptop has no such host.
            # * The scheme count on the page comes from what this process
            # * actually loaded, not from a number typed into a config file
            # * that would quietly go stale the next time a scheme is signed.
            # !
            # ! SERVABLE, not loaded. The landing page labels this number
            # ! "schemes signed off and screened against", and a drafted file
            # ! sitting unsigned in data/schemes is neither - it returns UNKNOWN
            # ! to every worker. Publishing len(schemes) would have claimed
            # ! credit for two files the moment they were drafted, which is the
            # ! exact shape of overstatement this project keeps auditing itself
            # ! for. The number rises when you sign, not when I write a file.
            os.environ.setdefault(
                "SCHEME_COUNT", str(sum(1 for sc in schemes.values() if sc.is_servable)))
            links.serve_in_background()

            try:
                TelegramBot(schemes, log).run_forever()
            except TelegramError as e:
                print(e, file=sys.stderr)
                return 2
            return 0
        if args.whatsapp:
            from sathi.channels.whatsapp import WhatsAppBot, WhatsAppError

            try:
                WhatsAppBot(schemes, log).serve_forever(args.port)
            except WhatsAppError as e:
                print(e, file=sys.stderr)
                return 2
            return 0
        return run_cli(schemes, log)
    finally:
        if log is not None:
            log.close()


if __name__ == "__main__":
    sys.exit(main())
