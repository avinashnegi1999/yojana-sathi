"""The only place eligibility is decided.

# ! NO LLM IMPORT IS PERMITTED IN THIS MODULE, ever, at any depth. Compute here,
# ! narrate elsewhere. tests/test_rules.py asserts this module's import graph
# ! stays clean, so a stray import fails the build rather than a demo.
#
# * evaluate(profile, scheme) is a pure function: no I/O, no clock, no network,
# * no randomness. Same inputs, same output, always. That is what makes the
# * whole engine testable with a plain table and no mocks.
"""

from dataclasses import dataclass
from enum import Enum

from sathi.core.profile import Profile
from sathi.core.schemes import Criterion, Scheme
from sathi.rules import operators


class Verdict(Enum):
    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"
    UNKNOWN = "unknown"  # ! missing profile answer OR unverified scheme data


class ReasonCode(Enum):
    """Why a line came out the way it did. The render layer maps these to Hindi."""

    CRITERION_PASS = "criterion_pass"
    CRITERION_FAIL = "criterion_fail"
    CRITERION_UNKNOWN = "criterion_unknown"
    EXCLUDED = "excluded"
    UNVERIFIED_DATA = "unverified_data"  # ! unresearched OR not signed off
    BAD_RULE = "bad_rule"  # a scheme-file bug: surfaced, never swallowed


@dataclass(frozen=True)
class Reason:
    """One line of explanation. Text is AUTHORED in the TOML, never generated.

    An LLM may rephrase `text_hi` for a specific listener. It may not write one.
    """

    code: ReasonCode
    field: str
    text_hi: str = ""
    source_url: str = ""
    detail: str = ""  # machine detail (a missing field name, an operator error)


@dataclass(frozen=True)
class Result:
    scheme_code: str
    verdict: Verdict
    reasons: tuple[Reason, ...]
    missing_fields: tuple[str, ...]
    unverified: bool
    annual_value_inr: int
    value_basis: str

    @property
    def is_eligible(self) -> bool:
        return self.verdict is Verdict.ELIGIBLE

    def reasons_with(self, code: ReasonCode) -> tuple[Reason, ...]:
        return tuple(r for r in self.reasons if r.code is code)

    @property
    def blocking_reason(self) -> Reason | None:
        """The single line that best explains an INELIGIBLE verdict.

        An exclusion outranks a failed criterion: "you are an income-tax payer"
        is a more useful thing to hear than "your income band is too high".
        """
        for code in (ReasonCode.EXCLUDED, ReasonCode.CRITERION_FAIL):
            hits = self.reasons_with(code)
            if hits:
                return hits[0]
        return None


def _check(criterion: Criterion, profile: Profile) -> tuple[bool | None, str]:
    """Run one criterion. Returns (outcome, error_detail)."""
    try:
        actual = getattr(profile, criterion.field)
    except AttributeError:
        # * The loader rejects unknown fields, so this only fires if a field was
        # * deleted from Profile after a scheme file started using it.
        return None, f"{criterion.field} is not a Profile field"
    try:
        return operators.apply(criterion.op, actual, criterion.value), ""
    except operators.OperatorError as e:
        return None, str(e)


def evaluate(profile: Profile, scheme: Scheme) -> Result:
    """Decide one scheme for one worker. Pure function.

    Precedence, in order — a definite NO outranks a maybe:
      1. scheme not servable            → UNKNOWN, always, no further checking
         (a "TODO" is left, OR no named human has signed `verified_by`)
      2. any exclusion definitely hits  → INELIGIBLE
      3. any criterion definitely fails → INELIGIBLE
      4. anything undecidable           → UNKNOWN
      5. otherwise                      → ELIGIBLE
    """
    value = scheme.annual_value_inr()
    basis = scheme.benefit.get("value_basis")
    basis = basis if isinstance(basis, str) else ""

    # ! Rule 1. A scheme nobody has finished never produces a verdict, not even
    # ! a negative one. "We haven't checked this yet" is the honest output, and
    # ! it still helps: the worker gets a question to ask at the centre.
    #
    # ! Two ways to be unfinished, and BOTH stop here. Values still reading
    # ! "TODO" is the obvious one. The second — every value filled in but
    # ! `verified_by` still saying PENDING HUMAN VERIFICATION — used to fall
    # ! straight through this gate and serve real ELIGIBLE verdicts off
    # ! transcription nobody had double-checked.
    if not scheme.is_servable:
        detail = (
            ", ".join(scheme.stubs[:5])
            if scheme.stubs
            else f"awaiting sign-off: verified_by = {scheme.verified_by!r}"
        )
        return Result(
            scheme_code=scheme.code,
            verdict=Verdict.UNKNOWN,
            reasons=(
                Reason(
                    code=ReasonCode.UNVERIFIED_DATA,
                    field="",
                    detail=detail,
                ),
            ),
            missing_fields=(),
            unverified=True,
            annual_value_inr=0,  # ! never let an unverified ₹ reach a metric
            value_basis=basis,
        )

    reasons: list[Reason] = []
    missing: list[str] = []
    excluded = False
    failed = False
    undecided = False

    for ex in scheme.exclusions:
        outcome, err = _check(ex, profile)
        if outcome is True:
            excluded = True
            reasons.append(
                Reason(ReasonCode.EXCLUDED, ex.field, ex.reason_hi, ex.source_url)
            )
        elif outcome is None:
            undecided = True
            code = ReasonCode.BAD_RULE if err else ReasonCode.CRITERION_UNKNOWN
            reasons.append(Reason(code, ex.field, "", ex.source_url, err))
            if not err and not profile.is_answered(ex.field):
                missing.append(ex.field)

    for c in scheme.criteria:
        outcome, err = _check(c, profile)
        if outcome is True:
            reasons.append(
                Reason(ReasonCode.CRITERION_PASS, c.field, c.pass_hi, c.source_url)
            )
        elif outcome is False:
            failed = True
            reasons.append(
                Reason(ReasonCode.CRITERION_FAIL, c.field, c.fail_hi, c.source_url)
            )
        else:
            undecided = True
            code = ReasonCode.BAD_RULE if err else ReasonCode.CRITERION_UNKNOWN
            reasons.append(Reason(code, c.field, "", c.source_url, err))
            if not err and not profile.is_answered(c.field):
                missing.append(c.field)

    if excluded or failed:
        verdict = Verdict.INELIGIBLE
    elif undecided:
        verdict = Verdict.UNKNOWN
    else:
        verdict = Verdict.ELIGIBLE

    return Result(
        scheme_code=scheme.code,
        verdict=verdict,
        reasons=tuple(reasons),
        missing_fields=tuple(dict.fromkeys(missing)),  # dedup, keep ask order
        unverified=False,
        # * ₹ counts only when the worker actually qualifies. A value attached to
        # * an INELIGIBLE or UNKNOWN result would quietly inflate the headline.
        annual_value_inr=value if verdict is Verdict.ELIGIBLE else 0,
        value_basis=basis,
    )


# * Sort order for the result screen: eligible first (biggest ₹ at the top,
# * because that is the one worth the trip), then unknown, then ineligible.
_VERDICT_RANK = {Verdict.ELIGIBLE: 0, Verdict.UNKNOWN: 1, Verdict.INELIGIBLE: 2}


def evaluate_all(profile: Profile, schemes: dict[str, Scheme]) -> tuple[Result, ...]:
    results = [evaluate(profile, s) for s in schemes.values()]
    results.sort(key=lambda r: (_VERDICT_RANK[r.verdict], -r.annual_value_inr, r.scheme_code))
    return tuple(results)


def total_value(results: tuple[Result, ...], only_codes: frozenset[str] | None = None) -> int:
    """₹ across eligible results. `only_codes` narrows it to newly surfaced ones.

    # ! This is "annual entitlement surfaced", never "money delivered". The
    # ! label travels with the number everywhere it is shown.
    """
    return sum(
        r.annual_value_inr
        for r in results
        if r.is_eligible and (only_codes is None or r.scheme_code in only_codes)
    )


def newly_surfaced(results: tuple[Result, ...], known: frozenset[str]) -> tuple[str, ...]:
    """Eligible schemes the worker did NOT already know about — the headline metric."""
    return tuple(r.scheme_code for r in results if r.is_eligible and r.scheme_code not in known)


def _self_check() -> None:
    # * Full coverage lives in tests/test_rules.py. This is the smoke test that
    # * runs on import from check.py.
    from sathi.core.schemes import Criterion as C

    def scheme(**kw) -> Scheme:
        base = dict(
            code="T", name_en="T", name_hi="ट", authority="A",
            official_url="u", verified_on="2026-09-01", verified_by="a",
            benefit={"annual_value_inr": 12000, "value_basis": "annual_payout"},
            criteria=(C("age", "between", [18, 40], "u", pass_hi="ठीक", fail_hi="नहीं"),),
            exclusions=(), documents=("x",), where_to_apply="csc", renewal="none",
        )
        base.update(kw)
        return Scheme(**base)

    assert evaluate(Profile(age=30), scheme()).verdict is Verdict.ELIGIBLE
    assert evaluate(Profile(age=50), scheme()).verdict is Verdict.INELIGIBLE
    assert evaluate(Profile(), scheme()).verdict is Verdict.UNKNOWN
    assert evaluate(Profile(age=30), scheme(stubs=("benefit.annual_value_inr",))).verdict is Verdict.UNKNOWN
    # ! Researched but unsigned must be UNKNOWN too. This is the regression that
    # ! let PENDING-verification schemes serve real verdicts.
    unsigned = scheme(verified_by="unconfirmed — PENDING HUMAN VERIFICATION")
    assert not unsigned.stubs, "the point of this case is that there is no TODO"
    assert evaluate(Profile(age=30), unsigned).verdict is Verdict.UNKNOWN
    assert evaluate(Profile(age=30), unsigned).unverified
    assert evaluate(Profile(age=30), unsigned).annual_value_inr == 0
    assert evaluate(Profile(age=50), unsigned).verdict is Verdict.UNKNOWN, \
        "an unsigned scheme must not even produce a NO"
    assert evaluate(Profile(age=30), scheme()).annual_value_inr == 12000
    assert evaluate(Profile(age=50), scheme()).annual_value_inr == 0
    print("engine.py OK")


if __name__ == "__main__":
    _self_check()
