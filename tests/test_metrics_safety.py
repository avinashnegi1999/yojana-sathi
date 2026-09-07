"""Measurement regressions; check.py runs this without production data.

# ! Insurance, grants and future pension are different quantities.
# * Synthetic events exercise the real report and message renderers.
"""

import sys
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sathi.core.profile import Profile
from sathi.core.schemes import load_all
from sathi.metrics import report
from sathi.metrics.events import EventLog
from sathi.pack import pack
from sathi.render import templates
from sathi.rules.engine import evaluate_all

ROOT = Path(__file__).resolve().parents[1]


def test_one_time_value_cannot_become_annual_income():
    original = load_all(ROOT / "data/schemes")["PMSBY"]
    scheme = replace(original, code="TEST_GRANT", verified_by="synthetic test fixture",
                     benefit={**original.benefit, "annual_value_inr": 12345,
                              "value_basis": "one_time"})
    schemes = {scheme.code: scheme}
    results = evaluate_all(Profile(age=30, has_bank_account=True), schemes)
    assert results[0].is_eligible
    text = templates.result_message(results, schemes, frozenset(), "en")
    _, blob = pack.build(results, schemes, frozenset(), lang="en")
    annual = templates.s("result.value_line", "en", total="12,345")
    assert annual not in text and annual not in blob.decode()
    log = EventLog(":memory:")
    try:
        session = log.start_session()
        log.grant_consent(session)
        log.log(session, "scheme_newly_surfaced", scheme_code=scheme.code, value_inr=12345)
        with patch.object(report, "load_all", return_value=schemes):
            assert report.value_split(log._conn)["payout"] == 0
        assert "value_inr" not in report.numbers(log._conn), "mixed total still exposed"
    finally:
        log.close()


def test_report_labels_sessions_and_hides_rare_dimension_labels():
    log = EventLog(":memory:")
    try:
        session = log.start_session()
        log.grant_consent(session)
        log.log(session, "eligibility_evaluated", profile=Profile(state="UK"))
        page = report.render(log._conn, schemes_dir=ROOT / "data/schemes")
        assert "screening sessions evaluated" in page
        assert "distinct people" in page
        assert ">UK<" not in page
        assert "did not already know" not in page
    finally:
        log.close()


if __name__ == "__main__":
    for name, fn in sorted(list(globals().items())):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_metrics_safety.py OK")
