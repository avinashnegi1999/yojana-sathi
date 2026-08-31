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
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sathi.core.profile import Profile

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
        self._conn = sqlite3.connect(self.db_path)
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

        for k, v in row.items():
            if v is not None and not isinstance(v, str):
                raise PrivacyError(f"dimension {k} must be a string band, got {v!r}")
        if value_inr is not None and not isinstance(value_inr, int):
            raise PrivacyError(f"value_inr must be an integer ₹, got {value_inr!r}")

        event_id = str(uuid.uuid4())
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
        cur = self._conn.execute(
            "DELETE FROM followups WHERE response IS NOT NULL OR created_ts < ?", (cutoff,)
        )
        self._conn.commit()
        return cur.rowcount

    # * ----------------------------------------------------------------- read

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
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
