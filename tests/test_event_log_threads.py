"""Thread safety of the event log. Run: python3 tests/test_event_log_threads.py

# ! This file exists because of a live bug. The WhatsApp adapter answers the
# ! webhook on one thread and drains its work queue on another, and both log.
# ! sqlite3 refuses a connection outside its creating thread, so every WhatsApp
# ! turn raised and every worker got the "screening stopped" notice instead of
# ! an answer. Telegram never showed it — it polls on a single thread.
#
# ! If someone drops check_same_thread or the lock in events.py, this fails.
"""

import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.metrics.events import EventLog


def test_log_from_another_thread() -> None:
    """The exact shape of the bug: connection made here, used over there."""
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(Path(tmp) / "events.db")
        session = log.start_session("whatsapp")  # * main thread

        errors: list[Exception] = []

        def worker() -> None:
            try:
                log.log(session, "consent_granted")
            except Exception as e:  # noqa: BLE001 — the test is what it raised
                errors.append(e)

        t = threading.Thread(target=worker)
        t.start()
        t.join()

        assert not errors, f"logging from a worker thread raised {errors[0]!r}"
        rows = log.query("SELECT event_type FROM events WHERE session_id = ?", (session.id,))
        assert "consent_granted" in [r["event_type"] for r in rows], "row never landed"


def test_concurrent_writers_all_land() -> None:
    """A lock that serialises is only useful if nothing is dropped."""
    with tempfile.TemporaryDirectory() as tmp:
        log = EventLog(Path(tmp) / "events.db")
        sessions = [log.start_session("whatsapp") for _ in range(8)]
        errors: list[Exception] = []

        def worker(session) -> None:
            try:
                for _ in range(10):
                    log.log(session, "consent_granted")
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(s,)) for s in sessions]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"concurrent logging raised {errors[0]!r}"
        rows = log.query("SELECT COUNT(*) AS n FROM events WHERE event_type = 'consent_granted'")
        assert rows[0]["n"] == 80, f"expected 80 rows, got {rows[0]['n']}"


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_event_log_threads.py OK")


if __name__ == "__main__":
    run()
