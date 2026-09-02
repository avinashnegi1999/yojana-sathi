"""Are the verdicts RIGHT? Run: python3 tests/test_rule_boundaries.py

# ! Every other test asks whether the software works. This one asks whether the
# ! ANSWER is correct, which is a different question and the one that costs a
# ! worker a day's wages when we get it wrong.
#
# ! The method is an independent oracle. `_oracle()` below re-encodes each
# ! scheme's rules straight from the official source text, deliberately NOT by
# ! reading data/schemes/*.toml. The sweep then compares it against the real
# ! engine over every combination of the fields any rule touches. A mismatch is
# ! either an engine bug or a transcription slip in a scheme file — the class of
# ! fault that pressing every button can never surface, because a wrong
# ! threshold produces a perfectly well-formed screen.
#
# ! Sign-off is simulated here (the engine refuses a verdict for an unsigned
# ! scheme, which would make every row UNKNOWN and test nothing). What is faked
# ! is only the signature; every threshold under test is the shipped one.
"""

import itertools
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.core.profile import Profile
from sathi.core.schemes import load_all
from sathi.rules.engine import Verdict, evaluate

# * Boundaries, not a range: one either side of every threshold in every file,
# * plus None for "not asked yet".
AGES = [None, 15, 16, 17, 18, 19, 25, 39, 40, 41, 58, 59, 60, 61, 69, 70, 71, 99]
INCOME = [None, "no_income", "upto_5000", "5001_10000", "10001_15000",
          "15001_25000", "above_25000"]
TRI = [None, True, False]

# ! PM-SYM's ceiling is "₹15,000 a month or less", so every band at or under it.
PM_SYM_BANDS = {"no_income", "upto_5000", "5001_10000", "10001_15000"}


def _oracle(code: str, p: Profile) -> bool | None:
    """The official rules, hand-encoded. None means undecidable.

    # ! Precedence matches the engine's documented order, and that order is a
    # ! correctness claim in itself: a DEFINITE no outranks a missing answer.
    # ! Being an EPFO member rules you out of PM-SYM whatever your age is, so
    # ! the engine must not answer UNKNOWN there just because age is unset.
    """
    excluded = failed = undecided = False

    def criterion(outcome: bool | None) -> None:
        nonlocal failed, undecided
        if outcome is None:
            undecided = True
        elif not outcome:
            failed = True

    def exclusion(hit: bool | None) -> None:
        nonlocal excluded, undecided
        if hit is None:
            undecided = True
        elif hit:
            excluded = True

    age, income = p.age, p.income_band
    tax, statutory, bank = (p.is_income_tax_payer, p.is_statutory_scheme_member,
                            p.has_bank_account)

    if code == "PMSBY":
        # jansuraksha.gov.in rules PDF: "aged between 18 years (completed) and 70
        # years", "All individual bank/ Post office account holders". No income
        # bar and no tax bar anywhere in that document — deliberately none here.
        criterion(None if age is None else 18 <= age <= 70)
        criterion(bank)
    elif code == "PM_SYM":
        # maandhan.in: entry age 18-40, monthly income ₹15,000 or less, and not
        # a member of EPFO/ESIC/NPS, and not an income-tax payer.
        criterion(None if age is None else 18 <= age <= 40)
        criterion(None if income is None else income in PM_SYM_BANDS)
        exclusion(statutory)
        exclusion(tax)
    elif code == "ESHRAM":
        # eshram.gov.in FAQ: 16 and above; an unorganised worker is one who is
        # not an EPFO/ESIC member and not an income-tax payer.
        criterion(None if age is None else age >= 16)
        exclusion(tax)
        exclusion(statutory)
    else:
        raise AssertionError(f"no oracle for {code} — write one before shipping it")

    if excluded or failed:
        return False
    if undecided:
        return None
    return True


def _expected(code: str, p: Profile) -> Verdict:
    out = _oracle(code, p)
    if out is None:
        return Verdict.UNKNOWN
    return Verdict.ELIGIBLE if out else Verdict.INELIGIBLE


def _signed_schemes() -> dict:
    return {
        code: replace(sc, verified_by="test-signature (tests/test_rule_boundaries.py)")
        for code, sc in load_all(ROOT / "data" / "schemes").items()
    }


def test_every_combination_matches_the_official_rules():
    schemes = _signed_schemes()
    missing = set(schemes) - {"PMSBY", "PM_SYM", "ESHRAM"}
    assert not missing, f"a scheme was added with no oracle: {sorted(missing)}"

    checked = 0
    wrong = []
    for age, income, bank, tax, statutory in itertools.product(
        AGES, INCOME, TRI, TRI, TRI
    ):
        p = Profile(age=age, income_band=income, has_bank_account=bank,
                    is_income_tax_payer=tax, is_statutory_scheme_member=statutory)
        for code, scheme in schemes.items():
            got = evaluate(p, scheme).verdict
            want = _expected(code, p)
            checked += 1
            if got is not want:
                wrong.append(f"{code} age={age} income={income} bank={bank} "
                             f"tax={tax} statutory={statutory}: got {got.value}, "
                             f"official rules say {want.value}")
    assert not wrong, "\n  " + "\n  ".join(wrong[:20])
    # ! Coverage counter, same reason as test_all_paths: a sweep that swept
    # ! nothing passes silently.
    assert checked > 5000, f"only {checked} verdicts checked"
    print(f"  .. {checked:,} verdicts checked against the official rules")


def test_the_named_boundaries_individually():
    """The thresholds a human would check by hand, stated one per line.

    # * Redundant with the sweep on purpose: when the sweep fails, this says
    # * WHICH edge moved without needing to read a combination dump.
    """
    schemes = _signed_schemes()

    def verdict(code, **kw):
        base = dict(income_band="no_income", has_bank_account=True,
                    is_income_tax_payer=False, is_statutory_scheme_member=False)
        base.update(kw)
        return evaluate(Profile(**base), schemes[code]).verdict

    E, N = Verdict.ELIGIBLE, Verdict.INELIGIBLE

    # PMSBY: 18 to 70, both ends inclusive.
    assert verdict("PMSBY", age=17) is N and verdict("PMSBY", age=18) is E
    assert verdict("PMSBY", age=70) is E and verdict("PMSBY", age=71) is N
    assert verdict("PMSBY", age=30, has_bank_account=False) is N
    # ! PMSBY has NO tax or EPFO bar. If someone ever adds one, this fails.
    assert verdict("PMSBY", age=30, is_income_tax_payer=True) is E
    assert verdict("PMSBY", age=30, is_statutory_scheme_member=True) is E

    # PM-SYM: 18 to 40 inclusive, ₹15,000 or less, no EPFO/ESIC/NPS, no tax.
    assert verdict("PM_SYM", age=17) is N and verdict("PM_SYM", age=18) is E
    assert verdict("PM_SYM", age=40) is E and verdict("PM_SYM", age=41) is N
    assert verdict("PM_SYM", age=30, income_band="10001_15000") is E
    assert verdict("PM_SYM", age=30, income_band="15001_25000") is N
    # ! Zero income sits under the ceiling and must qualify. It is its own band
    # ! precisely because a worker with nothing coming in would not pick
    # ! "up to ₹5,000" — and an earlier list left it out entirely.
    assert verdict("PM_SYM", age=30, income_band="no_income") is E
    assert verdict("PM_SYM", age=30, is_statutory_scheme_member=True) is N
    assert verdict("PM_SYM", age=30, is_income_tax_payer=True) is N

    # e-Shram: 16 and above, no EPFO/ESIC, no tax.
    assert verdict("ESHRAM", age=15) is N and verdict("ESHRAM", age=16) is E
    assert verdict("ESHRAM", age=30, is_statutory_scheme_member=True) is N
    assert verdict("ESHRAM", age=30, is_income_tax_payer=True) is N


def test_dont_know_never_becomes_a_no():
    """"Don't know" is a real button. It must produce UNKNOWN, never a refusal.

    # ! The one exception is a DEFINITE exclusion elsewhere: if the worker says
    # ! they are in EPFO, an unknown tax answer cannot rescue them.
    """
    schemes = _signed_schemes()
    for code in ("ESHRAM", "PM_SYM"):
        p = Profile(age=30, income_band="no_income", has_bank_account=True,
                    is_income_tax_payer=None, is_statutory_scheme_member=False)
        assert evaluate(p, schemes[code]).verdict is Verdict.UNKNOWN, code
        p2 = Profile(
            age=30, income_band="no_income", has_bank_account=True,
            is_income_tax_payer=None, is_statutory_scheme_member=True)
        assert evaluate(p2, schemes[code]).verdict is Verdict.INELIGIBLE, code


def test_eshram_has_no_upper_age_limit_yet():
    """# ! OPEN QUESTION A2, pinned so it cannot be forgotten silently.

    e-Shram's own FAQ says "16 and above", but other official e-Shram pages
    describe registration as 16-59. The files encode "16 and above", so a
    70-year-old is currently told YES. If 16-59 turns out to be correct, every
    worker aged 60+ is getting a wrong answer today.

    This test PASSES on the current reading. It exists to fail loudly the day
    someone adds an upper bound without updating docs/VERIFICATION.md — and to
    make the exposure visible while the question is open.
    """
    schemes = _signed_schemes()
    old = Profile(age=70, income_band="no_income", has_bank_account=True,
                  is_income_tax_payer=False, is_statutory_scheme_member=False)
    assert evaluate(old, schemes["ESHRAM"]).verdict is Verdict.ELIGIBLE, (
        "e-Shram now has an upper age bound — settle question A2 in "
        "docs/VERIFICATION.md and update this test deliberately"
    )


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_rule_boundaries.py OK")


if __name__ == "__main__":
    run()
