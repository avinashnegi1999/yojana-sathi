"""Are the verdicts RIGHT? Run: python3 tests/test_rule_boundaries.py

# ! Every other test asks whether the software works. This one asks whether the
# ! ANSWER matches the encoded source interpretation, which is a different
# ! question from channel behavior. Unresolved source conflicts remain human
# ! gates in docs/history/SCHEME_AUDIT.md; this sweep cannot establish legal correctness.
# ! A wrong answer costs a
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

    age, income, tax, bank = p.age, p.income_band, p.is_income_tax_payer, p.has_bank_account

    # ! The oracle names the memberships the way each SOURCE names them, not the
    # ! way the Profile stores them. Until 2026-09-03 both this file and the
    # ! engine shared one "statutory member" abstraction covering EPFO, ESIC and
    # ! NPS together — so the sweep could not tell that e-Shram's own wording
    # ! excludes only EPFO and ESIC. Two implementations only catch a bug when
    # ! they are free to disagree, and sharing an abstraction removes exactly
    # ! that freedom. Keep these expressed per-scheme.
    epfo_or_esic, nps = p.is_epfo_or_esic_member, p.nps_exclusion_applies

    if code == "PMSBY":
        # jansuraksha.gov.in rules PDF: "aged between 18 years (completed) and 70
        # years", "All individual bank/ Post office account holders". No income
        # bar and no tax bar anywhere in that document — deliberately none here.
        criterion(None if age is None else 18 <= age <= 70)
        # DFS terminates at nearest birthday 70; whole age 69 straddles it.
        criterion(None if age is None or age == 69 else age < 70)
        criterion(bank)
    elif code == "PM_SYM":
        criterion(p.is_unorganised_worker)
        # maandhan.in: entry age 18-40, monthly income ₹15,000 or less, and not
        # a member of EPFO/ESIC/NPS, and not an income-tax payer.
        criterion(None if age is None else 18 <= age <= 40)
        criterion(None if income is None else income in PM_SYM_BANDS)
        # "covered under any statutory Social Security Scheme such as NPS, ESIC,
        #  EPFO" — all three bar entry, so either field alone disqualifies.
        exclusion(epfo_or_esic)
        exclusion(nps)
        exclusion(tax)
    elif code == "ESHRAM":
        criterion(p.is_unorganised_worker)
        # eshram.gov.in FAQ: 16 and above; an unorganised worker is one who is
        # not an EPFO/ESIC member and not an income-tax payer.
        criterion(None if age is None else age >= 16)
        exclusion(tax)
        # ! EPFO/ESIC only. The FAQ defines an unorganised worker as one "not a
        # ! member of ESIC or EPFO" and never mentions NPS, so NPS is absent
        # ! here on purpose. This asymmetry with PM-SYM above is the whole
        # ! reason the two fields exist.
        exclusion(epfo_or_esic)
    elif code == "PMJJBY":
        criterion(None if age is None else 18 <= age <= 50)
        criterion(bank)
    elif code in ("UK_OLD_AGE", "UK_WIDOW"):
        criterion(None if p.state is None else p.state == "UK")
        criterion(None if age is None else age >= (60 if code == "UK_OLD_AGE" else 18))
        criterion(p.uk_pension_income_or_bpl)
        criterion(p.uk_pension_selected)
        if code == "UK_WIDOW":
            criterion(p.is_widow)
            # ! OUT OF DATE, and deliberately not "fixed" from the TOML. Since
            # ! 2026-09-15 uk_widow.toml carries an other-pension EXCLUSION
            # ! sourced to the department's Hindi pension overview, and that
            # ! file is unsigned. Encoding it here by copying the TOML would make
            # ! the oracle agree with the file by construction. Before UK_WIDOW
            # ! is re-signed, read that overview and write the exclusion here
            # ! from it. Until then the per-scheme sweep below skips unsigned
            # ! files, and the old sweep never varies receives_other_pension.
    elif code == "APY":
        # pfrda.org.in/w/faqs/atal-pension-yojana, read 12 September 2026:
        # "(i) The age of an individual should be between 18 and 40 years.
        #  (ii) He / She should have a savings bank account/ post office savings
        #  bank account. (iii) From 1st October, 2022, any Indian citizen who is
        #  or has been an income-tax payer ... will not be eligible to open a
        #  new APY account."
        # ! Two age criteria in the file rather than one range, so the worker is
        # ! told WHICH end she missed. The oracle states it as a range because
        # ! the verdict is identical either way - that difference is exactly
        # ! what this sweep is allowed to prove, and what it must not assume.
        criterion(None if age is None else 18 <= age <= 40)
        criterion(bank)
        # ! No EPFO/ESIC or NPS exclusion, deliberately. PM-SYM has one and the
        # ! shapes are otherwise near-identical, so the temptation to copy it is
        # ! real. The PFRDA FAQ states no such bar and explicitly allows
        # ! Central/State Government employees. An unsourced exclusion REFUSES
        # ! someone, which is the failure this project cares about most.
        exclusion(tax)
    elif code == "PMJAY_70":
        # Union Cabinet, PIB PRID=2053883: "all the senior citizens aged 70
        # years and above irrespective of income".
        # ! One condition, and the oracle has to be as bare as the file. There
        # ! is no income test, no occupation test and no state test to mirror -
        # ! adding any here would make the sweep agree with a file that wrongly
        # ! refused people, which is the one thing an oracle exists to catch.
        criterion(None if age is None else age >= 70)
    elif code in ("IGNOAPS", "IGNWPS", "IGNDPS"):
        # NSAP, via myscheme.gov.in/schemes/nsap-ignoaps, /ignwps, /igndps
        # (nsap.nic.in refused connections on 12 September 2026). All three:
        # BPL household. Then 60+ / widow 40+ / 18+ with an 80% certificate.
        criterion(p.is_bpl)
        if code == "IGNOAPS":
            criterion(None if age is None else age >= 60)
        elif code == "IGNWPS":
            criterion(p.is_widow)
            criterion(None if age is None else age >= 40)
        else:
            criterion(None if age is None else age >= 18)
            criterion(p.has_disability_80pct)
    elif code == "NPS_TRADERS":
        # maandhan.in FAQ Q2: trader/shopkeeper/self-employed, turnover <= 1.5
        # crore, 18-40, not an income-tax payer, not NPS(govt)/ESIC/EPFO.
        criterion(p.is_small_trader)
        criterion(None if age is None else 18 <= age <= 40)
        exclusion(tax)
        exclusion(epfo_or_esic)
        exclusion(nps)
        # ! Same FAQ answer, last clause, which this oracle had dropped: "They
        # ! should not be … a member of … Pradhan Mantri Shram Yogi Maandhan."
        # ! (docs/audit-evidence/nps-traders-maandhan-faq-2026-09-14.txt:11).
        # ! The old sweep never varied known_schemes, so the gap was invisible.
        exclusion("PM_SYM" in p.known_schemes)
    elif code == "PM_VISHWAKARMA":
        # PIB PRID=1989108: one of 18 trades, 18+, no unpaid PMEGP/MUDRA/
        # SVANidhi loan in 5 years, and no government service in the immediate
        # family. These are criteria (eq false) so the intake asks them; a
        # field used only by an exclusion would never be collected.
        criterion(p.is_vishwakarma_artisan)
        criterion(None if age is None else age >= 18)
        criterion(None if p.took_business_loan_5yr is None else not p.took_business_loan_5yr)
        criterion(None if p.has_government_service_in_family is None
                  else not p.has_government_service_in_family)
    elif code == "PMJDY":
        # pmjdy.gov.in. Inverted on purpose: surfaced to the person WITHOUT an
        # account, the only person a free account helps.
        criterion(None if bank is None else not bank)
    elif code == "PMUY":
        criterion(None if age is None else age >= 18)
        criterion(p.is_woman)
        criterion(None if p.household_has_lpg is None else not p.household_has_lpg)
        criterion(p.pmuy_declaration_met)
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
    # ! stubs=() as well as a signature. This sweep checks the ENCODED
    # ! CONDITIONS against the oracle below, and a file with a documented TODO
    # ! (UK_WIDOW's withdrawn benefit amount) is unservable, so every case in it
    # ! would come back UNKNOWN and the sweep would silently test nothing.
    # ! The ₹ values are not part of what this test compares.
    return {
        code: replace(sc, verified_by="test-signature (tests/test_rule_boundaries.py)",
                      stubs=())
        for code, sc in load_all(ROOT / "data" / "schemes").items()
    }


def test_every_combination_matches_the_encoded_source_interpretation():
    schemes = _signed_schemes()
    missing = set(schemes) - {"ESHRAM", "PM_SYM", "PMSBY", "PMJJBY", "UK_OLD_AGE",
                              "UK_WIDOW", "PMUY", "APY", "PMJAY_70",
                              "IGNOAPS", "IGNWPS", "IGNDPS", "NPS_TRADERS",
                              "PM_VISHWAKARMA", "PMJDY"}
    assert not missing, f"a scheme was added with no oracle: {sorted(missing)}"

    checked = 0
    wrong = []
    for age, income, bank, tax, epfo, nps, worker, government_family in itertools.product(
        AGES, INCOME, TRI, TRI, TRI, TRI, TRI, TRI
    ):
        p = Profile(is_unorganised_worker=worker, age=age, income_band=income, has_bank_account=bank,
                    is_income_tax_payer=tax, is_epfo_or_esic_member=epfo,
                    nps_exclusion_applies=nps,
                    has_government_service_in_family=government_family)
        for code, scheme in schemes.items():
            got = evaluate(p, scheme).verdict
            want = _expected(code, p)
            checked += 1
            if got is not want:
                wrong.append(f"{code} age={age} income={income} bank={bank} "
                             f"tax={tax} epfo_or_esic={epfo} nps={nps} government_family={government_family}: "
                             f"got {got.value}, official rules say {want.value}")
    assert not wrong, "\n  " + "\n  ".join(wrong[:20])
    # ! Coverage counter, same reason as test_all_paths: a sweep that swept
    # ! nothing passes silently.
    assert checked > 5000, f"only {checked} verdicts checked"
    print(f"  .. {checked:,} verdicts checked against the encoded source interpretation")


# * Values for the non-boolean fields a scheme file can touch. Every boolean
# * Profile field is swept over TRI. A new non-boolean field in a scheme file
# * fails the sweep below until it gets a list here, so nothing is silently
# * held at None again.
SWEEP_VALUES = {
    "age": sorted(set(a for a in AGES if a is not None) | {49, 50, 51, 79, 80, 81}) + [None],
    "income_band": INCOME,
    "state": [None, "UK", "UP", "BR"],
    "known_schemes": [frozenset(), frozenset({"PM_SYM"}), frozenset({"PMSBY"})],
}
NON_BOOLEAN_FIELDS = {"age", "income_band", "state", "known_schemes", "occupation",
                      "land_holding_band", "family_size"}


def test_every_signed_scheme_is_swept_over_its_own_fields():
    """AUDIT.md M3: the combined sweep above holds every field it does not
    list at None, so 6 of the 10 signed schemes (the three NSAP pensions,
    NPS-Traders, PMUY and the Uttarakhand old-age pension) never produced a
    single ELIGIBLE verdict in it. A wrong BPL, state, widow or trader
    condition could not fail it.

    This sweeps each SIGNED scheme over every combination of exactly the
    fields its own criteria and exclusions touch, and compares against the
    same hand-written oracle. It also requires every signed scheme to reach
    ELIGIBLE at least once, so an oracle that only ever agrees on UNKNOWN
    cannot pass.
    """
    real = load_all(ROOT / "data" / "schemes")
    signed_codes = sorted(code for code, sc in real.items() if sc.is_human_verified)
    schemes = _signed_schemes()
    wrong, checked = [], 0
    for code in signed_codes:
        scheme = schemes[code]
        fields = sorted({c.field for c in scheme.criteria + scheme.exclusions})
        domains = []
        for field in fields:
            if field in SWEEP_VALUES:
                domains.append(SWEEP_VALUES[field])
            elif field in NON_BOOLEAN_FIELDS:
                raise AssertionError(f"{code} uses {field}; give it values in SWEEP_VALUES")
            else:
                domains.append(TRI)
        eligible = 0
        for combo in itertools.product(*domains):
            p = Profile(**dict(zip(fields, combo)))
            got = evaluate(p, scheme).verdict
            want = _expected(code, p)
            checked += 1
            eligible += got is Verdict.ELIGIBLE
            if got is not want:
                wrong.append(f"{code} {dict(zip(fields, combo))}: got {got.value}, "
                             f"oracle says {want.value}")
        assert eligible, f"{code} never reached ELIGIBLE — the sweep proves nothing for it"
    assert not wrong, "\n  " + "\n  ".join(wrong[:20])
    assert len(signed_codes) >= 10, signed_codes
    print(f"  .. {checked:,} per-scheme verdicts across {len(signed_codes)} signed schemes, "
          f"each reaching ELIGIBLE")


def test_the_named_boundaries_individually():
    """The thresholds a human would check by hand, stated one per line.

    # * Redundant with the sweep on purpose: when the sweep fails, this says
    # * WHICH edge moved without needing to read a combination dump.
    """
    schemes = _signed_schemes()

    def verdict(code, **kw):
        base = dict(is_unorganised_worker=True, income_band="no_income", has_bank_account=True,
                    is_income_tax_payer=False, is_epfo_or_esic_member=False,
                    nps_exclusion_applies=False)
        base.update(kw)
        return evaluate(Profile(**base), schemes[code]).verdict

    E, N = Verdict.ELIGIBLE, Verdict.INELIGIBLE

    # PMSBY: entry age plus the nearest-birthday termination condition.
    assert verdict("PMSBY", age=17) is N and verdict("PMSBY", age=18) is E
    assert verdict("PMSBY", age=68) is E
    assert verdict("PMSBY", age=69) is Verdict.UNKNOWN
    assert verdict("PMSBY", age=70) is N and verdict("PMSBY", age=71) is N
    assert verdict("PMSBY", age=30, has_bank_account=False) is N
    # ! PMSBY has NO tax or EPFO bar. If someone ever adds one, this fails.
    assert verdict("PMSBY", age=30, is_income_tax_payer=True) is E
    assert verdict("PMSBY", age=30, is_epfo_or_esic_member=True) is E
    assert verdict("PMSBY", age=30, nps_exclusion_applies=True) is E

    # PM-SYM: 18 to 40 inclusive, ₹15,000 or less, no EPFO/ESIC/NPS, no tax.
    assert verdict("PM_SYM", age=17) is N and verdict("PM_SYM", age=18) is E
    assert verdict("PM_SYM", age=40) is E and verdict("PM_SYM", age=41) is N
    assert verdict("PM_SYM", age=30, income_band="10001_15000") is E
    assert verdict("PM_SYM", age=30, income_band="15001_25000") is N
    # ! Zero income sits under the ceiling and must qualify. It is its own band
    # ! precisely because a worker with nothing coming in would not pick
    # ! "up to ₹5,000" — and an earlier list left it out entirely.
    assert verdict("PM_SYM", age=30, income_band="no_income") is E
    assert verdict("PM_SYM", age=30, is_epfo_or_esic_member=True) is N
    assert verdict("PM_SYM", age=30, nps_exclusion_applies=True) is N
    assert verdict("PM_SYM", age=30, is_income_tax_payer=True) is N

    # e-Shram: 16 and above, no EPFO/ESIC, no tax.
    assert verdict("ESHRAM", age=15) is N and verdict("ESHRAM", age=16) is E
    assert verdict("ESHRAM", age=30, is_epfo_or_esic_member=True) is N
    # ! NPS alone does NOT bar e-Shram. This single line is the bug that one
    # ! conflated field made impossible to express, let alone catch.
    assert verdict("ESHRAM", age=30, nps_exclusion_applies=True) is E
    assert verdict("ESHRAM", age=30, is_income_tax_payer=True) is N

    # PM Vishwakarma: the government-service condition applies to the artisan,
    # spouse and unmarried children. It must not become a warning-only fact.
    artisan = dict(age=18, is_vishwakarma_artisan=True, took_business_loan_5yr=False)
    assert verdict("PM_VISHWAKARMA", **artisan,
                   has_government_service_in_family=False) is E
    assert verdict("PM_VISHWAKARMA", **artisan,
                   has_government_service_in_family=True) is N
    assert verdict("PM_VISHWAKARMA", **artisan,
                   has_government_service_in_family=None) is Verdict.UNKNOWN


def test_dont_know_never_becomes_a_no():
    """"Don't know" is a real button. It must produce UNKNOWN, never a refusal.

    # ! The one exception is a DEFINITE exclusion elsewhere: if the worker says
    # ! they are in EPFO, an unknown tax answer cannot rescue them.
    """
    schemes = _signed_schemes()
    for code in ("ESHRAM", "PM_SYM"):
        p = Profile(is_unorganised_worker=True, age=30, income_band="no_income", has_bank_account=True,
                    is_income_tax_payer=None, is_epfo_or_esic_member=False,
                    nps_exclusion_applies=False)
        assert evaluate(p, schemes[code]).verdict is Verdict.UNKNOWN, code
        p2 = Profile(
            age=30, income_band="no_income", has_bank_account=True,
            is_income_tax_payer=None, is_epfo_or_esic_member=True,
            nps_exclusion_applies=False)
        assert evaluate(p2, schemes[code]).verdict is Verdict.INELIGIBLE, code


def test_eshram_has_no_upper_age_limit_yet():
    """# ! OPEN QUESTION A2, pinned so it cannot be forgotten silently.

    e-Shram's own FAQ says "16 and above", but other official e-Shram pages
    describe registration as 16-59. The files encode "16 and above", so a
    70-year-old in this signed TEST fixture receives YES. Production remains
    UNKNOWN because the scheme is unsigned. If 16-59 is confirmed, the rule and
    oracle both need correction before human sign-off.

    This test PASSES on the current reading. It exists to fail loudly the day
    someone adds an upper bound without updating docs/history/VERIFICATION.md — and to
    make the exposure visible while the question is open.
    """
    schemes = _signed_schemes()
    old = Profile(is_unorganised_worker=True, age=70, income_band="no_income", has_bank_account=True,
                  is_income_tax_payer=False, is_epfo_or_esic_member=False,
                  nps_exclusion_applies=False)
    assert evaluate(old, schemes["ESHRAM"]).verdict is Verdict.ELIGIBLE, (
        "e-Shram now has an upper age bound — settle question A2 in "
        "docs/history/VERIFICATION.md and update this test deliberately"
    )


def test_central_government_nps_excludes_pm_sym_but_not_eshram():
    """# ! The pair of cases that one conflated field made inexpressible.

    The current ministry reply specifies central-government-contributed NPS.
    Other NPS types remain UNKNOWN. e-Shram defines an unorganised worker as one who is
    "not a member of ESIC or EPFO" — no mention of NPS anywhere.

    So the two schemes must disagree about a worker reporting central NPS and nothing
    else. Before the split they could not: one field fed both rules, e-Shram
    inherited PM-SYM's NPS bar, and a worker was turned away from the gateway
    scheme that every other benefit is delivered through. A wrong NO here is a
    missed entitlement, which is a correctness failure and not a safe default.
    """
    schemes = _signed_schemes()

    def verdicts(**kw):
        base = dict(is_unorganised_worker=True, age=30, income_band="no_income", has_bank_account=True,
                    is_income_tax_payer=False)
        base.update(kw)
        p = Profile(**base)
        return {c: evaluate(p, s).verdict for c, s in schemes.items()}

    nps_only = verdicts(is_epfo_or_esic_member=False, nps_exclusion_applies=True)
    assert nps_only["PM_SYM"] is Verdict.INELIGIBLE
    assert nps_only["ESHRAM"] is Verdict.ELIGIBLE, (
        "NPS alone must not bar e-Shram — its FAQ names only ESIC and EPFO"
    )

    epfo_only = verdicts(is_epfo_or_esic_member=True, nps_exclusion_applies=False)
    assert epfo_only["PM_SYM"] is Verdict.INELIGIBLE
    assert epfo_only["ESHRAM"] is Verdict.INELIGIBLE

    # * PMSBY has no membership bar at all, so it is unmoved by either.
    assert nps_only["PMSBY"] is Verdict.ELIGIBLE
    assert epfo_only["PMSBY"] is Verdict.ELIGIBLE


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_rule_boundaries.py OK")


if __name__ == "__main__":
    run()
