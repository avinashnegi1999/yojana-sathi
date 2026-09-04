"""End-to-end session checks. Run: python3 tests/test_flow.py

# ! This is the week-6 acceptance test, automated: LLM_API_KEY unset, buttons
# ! only, consent to application pack, with the event log written and read back
# ! after a restart. If this passes, the hybrid design and the impact pipeline
# ! both hold; if it fails, the deploy gate is not met.
#
# * Scheme files here are FIXTURES with invented numbers, and they are named
# * TEST_* so nobody mistakes them for researched government rules. Real files
# * in data/schemes/ carry researched values with a source for every one.
"""

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.conversation import consent
from sathi.conversation.flow import (
    DK, LANG_EN, LANG_HI, NEXT, NO, YES, Conversation, State,
)
from sathi.core.schemes import load_all
from sathi.metrics.events import EventLog
from sathi.metrics.report import _connect, numbers, render

VERIFIED = """
code         = "TEST_A"
name_en      = "Test Scheme A"
name_hi      = "जाँच योजना A"
authority    = "Test Ministry"
official_url = "https://example.gov.in/a"
verified_on  = "2026-09-01"
verified_by  = "test-fixture"

[benefit]
annual_value_inr = 12000
value_basis      = "annual_payout"
premium_inr      = 0
summary_hi       = "हर साल ₹12,000"
summary_en       = "₹12,000 every year"

[[criteria]]
field      = "age"
op         = "between"
value      = [18, 40]
ask_hi     = "उम्र?"
pass_hi    = "आपकी उम्र इस योजना के दायरे में है"
fail_hi    = "यह योजना 18 से 40 साल वालों के लिए है"
ask_en     = "Age?"
pass_en    = "You qualify on age"
fail_en    = "This scheme is for people aged 18 to 40"
source_url = "https://example.gov.in/a#age"

[[exclusions]]
field      = "is_income_tax_payer"
op         = "eq"
value      = true
reason_hi  = "आयकर भरने वालों को यह योजना नहीं मिलती"
reason_en  = "Income tax payers do not get this scheme"
source_url = "https://example.gov.in/a#tax"

[paperwork]
documents      = ["आधार", "बैंक पासबुक"]
documents_en   = ["Aadhaar", "Bank passbook"]
where_to_apply = "csc"
renewal        = "none"
renewal_en     = "none"
"""

STUBBED = """
code         = "TEST_B"
name_en      = "Test Scheme B"
name_hi      = "जाँच योजना B"
authority    = "Test Ministry"
official_url = "https://example.gov.in/b"
verified_on  = "TODO"
verified_by  = "TODO"

[benefit]
annual_value_inr = "TODO"
value_basis      = "TODO"
premium_inr      = "TODO"
summary_hi       = "TODO"
summary_en       = "TODO"

[[criteria]]
field      = "age"
op         = "between"
value      = "TODO"
ask_hi     = "TODO"
pass_hi    = "TODO"
fail_hi    = "TODO"
source_url = "TODO"

[paperwork]
documents      = ["TODO"]
where_to_apply = "TODO"
renewal        = "TODO"
"""


def _fixture_schemes(directory: Path) -> dict:
    (directory / "a.toml").write_text(VERIFIED, encoding="utf-8")
    (directory / "b.toml").write_text(STUBBED, encoding="utf-8")
    return load_all(directory)


def _answer_all(convo: Conversation, *, age="30", tax=DK, epfo=NO, nps=NO, known=(),
                lang=LANG_HI) -> list:
    """Drive intake with button values only. No typed free text anywhere."""
    convo.start()
    convo.handle(lang)
    convo.handle(consent.YES)
    convo.handle("state:UK")
    convo.handle(age)
    convo.handle("occ:construction")
    convo.handle("inc:upto_5000")
    convo.handle("land:landless")
    convo.handle("fam:4")
    convo.handle(YES)  # bank account
    convo.handle(tax)
    # ! EPFO/ESIC and NPS are separate questions: PM-SYM bars all three, e-Shram
    # ! only the first two, so one answer cannot serve both schemes.
    convo.handle(epfo)
    convo.handle(nps)
    for code in known:
        convo.handle(f"known:{code}")
    return convo.handle(NEXT)


def test_full_session_with_no_llm_key_reaches_a_pack():
    assert not os.environ.get("LLM_API_KEY"), "this suite must run with the key unset"
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        log = EventLog(directory / "t.db")
        convo = Conversation(schemes, log, channel="cli")

        out = _answer_all(convo, tax=NO)
        text = out[1].text  # * [0] is the answer recap
        assert "जाँच योजना A" in text and "12,000" in text
        assert "आपकी उम्र इस योजना के दायरे में है" in text, "authored pass reason must show"
        # * The stubbed scheme appears, honestly, as something we could not check.
        assert "जाँच योजना B" in text
        assert convo.state is State.DOCUMENTS

        convo.handle("doc:0")  # has आधार, not बैंक पासबुक
        out = convo.handle(NEXT)
        assert "बैंक पासबुक" in out[0].text, "missing document must be named"
        out = convo.handle(YES)  # yes, build the pack
        filename, blob = out[0].document
        assert filename.endswith(".html") and b"12,000" in blob
        assert out[-1].end and convo.state is State.DONE
        log.close()


def test_the_headline_metric_counts_only_unknown_to_the_worker():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)

        log = EventLog(directory / "new.db")
        _answer_all(Conversation(schemes, log), tax=NO)
        surfaced = log.query("SELECT * FROM events WHERE event_type='scheme_newly_surfaced'")
        assert len(surfaced) == 1 and surfaced[0]["value_inr"] == 12000
        log.close()

        # * Same worker, but they already hold TEST_A: matched, not newly surfaced.
        log2 = EventLog(directory / "known.db")
        _answer_all(Conversation(schemes, log2), tax=NO, known=("TEST_A",))
        assert log2.query("SELECT * FROM events WHERE event_type='scheme_matched'")
        assert not log2.query("SELECT * FROM events WHERE event_type='scheme_newly_surfaced'"), \
            "a scheme the worker already has must never inflate the headline number"
        log2.close()


def test_unverified_scheme_never_produces_a_verdict_or_rupees():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        log = EventLog(directory / "t.db")
        _answer_all(Conversation(schemes, log), tax=NO)
        unknown = log.query("SELECT * FROM events WHERE event_type='scheme_unknown'")
        assert [r["scheme_code"] for r in unknown] == ["TEST_B"]
        assert all(r["value_inr"] is None for r in unknown)
        log.close()


def test_ineligible_worker_gets_a_reason_and_never_a_dead_end():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)
        out = _answer_all(convo, age="65", tax=NO)
        text = out[1].text
        assert "यह योजना 18 से 40 साल वालों के लिए है" in text
        assert "नज़दीकी केंद्र" in text, "a no-match must still point somewhere"
        assert convo.state is State.DONE, "no eligible scheme means no paperwork step"


def test_exclusion_is_explained_in_the_workers_own_result():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)
        out = _answer_all(convo, tax=YES)  # income-tax payer
        assert "आयकर भरने वालों को यह योजना नहीं मिलती" in out[1].text


def test_dont_know_leaves_the_answer_unset_and_yields_unknown():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)
        out = _answer_all(convo, tax=DK)
        # ! "Don't know" must not be read as "no". The scheme with a tax
        # ! exclusion becomes UNKNOWN, with a question to ask at the centre.
        assert convo.profile.is_income_tax_payer is None
        assert "जाँच योजना A" in out[1].text
        assert "पक्का नहीं कह सकता" in out[1].text


def test_llm_path_and_button_path_agree():
    """The acceptance test for the hybrid design: same profile, same verdicts."""
    import sathi.render.llm as llm

    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)

        buttons_only = Conversation(schemes, None)
        expected = _answer_all(buttons_only, tax=NO)[0].text

        saved, real_ask = os.environ.get("LLM_API_KEY"), llm._ask
        os.environ["LLM_API_KEY"] = "test-not-a-real-key"
        llm._ask = lambda *a, **k: "construction"
        try:
            with_llm = Conversation(schemes, None)
            with_llm.start()
            with_llm.handle(LANG_HI)
            with_llm.handle(consent.YES)
            with_llm.handle("उत्तराखंड")          # typed, not tapped
            with_llm.handle("30")
            with_llm.handle("मैं ईंट का काम करता हूँ")  # free text → LLM proposal
            assert with_llm.state is State.OCCUPATION_CONFIRM
            with_llm.handle(YES)                  # ! confirmation, always
            with_llm.handle("inc:upto_5000")
            with_llm.handle("land:landless")
            with_llm.handle("fam:4")
            with_llm.handle(YES)
            with_llm.handle(NO)   # income tax
            with_llm.handle(NO)   # EPFO/ESIC
            with_llm.handle(NO)   # NPS
            got = with_llm.handle(NEXT)[0].text
        finally:
            llm._ask = real_ask
            os.environ.pop("LLM_API_KEY", None)
            if saved is not None:
                os.environ["LLM_API_KEY"] = saved

        assert got == expected, "the LLM changed the result — it must only change phrasing"
        assert buttons_only.profile == with_llm.profile


def test_english_gives_the_same_verdicts_with_no_devanagari():
    """Both languages, one engine. Only the words change."""
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)

        hi_convo = Conversation(schemes, None)
        _answer_all(hi_convo, tax=NO)
        en_convo = Conversation(schemes, None)
        out = _answer_all(en_convo, tax=NO, lang=LANG_EN)

        assert hi_convo.profile == en_convo.profile, "language changed a recorded answer"
        text = out[1].text
        assert "Test Scheme A" in text, text
        # ! The fixture authors pass_en/fail_en, so an English session must not
        # ! fall back to Devanagari anywhere in the result screen — recap included,
        # ! since that is assembled from the same string files.
        assert "qualify" in text.lower()
        assert not any(_devanagari(r.text) for r in out), \
            "Devanagari leaked into an English result screen"


def test_free_text_occupation_never_loops_back_to_the_same_menu():
    """A real tester typed "i dont do any job" and got the menu again, forever.

    # ! The menu's own "something else" leads to free text, so re-showing the
    # ! menu on a failed match is a loop with no exit. Free text must always end
    # ! somewhere the worker can accept or reject.
    """
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)

        for phrase in ("i dont do any job", "berojgar", "something nobody has ever typed"):
            convo = Conversation(schemes, None)
            convo.start()
            convo.handle(LANG_EN)
            convo.handle(consent.YES)
            convo.handle("state:UK")
            convo.handle("30")
            convo.handle("other")            # "something else" → free text
            out = convo.handle(phrase)
            assert convo.state is State.OCCUPATION_CONFIRM, \
                f"{phrase!r} bounced back to the menu instead of proposing a category"
            assert convo.profile.occupation is None, "a proposal must not be recorded yet"
            convo.handle(YES)
            assert convo.profile.occupation is not None
            assert convo.state is State.INCOME, "confirming must move the flow forward"


def test_not_working_is_an_answer_not_a_gap():
    # ! Someone with no work is screened like anyone else — none of the three
    # ! schemes tests occupation at all.
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)
        convo.start(); convo.handle(LANG_HI); convo.handle(consent.YES)
        convo.handle("state:UK"); convo.handle("30")
        convo.handle("occ:no_work")
        assert convo.profile.occupation == "no_work"
        convo.handle("inc:upto_5000"); convo.handle("land:landless"); convo.handle("fam:4")
        # bank, income tax, EPFO/ESIC, NPS — four questions since the split
        convo.handle(YES); convo.handle(NO); convo.handle(NO); convo.handle(NO)
        out = convo.handle(NEXT)
        assert "जाँच योजना A" in out[1].text, "being out of work must not block a match"


def _devanagari(text: str) -> bool:
    return any("\u0900" <= ch <= "\u097f" for ch in text)


def test_an_english_session_shows_no_hindi_anywhere_including_buttons():
    """The income and land BUTTONS were Hindi in an English session.

    # ! The earlier English test only read the result message, so it passed
    # ! while every band button stayed in Devanagari — caught by a screenshot,
    # ! not by the suite. This walks a whole session and checks button labels
    # ! too, which is where the bug actually was.
    """
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)

        # * The language picker is bilingual on purpose — it is the one screen
        # * that must be readable before a language has been chosen.
        convo.start()
        steps = ["consent_yes", "state:UK", "30", "occ:construction", "inc:upto_5000",
                 "land:landless", "fam:4", YES, NO, NO, NEXT, NEXT, NO]
        replies = convo.handle(LANG_EN)
        for step in steps:
            for r in replies:
                assert not _devanagari(r.text), f"Hindi text in an English session: {r.text[:80]}"
                for b in r.buttons:
                    assert not _devanagari(b.label), f"Hindi button in an English session: {b.label}"
            replies = convo.handle(step)


def test_a_worker_with_no_income_is_still_screened():
    # ! Zero income must not read as "missing answer" or fall outside a band.
    # ! The fixture caps at 40 years and has no income rule, so this checks the
    # ! band travels through intake intact; PM-SYM's own list is checked in
    # ! tests/test_schemes.py.
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        convo = Conversation(schemes, None)
        convo.start(); convo.handle(LANG_EN); convo.handle(consent.YES)
        convo.handle("state:UK"); convo.handle("30"); convo.handle("occ:no_work")
        convo.handle("inc:no_income")
        assert convo.profile.income_band == "no_income"
        convo.handle("land:landless"); convo.handle("fam:4")
        # bank, income tax, EPFO/ESIC, NPS — four questions since the split
        convo.handle(YES); convo.handle(NO); convo.handle(NO); convo.handle(NO)
        out = convo.handle(NEXT)
        assert "Test Scheme A" in out[1].text


def test_declining_consent_stores_nothing():
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        log = EventLog(directory / "t.db")
        convo = Conversation(schemes, log)
        convo.start()
        convo.handle(LANG_HI)
        out = convo.handle(consent.NO)
        assert out[0].end
        kinds = sorted(r["event_type"] for r in log.query("SELECT event_type FROM events"))
        assert kinds == ["consent_declined", "session_start"], kinds
        log.close()


def test_events_survive_a_restart_and_the_dashboard_renders():
    # ! Deploy-gate check 5. If the DB does not survive a restart, every impact
    # ! number is fiction — so it is asserted here, not left to deploy day.
    with tempfile.TemporaryDirectory() as d:
        directory = Path(d)
        schemes = _fixture_schemes(directory)
        db = directory / "t.db"

        log = EventLog(db)
        for _ in range(6):  # 6 workers, so k-anonymity does not suppress them
            _answer_all(Conversation(schemes, log), tax=NO)
        before = len(log.query("SELECT * FROM events"))
        log.close()

        reopened = EventLog(db)
        assert len(reopened.query("SELECT * FROM events")) == before
        reopened.close()

        conn = _connect(str(db))
        n = numbers(conn)
        assert n["screened"] == 6 and n["surfaced"] == 6 and n["value_inr"] == 72000
        page = render(conn, schemes_dir=directory)
        assert "₹72,000" in page and "not money received" in page
        assert "never verified" in page, "the stubbed fixture must show as unverified"
        conn.close()


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_flow.py OK")


if __name__ == "__main__":
    run()
