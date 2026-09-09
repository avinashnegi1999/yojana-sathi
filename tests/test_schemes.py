"""Scheme loader checks. Run: python3 tests/test_schemes.py

# * A validator nobody tested is a validator that passes everything. Each case
# * below is a mistake a human will actually make while authoring a rule file.
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sathi.core.profile import Profile
from sathi.core.schemes import (
    PENDING_MARKER,
    STUB,
    SchemeError,
    load_all,
    load_scheme,
)
from sathi.rules.engine import Verdict, evaluate

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


def _unsigned(text: str) -> str:
    """The same file with its signature taken off — researched, not signed."""
    return text.replace(
        'verified_by  = "avinash"',
        f'verified_by  = "unconfirmed — {PENDING_MARKER}"',
    )


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
    assert s.is_researched, f"no stubs expected, got {s.stubs}"
    assert s.annual_value_inr() == 12000
    assert s.criteria[0].op == "between" and s.criteria[0].value == [18, 40]
    assert s.exclusions[0].reason_hi == "आयकर"
    assert s.documents == ("Aadhaar", "Bank passbook")


def test_stub_marks_unverified_but_still_loads():
    # ! The whole anti-hallucination mechanism. An unresearched threshold must
    # ! load and be flagged, never crash and never silently default to a number.
    s = _load(GOOD.replace("value      = [18, 40]", f'value      = "{STUB}"'))
    assert not s.is_researched
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


def test_rejects_unsummable_basis_carrying_money():
    # ! A basis outside the payout/cover split is counted nowhere. Silent zero
    # ! is worse than a load failure, because nobody goes looking for it.
    for basis in ("one_time", "subsidy", "gateway", "in_kind"):
        _rejects(GOOD.replace('value_basis      = "annual_payout"',
                              f'value_basis      = "{basis}"'),
                 "no total sums that basis")
    # * The same basis at ₹0 is legitimate — e-Shram is exactly this.
    ok = _load(GOOD.replace('value_basis      = "annual_payout"',
                            'value_basis      = "gateway"')
                   .replace("annual_value_inr = 12000", "annual_value_inr = 0"))
    assert ok.annual_value_inr() == 0


def test_rejects_bad_apply_location():
    _rejects(GOOD.replace('where_to_apply = "csc"', 'where_to_apply = "somewhere"'),
             "where_to_apply")


def test_rejects_empty_documents():
    _rejects(GOOD.replace('documents      = ["Aadhaar", "Bank passbook"]',
                          "documents      = []"),
             "non-empty documents")


# ! Every "TODO" still left in a real scheme file, and why. Adding a line here
# ! is a deliberate act with a reason attached; the test above refuses any stub
# ! that is not on this list.
KNOWN_STUBS = ()  # ! nothing outstanding; add a line here with its reason, never a bare TODO


def test_documented_stubs_are_actually_still_stubbed():
    """A stub that gets researched must leave KNOWN_STUBS, or the list rots."""
    root = Path(__file__).resolve().parent.parent
    schemes = load_all(root / "data" / "schemes")
    for code, path in KNOWN_STUBS:
        assert code in schemes, f"KNOWN_STUBS names {code}, which no longer exists"
        assert path in schemes[code].stubs, (
            f"{code}.{path} is no longer a stub — delete its KNOWN_STUBS line"
        )


def test_real_scheme_files_are_structurally_valid():
    root = Path(__file__).resolve().parent.parent
    schemes = load_all(root / "data" / "schemes")
    assert set(schemes) == {"ESHRAM", "PM_SYM", "PMSBY", "PMJJBY", "UK_OLD_AGE", "UK_WIDOW", "PMUY"}, sorted(schemes)
    for code, s in schemes.items():
        assert s.source_path.endswith(".toml")
        # ! Not "no stubs" any more, but "no stub nobody wrote down". Every
        # ! remaining TODO must appear in KNOWN_STUBS with a reason, so a value
        # ! that quietly goes missing still fails this test. Withdrawing an
        # ! unsourceable number to "TODO" is the correct move (rule 3); leaving
        # ! it undocumented is not.
        unrecorded = set(s.stubs) - {path for c, path in KNOWN_STUBS if c == code}
        assert not unrecorded, f"{code} has undocumented unresearched values: {sorted(unrecorded)}"
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


def test_every_shipped_signature_is_a_real_person_or_no_signature_at_all():
    """A scheme is either honestly unsigned, or signed by a nameable human.

    # ! This replaced a test that asserted every file was still unsigned. That
    # ! version was correct while nothing was signed and became a trap the
    # ! moment anything was: signing a file would fail the build, and the
    # ! obvious way to get a green build is to delete the test — which is
    # ! precisely the safety net going away at the moment it starts to matter.
    #
    # ! What actually matters is that the two states never blur. Either the
    # ! file admits nobody has checked it and the engine serves UNKNOWN, or a
    # ! named person owns every value in it and the engine serves verdicts.
    # ! `sathi/review.py` is the only supported way to move between them, and
    # ! the name is held to the same standard that tool enforces, so nobody can
    # ! hand-edit `verified_by = "auto"` and get real verdicts out.
    """
    from sathi.review import ReviewError, check_name

    root = Path(__file__).resolve().parent.parent
    for code, sc in load_all(root / "data" / "schemes").items():
        if PENDING_MARKER in sc.verified_by:
            assert not sc.is_human_verified, code
            assert not sc.is_servable, f"{code}: pending, but the engine would serve it"
            continue
        assert sc.is_researched, \
            f"{code} carries a signature but still has TODOs: {sc.stubs}"
        signer = sc.verified_by.split(", checked")[0]
        try:
            check_name(signer)
        except ReviewError as e:
            raise AssertionError(f"{code}: {e}") from None


# ! Which schemes a named human has signed off, and therefore which ones give
# ! real verdicts to real people. Adding a line here is a claim the README, the
# ! checkpoint and the submission draft all repeat, so they change together.
SIGNED_OFF = ("PMJJBY", "PMSBY")  # Avinash Negi, 2026-09-09, against financialservices.gov.in


def test_the_signed_list_matches_the_files():
    """The live state, stated once so a change to it is deliberate and visible.

    # ! Not a safety invariant — the test above is. This one is a tripwire on a
    # ! fact three documents assert: exactly who has been given a verdict and
    # ! on what. It fires in both directions, so an unnoticed signature and an
    # ! unnoticed un-signing are both build failures.
    """
    root = Path(__file__).resolve().parent.parent
    signed = tuple(sorted(code for code, sc in load_all(root / "data" / "schemes").items()
                          if sc.is_human_verified))
    assert signed == tuple(sorted(SIGNED_OFF)), (
        f"signed schemes are {signed}, this list says {tuple(sorted(SIGNED_OFF))}. "
        f"That is a real change in what this bot tells people. Update README.md, "
        f"docs/CHECKPOINT_2026-09-09.md and docs/SUBMISSION_DRAFT.md, then fix "
        f"this list."
    )


# =====================================================================
# THE VERIFICATION GATE
# =====================================================================
# ! These are the invariants, not conveniences. The bug they exist to prevent:
# ! the app once treated "no TODO left" as "verified", so a file reading
# ! `verified_by = "unconfirmed — PENDING HUMAN VERIFICATION"` printed as
# ! "verified 2026-08-31" at startup and served real ELIGIBLE verdicts. The
# ! README told people not to use it on real workers; the runtime did not.
# ! Never delete a test in this block to make a build pass.


def test_researched_is_not_the_same_as_signed_off():
    s = _load(_unsigned(GOOD))
    assert s.is_researched, "no TODO left, so research really is complete"
    assert not s.is_human_verified, "nobody signed it"
    assert not s.is_servable, "and therefore the engine may not use it"


def test_blank_or_stub_signature_is_not_a_signature():
    # * "TODO" loads — it is the normal state of a half-authored file — but it
    # * is not a signature, so the scheme stays unservable.
    assert not _load(GOOD.replace(
        'verified_by  = "avinash"', f'verified_by  = "{STUB}"')).is_human_verified
    # * A whitespace-only signature never even loads: the loader treats it as
    # * the empty string. Checked here so the two layers cannot drift apart.
    _rejects(GOOD.replace('verified_by  = "avinash"', 'verified_by  = " "'),
             "expected a non-empty string")


def test_unsigned_scheme_never_produces_a_verdict():
    # ! Not even a NO. "We have not checked this yet" is the only honest answer,
    # ! and turning a worker away on unchecked data is the expensive mistake.
    s = _load(_unsigned(GOOD))
    # ! Two of these are fully answered, so an UNKNOWN here can only come from
    # ! the gate. Without them the test would pass for the wrong reason.
    for profile in (Profile(age=30, is_income_tax_payer=False),   # would be ELIGIBLE
                    Profile(age=99, is_income_tax_payer=True),    # would be INELIGIBLE
                    Profile()):                                   # genuinely unknown
        r = evaluate(profile, s)
        assert r.verdict is Verdict.UNKNOWN, f"{profile} got {r.verdict}"
        assert r.unverified and r.annual_value_inr == 0


def test_signed_scheme_does_produce_a_verdict():
    # * The gate has to be a gate, not a wall: a signed file still decides.
    s = _load(GOOD)
    assert s.is_servable
    # * GOOD asks two things: age 18-40, and not an income-tax payer. Answer
    # * both, or the result is UNKNOWN for the ordinary reason and proves nothing.
    answered = Profile(age=30, is_income_tax_payer=False)
    assert evaluate(answered, s).verdict is Verdict.ELIGIBLE
    assert evaluate(Profile(age=55, is_income_tax_payer=False), s).verdict \
        is Verdict.INELIGIBLE


def test_no_shipped_scheme_is_servable_while_sign_off_is_pending():
    # ! The end-to-end version of the invariant, on the real files. While the
    # ! test above holds, this one must hold too — every shipped scheme reaches
    # ! a worker as UNKNOWN. Both flip together on the day someone signs off.
    root = Path(__file__).resolve().parent.parent
    for code, s in load_all(root / "data" / "schemes").items():
        if s.is_human_verified:
            continue  # signed on purpose; the test above vouches for the name
        assert not s.is_servable, f"{code} is servable but sign-off is pending"
        assert evaluate(Profile(age=30), s).verdict is Verdict.UNKNOWN, code


def test_rejects_nonfinite_boolean_and_reversed_thresholds():
    for value in ("[18, nan]", "[18, inf]", "[true, 40]", "[40, 18]"):
        _rejects(GOOD.replace("value      = [18, 40]", f"value      = {value}"),
                 "between")


def test_rejects_negative_or_boolean_money():
    for value in ("-1", "true"):
        _rejects(GOOD.replace("annual_value_inr = 12000", f"annual_value_inr = {value}"),
                 "annual_value_inr")


def test_unsigned_scheme_value_accessor_returns_zero():
    assert _load(_unsigned(GOOD)).annual_value_inr() == 0


def test_eshram_does_not_promise_automatic_insurance():
    root = Path(__file__).resolve().parent.parent
    sc = load_all(root / "data" / "schemes")["ESHRAM"]
    assert "PMSBY" not in sc.summary("en")
    assert "पहले साल का प्रीमियम" not in sc.summary("hi")


def test_large_integer_threshold_loads_without_float_overflow():
    large = 10 ** 400
    sc = _load(GOOD.replace("value      = [18, 40]", f"value      = [18, {large}]"))
    assert sc.criteria[0].value == [18, large]


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_schemes.py OK")


if __name__ == "__main__":
    run()
