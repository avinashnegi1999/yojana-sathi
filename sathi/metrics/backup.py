"""Nightly copy of the event database, and a restore check that actually opens it.

Run on the server (deploy/sathi-backup.timer does, once a night):
    python3 -m sathi.metrics.backup --db /var/lib/sathi/sathi.db --out /var/lib/sathi/backups
Check a copy can be restored (on the server, or on a laptop after
deploy/pull-backups.sh brought it off the server):
    python3 -m sathi.metrics.backup --check path/to/sathi-2026-10-01.db

# ! Council audit, 1 Oct 2026: the live database is the impact evidence, a
# ! quarter of the score, and there was no copy of it anywhere. A disk failure
# ! or a bad deploy would have erased five weeks of real usage that cannot be
# ! re-run. This module only READS the live database, through SQLite's own
# ! backup API, which copies a consistent snapshot while the bots keep writing.
#
# ! A backup holds what the database holds: coarse bands under random session
# ! ids, and keyed hashes. No names, phones or Aadhaar exist to copy. Still,
# ! files are written owner-only, and old ones are deleted after KEEP nights.
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# * Two weeks of nightly copies. Enough to step back past a bad deploy noticed
# * days later; short enough that a deleted row does not live on for months.
KEEP = 14
PREFIX = "sathi-"
TABLES = ("events", "feedback", "followups", "reach", "meta")


class BackupError(Exception):
    """A copy that cannot be trusted. Never caught to carry on regardless."""


def backup(db_path: Path | str, out_dir: Path | str, keep: int = KEEP,
           today: str = "") -> Path:
    """Copy the database to out_dir/sathi-YYYY-MM-DD.db, check it, prune old copies."""
    db_path, out_dir = Path(db_path), Path(out_dir)
    if not db_path.exists():
        raise BackupError(f"no database at {db_path}")
    out_dir.mkdir(parents=True, exist_ok=True)
    os.chmod(out_dir, 0o700)
    today = today or datetime.now(timezone.utc).date().isoformat()
    target = out_dir / f"{PREFIX}{today}.db"
    partial = target.with_suffix(".db.partial")

    # ! Read-only on the live file. The backup API takes a consistent snapshot
    # ! even while the bots are writing; a plain file copy would not.
    source = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
    dest = sqlite3.connect(partial)
    try:
        source.backup(dest)
    finally:
        dest.close()
        source.close()
    os.chmod(partial, 0o600)

    # ! A copy is only a backup once it has been opened and checked.
    check_restore(partial)
    partial.replace(target)

    copies = sorted(out_dir.glob(f"{PREFIX}????-??-??.db"))
    for old in copies[:-keep] if keep > 0 else []:
        old.unlink()
    return target


def check_restore(path: Path | str) -> dict[str, int]:
    """Open a copy as if restoring it: integrity check, then count every table.

    # * Returns rows per table. Raises BackupError if the file is not a sound
    # * SQLite database with the event log's tables in it.
    """
    path = Path(path)
    if not path.exists():
        raise BackupError(f"no backup at {path}")
    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise BackupError(f"{path.name}: integrity check says {result!r}")
        present = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        missing = [t for t in TABLES if t not in present]
        if missing:
            raise BackupError(f"{path.name}: missing table(s) {missing}")
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}
    except sqlite3.DatabaseError as e:
        raise BackupError(f"{path.name}: not a readable database ({e})") from e
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Back up the event database, or check a backup")
    ap.add_argument("--db", default="/var/lib/sathi/sathi.db")
    ap.add_argument("--out", default="/var/lib/sathi/backups")
    ap.add_argument("--check", default="", help="check this backup file instead of making one")
    args = ap.parse_args(argv)
    try:
        if args.check:
            counts = check_restore(args.check)
            print(f"restore check OK: {args.check} — " +
                  ", ".join(f"{t} {n}" for t, n in counts.items()))
            return 0
        target = backup(args.db, args.out)
        print(f"backup OK: {target} — " +
              ", ".join(f"{t} {n}" for t, n in check_restore(target).items()))
        return 0
    except BackupError as e:
        # ! Non-zero so the systemd unit is marked failed and shows in
        # ! `systemctl --failed`. A silent failed backup is worse than none.
        print(f"BACKUP FAILED: {e}", file=sys.stderr)
        return 1


def _self_check() -> None:
    import tempfile

    from sathi.metrics.events import EventLog

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        live = Path(d) / "sathi.db"
        log = EventLog(live)
        session = log.start_session("web")
        log.log(session, "consent_granted")
        log.close()
        out = Path(d) / "backups"

        first = backup(live, out, today="2026-10-01")
        counts = check_restore(first)
        assert counts["events"] >= 1, counts
        assert first.name == "sathi-2026-10-01.db"
        if os.name == "posix":
            assert (first.stat().st_mode & 0o777) == 0o600, "a backup must be owner-only"

        # * Old copies beyond KEEP are deleted; the newest stay.
        for day in range(2, 6):
            backup(live, out, keep=3, today=f"2026-10-0{day}")
        names = sorted(p.name for p in out.glob("sathi-*.db"))
        assert names == ["sathi-2026-10-03.db", "sathi-2026-10-04.db", "sathi-2026-10-05.db"], names

        # ! A damaged copy is refused, not reported as fine.
        broken = out / "sathi-2026-10-06.db"
        broken.write_bytes(b"not a database at all")
        try:
            check_restore(broken)
        except BackupError:
            pass
        else:
            raise AssertionError("a broken backup passed the restore check")

        # * The live file is only ever read.
        try:
            backup(Path(d) / "missing.db", out)
        except BackupError:
            pass
        else:
            raise AssertionError("a missing database produced a backup")
    print("backup.py OK")


if __name__ == "__main__":
    raise SystemExit(main())
