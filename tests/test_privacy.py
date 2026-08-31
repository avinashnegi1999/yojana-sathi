"""Privacy checks. Run: python3 tests/test_privacy.py

# ! This file is why the privacy claim in the README is defensible rather than
# ! aspirational. It builds a Profile with every field populated, drives a whole
# ! session through the event log, and then asserts that only the four coarse
# ! dimensions survived — column by column, value by value.
#
# ! If someone adds a field to Profile and quietly plumbs it into events.py,
# ! this file fails. That is its entire job.
"""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.core.profile import AGE_BANDS, INCOME_BANDS, Profile
from sathi.core.content import occupation_codes, states
from sathi.metrics.events import (
    COARSE_FIELDS,
    EVENT_TYPES,
    ConsentError,
    EventLog,
    PrivacyError,
    coarse_dims,
)

EXPECTED_COLUMNS = {
    "event_id", "session_id", "ts", "event_type", "scheme_code",
    "state", "age_band", "occupation", "income_band", "value_inr", "channel",
}

# ! Names a well-meaning patch might add. None of them may ever be a column.
FORBIDDEN_COLUMNS = {
    "name", "full_name", "phone", "phone_number", "mobile", "aadhaar", "aadhar",
    "uid", "district", "village", "pincode", "address", "age", "income",
    "family_size", "land_holding_band", "has_bank_account", "known_schemes",
    "telegram_id", "chat_id", "user_id",
}

FULL_PROFILE = Profile(
    state="UK",
    age=37,
    occupation="construction",
    income_band="5001_10000",
    land_holding_band="above_2_hectare",
    family_size=7,
    has_bank_account=True,
    is_income_tax_payer=False,
    known_schemes=frozenset({"PMSBY"}),
)

# * Values that exist in the Profile and must NOT reach any column.
# * The worker's declared known_schemes set is deliberately absent from this
# * list: a scheme CODE is legitimate in scheme_code. What must not survive is
# * the worker's own declared list, which is asserted through coarse_dims below.
RAW_VALUES = {"37", 37, "above_2_hectare", "7", 7, "True", "false"}


def _run_a_full_session(db: Path) -> EventLog:
    log = EventLog(db)
    session = log.start_session("telegram")
    log.grant_consent(session)
    # * Every event type a session can emit, so no path escapes the audit.
    for event_type in sorted(EVENT_TYPES - {"consent_declined", "followup_sent",
                                            "followup_response", "session_start",
                                            "consent_granted"}):
        log.log(session, event_type, profile=FULL_PROFILE,
                scheme_code="PMSBY" if "scheme" in event_type else None,
                value_inr=12000 if event_type == "scheme_newly_surfaced" else None)
    return log


def test_schema_has_only_coarse_columns():
    with tempfile.TemporaryDirectory() as d:
        log = EventLog(Path(d) / "t.db")
        cols = {r[1] for r in log.query("PRAGMA table_info(events)")}
        assert cols == EXPECTED_COLUMNS, cols
        assert not (cols & FORBIDDEN_COLUMNS), cols & FORBIDDEN_COLUMNS
        log.close()


def test_no_raw_profile_value_reaches_any_column():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        log = _run_a_full_session(db)
        rows = log.query("SELECT * FROM events")
        assert rows, "no events written — the audit would be vacuous"
        band_labels = {label for label, _, _ in AGE_BANDS} | {"under-18"}
        state_codes = {s.code for s in states()}
        for row in rows:
            for column in EXPECTED_COLUMNS:
                assert row[column] not in RAW_VALUES, f"{column} leaked {row[column]!r}"
            # * NULL is fine — session_start and consent_granted carry no
            # * profile at all. What matters is that a populated cell is coarse.
            assert row["age_band"] in band_labels | {None}, row["age_band"]
            assert row["age_band"] in ("26-40", None), "37 must be coarsened, never stored"
            assert row["state"] in state_codes | {None}
            assert row["occupation"] in occupation_codes() | {None}
            assert row["income_band"] in set(INCOME_BANDS) | {None}
        log.close()


def test_coarse_dims_is_the_only_bridge_and_drops_everything_else():
    dims = coarse_dims(FULL_PROFILE)
    assert set(dims) == set(COARSE_FIELDS)
    assert dims["age_band"] == "26-40" and "age" not in dims
    for dropped in ("land_holding_band", "family_size", "has_bank_account",
                    "is_income_tax_payer", "known_schemes"):
        assert dropped not in dims, dropped


def test_explicit_dims_cannot_smuggle_a_field_in():
    with tempfile.TemporaryDirectory() as d:
        log = EventLog(Path(d) / "t.db")
        session = log.start_session("cli")
        log.grant_consent(session)
        for bad in ({"family_size": "7"}, {"phone": "9999999999"}, {"age": "37"}):
            try:
                log.log(session, "guidance_shown", dims=bad)
            except PrivacyError:
                continue
            raise AssertionError(f"{bad} was accepted into the event log")
        # * And a non-string band is refused too, so an exact number cannot slip
        # * into a dimension column by type.
        try:
            log.log(session, "guidance_shown", dims={"age_band": 37})
        except PrivacyError:
            pass
        else:
            raise AssertionError("a numeric dimension was accepted")
        log.close()


def test_no_consent_means_no_events():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        log = EventLog(db)
        session = log.start_session("telegram")
        for event_type in ("profile_field_captured", "eligibility_evaluated",
                           "scheme_matched", "pack_generated"):
            try:
                log.log(session, event_type, profile=FULL_PROFILE)
            except ConsentError:
                continue
            raise AssertionError(f"{event_type} was written before consent")
        # * Declining leaves exactly the two events that describe the decline.
        log.decline_consent(session)
        # * Sorted: SQLite is free to answer this from the event_type index, so
        # * insertion order is not guaranteed and is not what we are asserting.
        kinds = sorted(r["event_type"] for r in log.query("SELECT event_type FROM events"))
        assert kinds == ["consent_declined", "session_start"], kinds
        log.close()


def test_sessions_are_not_linkable_to_a_channel_id():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "t.db"
        log = EventLog(db)
        channel_key = "telegram-chat-987654321"
        ids = []
        for _ in range(3):
            # ! The channel id is never passed to the event log at all. Even the
            # ! same worker returning three times produces three unrelated ids.
            session = log.start_session("telegram")
            log.grant_consent(session)
            log.log(session, "eligibility_evaluated", profile=FULL_PROFILE)
            ids.append(session.id)
        assert len(set(ids)) == 3

        dump = "\n".join(
            "|".join(str(v) for v in row)
            for row in log.query("SELECT * FROM events")
        )
        assert channel_key not in dump
        assert "987654321" not in dump
        log.close()


def test_followups_are_off_by_default_and_never_joinable():
    import os

    saved = os.environ.pop("FOLLOWUP_SALT", None)
    try:
        with tempfile.TemporaryDirectory() as d:
            log = EventLog(Path(d) / "t.db")
            assert log.schedule_followup("987654321", "telegram") is None, \
                "follow-ups must be off unless a salt is deliberately configured"

            os.environ["FOLLOWUP_SALT"] = "test-salt"
            digest = log.schedule_followup("987654321", "telegram")
            assert digest and "987654321" not in digest
            cols = {r[1] for r in log.query("PRAGMA table_info(followups)")}
            # ! No session_id column: the follow-up table cannot be joined back
            # ! to the event log, by construction rather than by policy.
            assert "session_id" not in cols and not (cols & FORBIDDEN_COLUMNS), cols
            assert log.purge_followups(max_age_days=0) == 1
            log.close()
    finally:
        os.environ.pop("FOLLOWUP_SALT", None)
        if saved is not None:
            os.environ["FOLLOWUP_SALT"] = saved


def test_event_log_is_append_only_in_the_codebase():
    # ! One DELETE exists, on followups, and it is the purge. There must be no
    # ! UPDATE or DELETE anywhere against `events`.
    source = (ROOT / "sathi").rglob("*.py")
    for path in source:
        text = path.read_text(encoding="utf-8").lower()
        for stmt in ("update events", "delete from events", "drop table events"):
            assert stmt not in text, f"{path.name} mutates the event log: {stmt}"


def test_the_pack_carries_no_personal_detail():
    from sathi.core.schemes import Criterion, Scheme
    from sathi.pack import pack
    from sathi.rules.engine import evaluate_all

    sc = Scheme(
        code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
        verified_on="2026-09-01", verified_by="a",
        benefit={"annual_value_inr": 12000, "value_basis": "annual_payout", "summary_hi": "प"},
        criteria=(Criterion("age", "between", [18, 40], "u", pass_hi="ok", fail_hi="no"),),
        exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
    )
    results = evaluate_all(FULL_PROFILE, {"A": sc})
    _, blob = pack.build(results, {"A": sc}, known=frozenset())
    text = blob.decode("utf-8")
    # * The worker's age, family size and land holding are in memory during the
    # * session and must not reach the sheet they carry to a public office.
    for leak in ("37", "above_2_hectare", "UK"):
        assert leak not in text, f"pack leaked {leak}"


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_privacy.py OK")


if __name__ == "__main__":
    run()
