"""Trust-boundary regressions, run by check.py; no live services or worker data.

# * Exercises real intake and event writes, not a second implementation.
# ! Synthetic malformed input must never become a retained profile dimension.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sathi.conversation.flow import Conversation, State
from sathi.core.profile import Profile
from sathi.metrics.events import ConsentError, EventLog, PrivacyError


def test_prefixed_state_is_validated_before_logging():
    log = EventLog(":memory:")
    try:
        c = Conversation({}, log)
        c.handle("lang:en")
        c.handle("consent_yes")
        c.handle("state:private-free-text")
        assert c.state is State.STATE and c.profile.state is None
        assert not log.query("SELECT 1 FROM events WHERE state IS NOT NULL")
        c.handle("state:UK")
        assert c.state is State.AGE and c.profile.state == "UK"
    finally:
        log.close()


def test_family_input_is_not_repaired_into_a_different_number():
    for raw in ("-5", "2.5", "2 people", "²", "fam:-1", "9" * 5000):
        c = Conversation({})
        c.state = State.FAMILY
        c.handle(raw)
        assert c.state is State.FAMILY and c.profile.family_size is None, raw[:20]
    for raw in ("5", "५", "fam:9"):
        c = Conversation({})
        c.state = State.FAMILY
        c.handle(raw)
        assert c.state is State.BANK


def test_oversized_age_reasks_without_raising():
    c = Conversation({})
    c.state = State.AGE
    c.handle("9" * 5000)
    assert c.state is State.AGE and c.profile.age is None


def test_negative_document_index_does_not_mark_last_document():
    c = Conversation({})
    c.state = State.DOCUMENTS
    c._required_docs = ("Document A", "Document B")
    for raw in ("doc:-1", "doc:+1", "doc:2", "doc:²"):
        c.handle(raw)
        assert not c._have_docs, raw
    c.handle("doc:1")
    assert c._have_docs == {"Document B"}


def test_coarse_column_names_do_not_allow_free_text_values():
    log = EventLog(":memory:")
    try:
        session = log.start_session()
        log.grant_consent(session)
        for field in ("state", "occupation", "income_band", "age_band"):
            try:
                log.log(session, "guidance_shown", dims={field: "private-free-text"})
            except PrivacyError as error:
                assert "private-free-text" not in str(error)
            else:
                raise AssertionError(f"{field} accepted arbitrary private text")
        try:
            log.log(session, "guidance_shown", profile=Profile(state="private-free-text"))
        except PrivacyError:
            pass
        else:
            raise AssertionError("Profile bypassed coarse-value validation")
        assert len(log.query("SELECT * FROM events")) == 2
    finally:
        log.close()


def test_preconsent_event_cannot_carry_profile_dimensions():
    log = EventLog(":memory:")
    try:
        session = log.start_session()
        try:
            log.log(session, "session_start", profile=Profile(state="UK"))
        except ConsentError:
            pass
        else:
            raise AssertionError("preconsent event retained profile information")
        assert len(log.query("SELECT * FROM events")) == 1
    finally:
        log.close()


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_input_privacy.py OK")
