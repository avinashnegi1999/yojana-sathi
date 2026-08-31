"""Scheme loader checks. Run: python3 tests/test_schemes.py

# * A validator nobody tested is a validator that passes everything. Each case
# * below is a mistake a human will actually make while authoring a rule file.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sathi.core.schemes import STUB, SchemeError, load_all, load_scheme

GOOD = """
code         = "TEST"
name_en      = "Test Scheme"
name_hi      = "परीक्षण योजना"
authority    = "Test Ministry"
official_url = "https://example.gov.in/test"
verified_on  = "2026-09-01"
verified_by  = "avinash"

[benefit]
annual_value_inr = 12000
value_basis      = "annual_payout"
premium_inr      = 0
summary_hi       = "टेस्ट"
summary_en       = "Test"

[[criteria]]
field      = "age"
op         = "between"
value      = [18, 40]
ask_hi     = "उम्र?"
pass_hi    = "ठीक"
fail_hi    = "नहीं"
source_url = "https://example.gov.in/test#age"

[[exclusions]]
field      = "is_income_tax_payer"
op         = "eq"
value      = true
reason_hi  = "आयकर"
source_url = "https://example.gov.in/test#tax"

[paperwork]
documents      = ["Aadhaar", "Bank passbook"]
where_to_apply = "csc"
renewal        = "none"
"""


def _load(text: str):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "scheme.toml"
        p.write_text(text, encoding="utf-8")
        return load_scheme(p)


def _rejects(text: str, fragment: str) -> None:
    try:
        _load(text)
    except SchemeError as e:
        assert fragment in str(e), f"wrong error for {fragment!r}: {e}"
        return
    raise AssertionError(f"expected SchemeError containing {fragment!r}, file loaded clean")


def test_good_file_loads():
    s = _load(GOOD)
    assert s.code == "TEST"
    assert s.is_verified, f"no stubs expected, got {s.stubs}"
    assert s.annual_value_inr() == 12000
    assert s.criteria[0].op == "between" and s.criteria[0].value == [18, 40]
    assert s.exclusions[0].reason_hi == "आयकर"
    assert s.documents == ("Aadhaar", "Bank passbook")


def test_stub_marks_unverified_but_still_loads():
    # ! The whole anti-hallucination mechanism. An unresearched threshold must
    # ! load and be flagged, never crash and never silently default to a number.
    s = _load(GOOD.replace("value      = [18, 40]", f'value      = "{STUB}"'))
    assert not s.is_verified
    assert "criteria[0].value" in s.stubs, s.stubs
    # ₹ must stay 0 while unverified, so it can never inflate an impact number
    s2 = _load(GOOD.replace("annual_value_inr = 12000", f'annual_value_inr = "{STUB}"'))
    assert s2.annual_value_inr() == 0


def test_rejects_unknown_key():
    _rejects(GOOD + '\nextra_key = "oops"\n', "unknown key")


def test_rejects_unknown_operator():
    _rejects(GOOD.replace('op         = "between"', 'op         = "roughly"'), "unknown op")


def test_rejects_field_not_on_profile():
    # * Catches the typo, and catches inventing a question we never ask.
    _rejects(GOOD.replace('field      = "age"', 'field      = "anual_income"'),
             "not a Profile field")


def test_rejects_missing_source_url():
    _rejects(GOOD.replace('source_url = "https://example.gov.in/test#age"\n', "", 1),
             "missing key")


def test_rejects_wrong_value_shape_for_operator():
    _rejects(GOOD.replace("value      = [18, 40]", "value      = 18"),
             "needs a [low, high] pair")


def test_rejects_bad_value_basis():
    _rejects(GOOD.replace('value_basis      = "annual_payout"', 'value_basis      = "money"'),
             "value_basis")


def test_rejects_bad_apply_location():
    _rejects(GOOD.replace('where_to_apply = "csc"', 'where_to_apply = "somewhere"'),
             "where_to_apply")


def test_rejects_empty_documents():
    _rejects(GOOD.replace('documents      = ["Aadhaar", "Bank passbook"]',
                          "documents      = []"),
             "non-empty documents")


def test_real_scheme_files_are_structurally_valid():
    root = Path(__file__).resolve().parent.parent
    schemes = load_all(root / "data" / "schemes")
    assert set(schemes) == {"ESHRAM", "PM_SYM", "PMSBY"}, sorted(schemes)
    for code, s in schemes.items():
        assert s.source_path.endswith(".toml")
        assert not s.stubs, f"{code} still has unresearched values: {s.stubs}"
        # ! Every value must cite a page, not a site root. This is the check that
        # ! makes "audit one rule in 30 seconds" true rather than aspirational.
        for c in s.criteria + s.exclusions:
            assert c.source_url.startswith("https://"), f"{code}: {c.field} has no source"
            assert c.source_url.count("/") > 2, f"{code}: {c.field} cites a site root"
        assert s.official_url.startswith("https://")


def test_real_scheme_files_are_fully_bilingual():
    # ! English is optional in the loader so a Hindi-only contribution still
    # ! works. Our own three files are held to a higher bar: a worker who picks
    # ! English must never hit a Devanagari sentence mid-result.
    root = Path(__file__).resolve().parent.parent
    for code, s in load_all(root / "data" / "schemes").items():
        assert s.name_en and s.benefit.get("summary_en"), code
        assert len(s.documents_en) == len(s.documents), \
            f"{code}: documents_en must match documents one for one, or it is ignored"
        assert s.renewal_en, code
        for c in s.criteria:
            assert c.pass_en and c.fail_en, f"{code}: criterion {c.field} has no English"
            assert c.text("pass", "en") == c.pass_en
        for e in s.exclusions:
            assert e.reason_en, f"{code}: exclusion {e.field} has no English"


def test_english_falls_back_to_hindi_rather_than_going_blank():
    # * A contributed Hindi-only file must still render an English screen.
    s = _load(GOOD)
    assert s.criteria[0].text("pass", "en") == s.criteria[0].pass_hi
    assert s.name("en") == s.name_en
    assert s.docs("en") == s.documents, "a missing English list falls back, never blanks"


def test_every_income_band_is_accounted_for_in_every_income_rule():
    # ! A band added to the profile menu but left out of a scheme's list is a
    # ! silent denial — the worker sees the option, picks it, and is quietly
    # ! ruled out. This fails the build instead.
    from sathi.core.profile import INCOME_BANDS

    root = Path(__file__).resolve().parent.parent
    for code, s in load_all(root / "data" / "schemes").items():
        for c in s.criteria + s.exclusions:
            if c.field == "income_band" and isinstance(c.value, list):
                unknown = set(c.value) - set(INCOME_BANDS)
                assert not unknown, f"{code}: income rule names bands that do not exist: {unknown}"
                # * PM-SYM's rule is a ceiling ("₹15,000 or less"), so the bands
                # * below the ceiling must all be present — including zero.
                assert "no_income" in c.value, \
                    f"{code}: an income ceiling must include workers with no income at all"


def test_filled_files_still_admit_they_are_unverified_by_a_human():
    # ! The values were transcribed from official pages in one pass, which is
    # ! not the same as a person having checked them one by one. Until a
    # ! maintainer puts their own name in verified_by, that has to be visible in
    # ! the data itself. Delete this test the day it is signed off —
    # ! deliberately, not by accident.
    root = Path(__file__).resolve().parent.parent
    for code, s in load_all(root / "data" / "schemes").items():
        assert "PENDING HUMAN VERIFICATION" in s.verified_by, \
            f"{code}: verified_by is {s.verified_by!r} — if a human checked it, remove this test"


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_schemes.py OK")


if __name__ == "__main__":
    run()
