"""Rule engine checks. Run: python3 tests/test_rules.py

# * The engine is a pure function, so this is one table of
# * (profile, scheme) -> expected verdict and no mocks anywhere.
#
# ! Every UNKNOWN path is covered on purpose. UNKNOWN is the behaviour that
# ! stops a guessed threshold reaching a worker, and untested safety behaviour
# ! is not safety behaviour.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.core.profile import Profile
from sathi.core.schemes import STUB, Criterion, Scheme
from sathi.rules.engine import (
    ReasonCode,
    Verdict,
    evaluate,
    evaluate_all,
    newly_surfaced,
    total_value,
)


def scheme(code="T", *, criteria=(), exclusions=(), value=12000, stubs=()) -> Scheme:
    return Scheme(
        code=code,
        name_en=code,
        name_hi=f"योजना-{code}",
        authority="Test Ministry",
        official_url="https://example.gov.in/t",
        verified_on="2026-09-01",
        verified_by="test",
        benefit={"annual_value_inr": value, "value_basis": "annual_payout",
                 "summary_hi": "टेस्ट"},
        criteria=criteria or (
            Criterion("age", "between", [18, 40], "u", pass_hi="उम्र सही", fail_hi="उम्र बाहर"),
        ),
        exclusions=exclusions,
        documents=("आधार",),
        where_to_apply="csc",
        renewal="none",
        stubs=stubs,
    )


AGE_ONLY = scheme()
WITH_EXCLUSION = scheme(
    exclusions=(Criterion("is_income_tax_payer", "eq", True, "u", reason_hi="आप आयकर भरते हैं"),)
)
TWO_CRITERIA = scheme(
    criteria=(
        Criterion("age", "between", [18, 40], "u", pass_hi="उम्र सही", fail_hi="उम्र बाहर"),
        Criterion("income_band", "in", ["upto_5000"], "u", pass_hi="कमाई सही", fail_hi="कमाई ज़्यादा"),
    )
)
UNRESEARCHED = scheme(stubs=("criteria[0].value",), value=0)

# (label, profile, scheme, expected verdict)
TABLE = [
    ("in band", Profile(age=30), AGE_ONLY, Verdict.ELIGIBLE),
    ("lower edge is inclusive", Profile(age=18), AGE_ONLY, Verdict.ELIGIBLE),
    ("upper edge is inclusive", Profile(age=40), AGE_ONLY, Verdict.ELIGIBLE),
    ("one year over", Profile(age=41), AGE_ONLY, Verdict.INELIGIBLE),
    ("age never asked", Profile(), AGE_ONLY, Verdict.UNKNOWN),

    ("all criteria pass", Profile(age=30, income_band="upto_5000"), TWO_CRITERIA, Verdict.ELIGIBLE),
    ("one criterion fails", Profile(age=30, income_band="above_25000"), TWO_CRITERIA, Verdict.INELIGIBLE),
    ("one criterion unanswered", Profile(age=30), TWO_CRITERIA, Verdict.UNKNOWN),
    # ! A definite NO outranks a maybe: we can say "no" honestly here.
    ("failure beats a missing answer", Profile(age=99), TWO_CRITERIA, Verdict.INELIGIBLE),

    ("exclusion hits", Profile(age=30, is_income_tax_payer=True), WITH_EXCLUSION, Verdict.INELIGIBLE),
    ("exclusion misses", Profile(age=30, is_income_tax_payer=False), WITH_EXCLUSION, Verdict.ELIGIBLE),
    ("exclusion unanswered", Profile(age=30), WITH_EXCLUSION, Verdict.UNKNOWN),

    # ! The core anti-hallucination path: unresearched file, no verdict, ever.
    ("stub in the file", Profile(age=30), UNRESEARCHED, Verdict.UNKNOWN),
    ("stub beats a clear fail", Profile(age=99), UNRESEARCHED, Verdict.UNKNOWN),
    ("stub with an empty profile", Profile(), UNRESEARCHED, Verdict.UNKNOWN),
]


def test_verdict_table():
    for label, profile, sc, expected in TABLE:
        got = evaluate(profile, sc).verdict
        assert got is expected, f"{label}: expected {expected}, got {got}"


def test_unverified_scheme_never_contributes_rupees():
    r = evaluate(Profile(age=30), UNRESEARCHED)
    assert r.annual_value_inr == 0 and r.unverified
    assert r.reasons[0].code is ReasonCode.UNVERIFIED_DATA


def test_rupees_only_count_when_eligible():
    assert evaluate(Profile(age=30), AGE_ONLY).annual_value_inr == 12000
    assert evaluate(Profile(age=99), AGE_ONLY).annual_value_inr == 0
    assert evaluate(Profile(), AGE_ONLY).annual_value_inr == 0


def test_reasons_are_the_authored_strings():
    # ! Nothing here is generated. Both strings come from the scheme file.
    ok = evaluate(Profile(age=30), AGE_ONLY)
    assert ok.reasons_with(ReasonCode.CRITERION_PASS)[0].text_hi == "उम्र सही"
    no = evaluate(Profile(age=99), AGE_ONLY)
    assert no.blocking_reason.text_hi == "उम्र बाहर"


def test_exclusion_outranks_criterion_in_the_explanation():
    r = evaluate(Profile(age=99, is_income_tax_payer=True), WITH_EXCLUSION)
    assert r.blocking_reason.code is ReasonCode.EXCLUDED
    assert r.blocking_reason.text_hi == "आप आयकर भरते हैं"


def test_missing_fields_are_reported_for_the_worker():
    r = evaluate(Profile(), TWO_CRITERIA)
    assert r.missing_fields == ("age", "income_band"), r.missing_fields


def test_broken_rule_is_surfaced_not_swallowed():
    # * A scheme file comparing an age band to a string is a bug. The worker gets
    # * UNKNOWN; the detail is kept for whoever fixes the file.
    broken = scheme(criteria=(Criterion("occupation", "gte", 5, "u", pass_hi="a", fail_hi="b"),))
    r = evaluate(Profile(occupation="construction"), broken)
    assert r.verdict is Verdict.UNKNOWN
    bad = r.reasons_with(ReasonCode.BAD_RULE)
    assert bad and "number" in bad[0].detail


def test_evaluate_is_pure():
    p = Profile(age=30)
    first = evaluate(p, TWO_CRITERIA)
    for _ in range(5):
        assert evaluate(p, TWO_CRITERIA) == first
    assert p == Profile(age=30), "evaluate must not mutate the profile"


def test_sorting_puts_the_biggest_eligible_first():
    schemes = {
        "SMALL": scheme("SMALL", value=1000),
        "BIG": scheme("BIG", value=50000),
        "STUBBED": scheme("STUBBED", stubs=("x",)),
        "NO": scheme("NO", criteria=(Criterion("age", "between", [60, 90], "u",
                                               pass_hi="a", fail_hi="b"),)),
    }
    order = [r.scheme_code for r in evaluate_all(Profile(age=30), schemes)]
    assert order == ["BIG", "SMALL", "STUBBED", "NO"], order


def test_headline_metric_counts_only_what_the_worker_did_not_know():
    schemes = {"A": scheme("A", value=12000), "B": scheme("B", value=5000)}
    results = evaluate_all(Profile(age=30), schemes)
    assert newly_surfaced(results, known=frozenset()) == ("A", "B")
    assert newly_surfaced(results, known=frozenset({"A"})) == ("B",)
    assert total_value(results) == 17000
    assert total_value(results, only_codes=frozenset({"B"})) == 5000


def test_stub_value_inside_a_criterion_is_unknown_not_false():
    half = scheme(criteria=(Criterion("age", "between", [18, STUB], "u",
                                      pass_hi="a", fail_hi="b"),))
    # * The file has no stubs list set here, so this exercises the operator's own
    # * stub detection rather than the scheme-level short circuit.
    assert evaluate(Profile(age=30), half).verdict is Verdict.UNKNOWN


def test_engine_does_not_import_an_llm():
    # ! The rule that matters most, enforced as a test rather than a comment.
    # ! Importing the engine must not drag in the LLM module or any HTTP client.
    # * Checked by name, not by prefix: `urllib.parse` is pure string handling
    # * and some stdlib versions import it from pathlib. What must never appear
    # * is anything that can talk to a model or open a connection.
    code = (
        "import sys; import sathi.rules.engine;"
        "banned={'urllib.request','http.client','socket','ssl','anthropic','openai','requests'};"
        "bad=[m for m in sys.modules if m in banned or 'llm' in m.lower()];"
        "print(','.join(sorted(bad)))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert out == "", f"rules/ pulled in {out}"

    for path in (ROOT / "sathi" / "rules").glob("*.py"):
        source = path.read_text(encoding="utf-8")
        for banned in ("import llm", "render.llm", "anthropic", "openai", "requests"):
            assert banned not in source, f"{path.name} mentions {banned}"


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_rules.py OK")


if __name__ == "__main__":
    run()
