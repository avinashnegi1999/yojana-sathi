"""Source-review regressions: uncertainty must not become eligibility or refusal.

# * Real scheme signatures are simulated only inside this test. No production
# * data is approved by these assertions. Run: python tests/test_review_conditions.py
"""
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.conversation.flow import Conversation, State, YES, NO, DK, OTHER
from sathi.core.profile import Profile
from sathi.core.schemes import load_all, load_scheme, SchemeError
from sathi.rules.engine import evaluate, Verdict
from sathi.rules.operators import apply, OperatorError


def test_worker_status_is_independent_of_income_and_job_title():
    schemes = {code: replace(sc, verified_by="test-review-only")
               for code, sc in load_all(ROOT / "data/schemes").items()}
    base = Profile(age=30, occupation="no_work", income_band="no_income",
                   has_bank_account=True, is_income_tax_payer=False,
                   is_epfo_or_esic_member=False, nps_exclusion_applies=False)
    for code in ("PM_SYM", "ESHRAM"):
        assert evaluate(base, schemes[code]).verdict is Verdict.UNKNOWN
        assert evaluate(replace(base, is_unorganised_worker=False), schemes[code]).verdict is Verdict.INELIGIBLE
        assert evaluate(replace(base, occupation="construction", is_unorganised_worker=True), schemes[code]).verdict is Verdict.ELIGIBLE
    # Insurance has no employment condition.
    assert evaluate(base, schemes["PMSBY"]).verdict is Verdict.ELIGIBLE


def test_nps_and_worker_answers_survive_language_switches():
    schemes = load_all(ROOT / "data/schemes")
    for lang in ("hi", "en"):
        for answer, expected in ((NO, False), (YES, True), (OTHER, None), (DK, None)):
            c = Conversation(schemes)
            c.lang = lang
            c.state = State.NPS
            assert c._current_question().button_values() == {YES, NO, OTHER, DK}
            c.handle("unexpected")
            assert c.state is State.NPS
            c.handle(answer)
            assert c.profile.nps_exclusion_applies is expected
            assert c.state is State.WORKER
            c.set_language("en" if lang == "hi" else "hi")
            assert c.state is State.WORKER
            assert c._current_question().button_values() == {YES, NO, DK}
            c.handle("unexpected")
            assert c.profile.is_unorganised_worker is None
            c.handle(DK)
            assert c.state is State.FOLLOWUP
            while c.state is State.FOLLOWUP:
                c.handle(DK)
            assert c.state is State.KNOWN_SCHEMES
            assert c.profile.is_unorganised_worker is None
            assert c.profile.nps_exclusion_applies is expected
            c.cancel()
            assert c.profile == Profile()


def test_other_nps_does_not_cause_a_definite_refusal():
    schemes = load_all(ROOT / "data/schemes")
    c = Conversation(schemes)
    c.profile = Profile(age=30, income_band="upto_5000", has_bank_account=True,
                        is_income_tax_payer=False, is_epfo_or_esic_member=False)
    c.state = State.NPS
    c.handle(OTHER)
    c.handle(YES)
    signed = replace(schemes["PM_SYM"], verified_by="test-review-only")
    assert evaluate(c.profile, signed).verdict is Verdict.UNKNOWN
    # The production human-verification gate is retained for every answer.
    for sc in schemes.values():
        assert evaluate(c.profile, sc).verdict is Verdict.UNKNOWN


def test_nearest_birthday_uses_only_known_age_precision():
    for age, expected in ((None, None), (68, True), (69, None), (70, False), (71, False)):
        assert apply("before_nearest_birthday", age, 70) is expected
    assert apply("before_nearest_birthday", 30, "TODO") is None
    for actual, cutoff in ((True, 70), (69.5, 70), (-1, 70), (30, 0), (30, True)):
        try:
            apply("before_nearest_birthday", actual, cutoff)
        except OperatorError:
            pass
        else:
            raise AssertionError((actual, cutoff))
    import tempfile
    source = (ROOT / "data/schemes/pmsby.toml").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "invalid.toml"
        for bad in ('true', '0', '70.5'):
            path.write_text(source.replace('value      = 70', f'value      = {bad}', 1), encoding="utf-8")
            try:
                load_scheme(path)
            except SchemeError:
                pass
            else:
                raise AssertionError(f"invalid cutoff loaded: {bad}")


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_review_conditions.py OK")
