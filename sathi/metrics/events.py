"""The only writer to the event database.

# ! Nothing else in this project opens the DB for writing. One writer means one
# ! place to audit for a privacy leak, and tests/test_privacy.py audits exactly
# ! this file.
#
# ! Two invariants enforced in code, not in a comment:
# !   1. No profile event can be written before consent_granted for that session.
# !   2. Only the four coarse dimensions ever reach a column. Anything else
# !      raises PrivacyError — loudly, at the call site, in tests.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sathi.core import content
from sathi.core.profile import AGE_BANDS, INCOME_BANDS, Profile

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

EVENT_TYPES = frozenset(
    {
        "session_start",
        "consent_granted",
        "consent_declined",
        "profile_field_captured",
        "occupation_clarified",
        "known_schemes_declared",
        "eligibility_evaluated",
        "scheme_matched",
        "scheme_newly_surfaced",
        "scheme_unknown",
        "no_match",
        "docs_missing",
        "pack_generated",
        "guidance_shown",
        "session_complete",
        "followup_sent",
        "followup_response",
    }
)

# * Events allowed before consent. Everything else is refused.
_PRE_CONSENT = frozenset({"session_start", "consent_granted", "consent_declined"})

# ! The complete list of profile-derived columns. Adding to it is a privacy
# ! decision, not a refactor — test_privacy.py pins this exact set.
COARSE_FIELDS = ("state", "age_band", "occupation", "income_band")


class ConsentError(Exception):
    """A profile event was attempted before the worker agreed. Never caught."""


class PrivacyError(Exception):
    """Something that is not a coarse dimension tried to reach a column."""


def coarse_dims(profile: Profile) -> dict[str, str | None]:
    """The ONLY bridge from a Profile to the event log.

    # ! Exact age, family size, land holding, bank status and known_schemes are
    # ! deliberately dropped here. age becomes a band; the rest do not travel.
    """
    return {
        "state": profile.state,
        "age_band": profile.age_band(),
        "occupation": profile.occupation,
        "income_band": profile.income_band,
    }


@dataclass(frozen=True)
class Session:
    """A screening session. `id` is random and unlinkable to any channel id."""

    id: str
    channel: str


class EventLog:
    def __init__(self, db_path: str | Path | None = None) -> None:
        self.db_path = str(db_path or os.environ.get("DB_PATH", "./sathi.db"))
        # ! On a deployed container this must point at a persistent volume. An
        # ! ephemeral disk means every impact number is lost on the next restart.
        # ! check_same_thread=False because the WhatsApp adapter answers the
        # ! webhook on one thread and drains the work queue on another, and both
        # ! log. The lock below is what makes that safe: sqlite3 will hand the
        # ! connection to any thread, but an execute and its commit must not
        # ! interleave with another thread's.
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        self._conn.commit()
        self._consented: set[str] = set()

    # * ---------------------------------------------------------------- write

    def start_session(self, channel: str = "cli") -> Session:
        """Open a session. The id is uuid4 — NOT a hash of the Telegram user id.

        A hash of a stable id is still a stable id: two visits by the same
        worker would become linkable, and the privacy claim would be false.
        """
        session = Session(id=str(uuid.uuid4()), channel=channel)
        self.log(session, "session_start")
        return session

    def grant_consent(self, session: Session) -> None:
        self._consented.add(session.id)
        self.log(session, "consent_granted")

    def decline_consent(self, session: Session) -> None:
        self.log(session, "consent_declined")

    def log(
        self,
        session: Session,
        event_type: str,
        *,
        profile: Profile | None = None,
        scheme_code: str | None = None,
        value_inr: int | None = None,
        dims: dict | None = None,
    ) -> str:
        if event_type not in EVENT_TYPES:
            raise ValueError(f"unknown event_type {event_type!r}")
        if event_type not in _PRE_CONSENT and session.id not in self._consented:
            raise ConsentError(
                f"{event_type!r} attempted before consent_granted — "
                f"no consent, no events. This is the code path enforcing it."
            )
        if session.id not in self._consented and (profile is not None or dims):
            raise ConsentError("profile dimensions require consent, including on session events")

        row = {k: None for k in COARSE_FIELDS}
        if profile is not None:
            row.update(coarse_dims(profile))
        if dims:
            # ! An explicit dims dict is the one place a caller could smuggle a
            # ! raw value in. Whitelist, then refuse anything else.
            unknown = set(dims) - set(COARSE_FIELDS)
            if unknown:
                raise PrivacyError(
                    f"{sorted(unknown)} is not a coarse dimension. "
                    f"Allowed: {list(COARSE_FIELDS)}"
                )
            row.update(dims)

        allowed = {
            "state": {st.code for st in content.states()},
            "age_band": {label for label, _, _ in AGE_BANDS} | {"under-18"},
            "occupation": content.occupation_codes(),
            "income_band": INCOME_BANDS,
        }
        for k, v in row.items():
            # ! A whitelisted column is not enough: arbitrary text in `state`
            # ! used to retain anything a worker sent after the `state:` prefix.
            if v is not None and (not isinstance(v, str) or v not in allowed[k]):
                raise PrivacyError(f"dimension {k} must be a recognised coarse band")
        if value_inr is not None and not isinstance(value_inr, int):
            raise PrivacyError(f"value_inr must be an integer ₹, got {value_inr!r}")

        event_id = str(uuid.uuid4())
        with self._lock:
            self._conn.execute(
            "INSERT INTO events (event_id, session_id, ts, event_type, scheme_code,"
            " state, age_band, occupation, income_band, value_inr, channel)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                event_id,
                session.id,
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                event_type,
                scheme_code,
                row["state"],
                row["age_band"],
                row["occupation"],
                row["income_band"],
                value_inr,
                    session.channel,
                ),
            )
            self._conn.commit()
        return event_id

    def log_results(self, session: Session, profile: Profile, results, known: frozenset[str]) -> None:
        """Record one full evaluation. Called once per screening, from the flow.

        # ! `scheme_newly_surfaced` is the headline metric and it exists only
        # ! because intake asks "which of these do you already have?". Drop that
        # ! question and this event can never be emitted.
        """
        from sathi.rules.engine import Verdict  # local: keeps engine free of metrics

        self.log(session, "eligibility_evaluated", profile=profile)
        matched = 0
        for r in results:
            if r.verdict is Verdict.ELIGIBLE:
                matched += 1
                self.log(session, "scheme_matched", profile=profile, scheme_code=r.scheme_code)
                if r.scheme_code not in known:
                    self.log(
                        session,
                        "scheme_newly_surfaced",
                        profile=profile,
                        scheme_code=r.scheme_code,
                        value_inr=r.annual_value_inr,
                    )
            elif r.verdict is Verdict.UNKNOWN:
                self.log(session, "scheme_unknown", profile=profile, scheme_code=r.scheme_code)
        if matched == 0:
            self.log(session, "no_match", profile=profile)

    # * ------------------------------------------------------------ follow-up

    # ! Kept deliberately narrow: four categories, chosen from buttons, never
    # ! free text. "Who is this for?" is the difference between "214 people used
    # ! it" and "96 used it for themselves or someone they were helping, and 118
    # ! were testing the software" - which is the honest sentence when a link
    # ! has been posted somewhere developers read.
    PURPOSES = frozenset({"self", "family", "helping", "testing"})

    def _reach_key(self) -> bytes:
        """The hashing key, generated once and kept only in this database."""
        row = self._conn.execute(
            "SELECT value FROM meta WHERE key = 'reach_key'").fetchone()
        if row is None:
            key = secrets.token_hex(32)
            self._conn.execute(
                "INSERT OR IGNORE INTO meta (key, value) VALUES ('reach_key', ?)", (key,))
            self._conn.commit()
            row = self._conn.execute(
                "SELECT value FROM meta WHERE key = 'reach_key'").fetchone()
        return str(row[0]).encode("utf-8")

    def record_reach(self, channel_id: str, channel: str,
                     source: str = "", purpose: str = "") -> bool:
        """Count one person once. Returns True the first time only.

        # ! INSERT OR IGNORE against a hashed primary key, never a counter that
        # ! is read and incremented - a number you increment drifts, and there
        # ! is no way afterwards to tell a drifted count from a real one.
        # ! Someone pressing /start fifty times stays one person.
        """
        anon = hmac.new(self._reach_key(), channel_id.encode("utf-8"),
                        hashlib.sha256).hexdigest()
        if purpose and purpose not in self.PURPOSES:
            raise ValueError(f"unknown purpose {purpose!r}")
        # * Day precision. An exact timestamp beside a stable id is a pattern
        # * of life; the date is all any dashboard here needs.
        day = datetime.now(timezone.utc).date().isoformat()
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO reach (anon_id, channel, source, purpose, first_seen)"
            " VALUES (?, ?, ?, ?, ?)",
            (anon, channel, source or None, purpose or None, day))
        self._conn.commit()
        return cur.rowcount == 1

    def set_purpose(self, channel_id: str, purpose: str) -> None:
        """Record what someone said they were using it for, if they said."""
        if purpose not in self.PURPOSES:
            raise ValueError(f"unknown purpose {purpose!r}")
        anon = hmac.new(self._reach_key(), channel_id.encode("utf-8"),
                        hashlib.sha256).hexdigest()
        self._conn.execute("UPDATE reach SET purpose = ? WHERE anon_id = ?",
                           (purpose, anon))
        self._conn.commit()

    def reach_counts(self) -> dict:
        """Unique people, and where they came from. Never per-person rows."""
        q = self._conn.execute
        total = q("SELECT COUNT(*) FROM reach").fetchone()[0]
        by_source = q("SELECT COALESCE(source, 'direct'), COUNT(*) FROM reach"
                      " GROUP BY 1 ORDER BY 2 DESC").fetchall()
        by_purpose = q("SELECT COALESCE(purpose, 'not asked'), COUNT(*) FROM reach"
                       " GROUP BY 1 ORDER BY 2 DESC").fetchall()
        return {"unique_people": total,
                "by_source": [(str(a), int(b)) for a, b in by_source],
                "by_purpose": [(str(a), int(b)) for a, b in by_purpose]}

    def schedule_followup(self, channel_id: str, channel: str, days: int = 14) -> str | None:
        """Opt-in. Returns None unless FOLLOWUP_SALT is set.

        ? Whether this is worth holding a channel id at all is a judgement
        ? Unset salt = feature off, which is the default.
        """
        salt = os.environ.get("FOLLOWUP_SALT", "")
        if not salt:
            return None
        digest = hashlib.sha256(f"{salt}:{channel}:{channel_id}".encode()).hexdigest()
        now = datetime.now(timezone.utc)
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO followups (id, channel, due_ts, created_ts)"
                " VALUES (?,?,?,?)",
                (
                    digest,
                    channel,
                    (now + timedelta(days=days)).isoformat(timespec="seconds"),
                    now.isoformat(timespec="seconds"),
                ),
            )
            self._conn.commit()
        return digest

    def purge_followups(self, max_age_days: int = 30) -> int:
        """Delete answered or stale rows. The only DELETE in the project."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        with self._lock:
            cur = self._conn.execute(
                "DELETE FROM followups WHERE response IS NOT NULL OR created_ts < ?", (cutoff,)
            )
            self._conn.commit()
        return cur.rowcount

    # * ----------------------------------------------------------------- read

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._conn.execute(sql, params))

    def close(self) -> None:
        self._conn.close()


def _self_check() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        log = EventLog(Path(d) / "t.db")
        s = log.start_session("cli")
        p = Profile(state="UK", age=34, occupation="construction", income_band="upto_5000")

        try:
            log.log(s, "profile_field_captured", profile=p)
        except ConsentError:
            pass
        else:
            raise AssertionError("profile event before consent must be refused")

        log.grant_consent(s)
        log.log(s, "profile_field_captured", profile=p)
        rows = log.query("SELECT * FROM events WHERE event_type='profile_field_captured'")
        assert rows[0]["age_band"] == "26-40", "exact age must never be stored"
        assert rows[0]["state"] == "UK"

        try:
            log.log(s, "guidance_shown", dims={"family_size": "4"})
        except PrivacyError:
            pass
        else:
            raise AssertionError("non-coarse dimension must be refused")

        # * A restart must find the same rows — the whole impact claim rests on it.
        log.close()
        again = EventLog(Path(d) / "t.db")
        assert len(again.query("SELECT * FROM events")) == 3
        again.close()
    print("events.py OK")


if __name__ == "__main__":
    _self_check()
