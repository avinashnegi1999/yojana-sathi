"""Turn engine Results into Hindi a worker can hear.

# ! Every sentence here comes from data/strings_hi.toml or from a scheme's own
# ! authored pass_hi / fail_hi / reason_hi. This module concatenates and
# ! formats. It never writes a sentence, never invents a ₹ figure, and never
# ! decides a verdict — by the time a Result reaches here, the decision is made.
#
# * The templated path is the DEFAULT, not the fallback. With LLM_API_KEY unset
# * this is the entire output layer and the result text is identical.
"""

from sathi.core import content
from sathi.core.content import s
from sathi.core.schemes import STUB, Scheme
from sathi.rules.engine import ReasonCode, Result, Verdict


def rupees(n: int) -> str:
    """Indian digit grouping: 1234567 -> '12,34,567'. Last three, then pairs."""
    digits = str(abs(int(n)))
    if len(digits) <= 3:
        out = digits
    else:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        out = ",".join(parts) + "," + tail
    return ("-" if n < 0 else "") + out


def field_label(field: str, lang: str = "hi") -> str:
    return s(f"field_labels.{field}", lang)


def where_label(scheme: Scheme, lang: str = "hi") -> str:
    """paperwork.where_to_apply in words. An unresearched location says so."""
    if scheme.where_to_apply == STUB or not scheme.where_to_apply:
        return s("where.unknown", lang)
    try:
        return s(f"where.{scheme.where_to_apply}", lang)
    except content.ContentError:
        # * The loader restricts this to a known set, so we only get here if a
        # * location was added to schemes.py without a label.
        return s("where.unknown", lang)


def _why(result: Result, scheme: Scheme, lang: str = "hi", limit: int = 2) -> str:
    """The authored 'you qualify because…' lines, joined. Never generated.

    # * The Result carries the Hindi it was decided with; the English twin lives
    # * on the Criterion. Matched by field name, which is unique per criterion in
    # * every file we have. Falls back to the Hindi text if no English exists.
    """
    by_field = {c.field: c for c in scheme.criteria}
    lines = []
    for r in result.reasons_with(ReasonCode.CRITERION_PASS):
        c = by_field.get(r.field)
        text = c.text("pass", lang) if c else r.text_hi
        if text:
            lines.append(text)
    joiner = " " if lang == "en" else "। "
    return joiner.join(lines[:limit])


def _blocking_text(result: Result, scheme: Scheme, lang: str = "hi") -> str:
    """The authored reason a worker did not qualify, in their language."""
    reason = result.blocking_reason
    if reason is None:
        return ""
    if reason.code is ReasonCode.EXCLUDED:
        c = next((e for e in scheme.exclusions if e.field == reason.field), None)
        return c.text("reason", lang) if c else reason.text_hi
    c = next((x for x in scheme.criteria if x.field == reason.field), None)
    return c.text("fail", lang) if c else reason.text_hi


def _gap(result: Result, scheme: Scheme, lang: str = "hi") -> str:
    """Why a scheme came out UNKNOWN, in one phrase."""
    if result.unverified:
        # ! The engine carries ONE flag for two different admissions, because
        # ! neither one may produce a verdict. The worker is owed the difference:
        # ! "nobody has looked this up" and "one person looked it up and is
        # ! waiting on a second" are not the same sentence, and the first is a
        # ! lie once the file is researched. Scheme.is_researched is the split.
        key = "unknown_reason_unsigned" if scheme.is_researched else "unknown_reason_data"
        return s(f"result.{key}", lang)
    if result.missing_fields:
        return s(
            "result.unknown_reason_profile", lang,
            fields=", ".join(field_label(f, lang) for f in result.missing_fields),
        )
    # * BAD_RULE: a scheme file is broken. The worker gets the honest version;
    # * the detail goes to the logs for a maintainer, not to the screen.
    return s("result.unknown_reason_data", lang)


def eligible_block(results: tuple[Result, ...], schemes: dict[str, Scheme],
                   known: frozenset[str], lang: str = "hi") -> str:
    hits = [r for r in results if r.verdict is Verdict.ELIGIBLE]
    if not hits:
        return ""
    lines = [s("result.eligible_header", lang, count=len(hits))]
    for i, r in enumerate(hits, start=1):
        sc = schemes[r.scheme_code]
        lines.append(
            s(
                "result.scheme_line", lang,
                index=i,
                name_hi=sc.name(lang),
                new_badge=s("result.new_badge", lang) if r.scheme_code not in known else "",
                benefit=sc.summary(lang),
                why=_why(r, sc, lang),
                where=where_label(sc, lang),
            )
        )
    # ! Two different kinds of money, never added together. A pension is what
    # ! arrives every year; a cover is what is paid only if something happens.
    # ! One number for both would overstate a worker's position by lakhs.
    payout = sum(r.annual_value_inr for r in hits if r.value_basis != "insurance_cover")
    cover = sum(r.annual_value_inr for r in hits if r.value_basis == "insurance_cover")
    if payout:
        lines.append(s("result.value_line", lang, total=rupees(payout)))
    if cover:
        # * "On top of that" only makes sense when there IS something above it.
        key = "result.cover_line" if payout else "result.cover_only_line"
        lines.append(s(key, lang, total=rupees(cover)))
    if payout or cover:
        # ! The caveat ships with the number, every time, in the product and not
        # ! only in the README. "Surfaced", never "delivered".
        lines.append(s("result.value_caveat", lang))
    return "\n\n".join(lines)


def unknown_block(results: tuple[Result, ...], schemes: dict[str, Scheme],
                  lang: str = "hi") -> str:
    hits = [r for r in results if r.verdict is Verdict.UNKNOWN]
    if not hits:
        return ""
    lines = [s("result.unknown_header", lang, count=len(hits))]
    gaps = [_gap(r, schemes[r.scheme_code], lang) for r in hits]

    # ! One reason, said once. Today every scheme is unsure for the same reason
    # ! — nobody has signed the values off — so the per-scheme version printed
    # ! the identical sentence three times and pushed the actionable line, the
    # ! question to ask at the centre, out of sight on a phone.
    if len(hits) > 1 and len(set(gaps)) == 1:
        lines.append(s("result.unknown_shared", lang, gap=gaps[0]))
        lines.extend(s("result.unknown_line_bare", lang, name_hi=schemes[r.scheme_code].name(lang))
                     for r in hits)
        return "\n\n".join(lines[:2]) + "\n" + "\n".join(lines[2:])

    for r, gap in zip(hits, gaps):
        lines.append(s("result.unknown_line", lang, name_hi=schemes[r.scheme_code].name(lang), gap=gap))
    return "\n\n".join(lines)


def ineligible_block(results: tuple[Result, ...], schemes: dict[str, Scheme],
                     lang: str = "hi") -> str:
    hits = [r for r in results if r.verdict is Verdict.INELIGIBLE]
    if not hits:
        return ""
    lines = [s("result.ineligible_header", lang)]
    for r in hits:
        sc = schemes[r.scheme_code]
        lines.append(
            s(
                "result.ineligible_line", lang,
                name_hi=sc.name(lang),
                # * The reason is authored per criterion and says what to do
                # * instead. If a file has none yet, say nothing rather than
                # * inventing a reason.
                reason=_blocking_text(r, sc, lang),
            ).rstrip(" —")
        )
    return "\n".join(lines)


def no_match_block(results: tuple[Result, ...], schemes: dict[str, Scheme],
                   lang: str = "hi") -> str:
    """Shown when nothing is ELIGIBLE. A dead end is never an acceptable output.

    Nearest miss = the ineligible scheme whose own authored fail_hi explains the
    single thing standing in the way.
    """
    lines = [s("result.no_match_header", lang)]
    near = next(
        (r for r in results if r.verdict is Verdict.INELIGIBLE and r.blocking_reason
         and r.blocking_reason.text_hi),
        None,
    )
    if near is not None:
        sc = schemes[near.scheme_code]
        lines.append(
            s("result.near_miss", lang, name_hi=sc.name(lang),
              reason=_blocking_text(near, sc, lang))
        )
    lines.append(s("result.no_match_footer", lang))
    return "\n\n".join(lines)


def result_message(results: tuple[Result, ...], schemes: dict[str, Scheme],
                   known: frozenset[str], lang: str = "hi") -> str:
    """The whole result screen, in order: good news, honest gaps, then the rest."""
    blocks = []
    eligible = eligible_block(results, schemes, known, lang)
    if eligible:
        blocks.append(eligible)
    else:
        blocks.append(no_match_block(results, schemes, lang))
    for block in (unknown_block(results, schemes, lang),
                  ineligible_block(results, schemes, lang)):
        if block:
            blocks.append(block)
    return "\n\n".join(blocks)


def documents_block(scheme: Scheme, missing: tuple[str, ...] = (), lang: str = "hi") -> str:
    lines = [s("documents.header", lang, name_hi=scheme.name(lang))]
    lines += [s("documents.line", lang, doc=d) for d in scheme.docs(lang)]
    if missing:
        lines.append(s("documents.missing_header", lang))
        lines += [s("documents.missing_line", lang, doc=d, how=s("documents.how_generic", lang))
                  for d in missing]
    else:
        lines.append(s("documents.have_all", lang))
    return "\n".join(lines)


def _self_check() -> None:
    from dataclasses import replace

    from sathi.core.profile import Profile, PROFILE_FIELDS
    from sathi.core.schemes import Criterion as C
    from sathi.rules.engine import evaluate_all

    assert rupees(1234567) == "12,34,567", rupees(1234567)
    assert rupees(12000) == "12,000"
    assert rupees(500) == "500"

    # ! Every profile field needs a Hindi label, or a worker gets told a gap in
    # ! English (or a KeyError) at the worst possible moment.
    for f in PROFILE_FIELDS:
        assert field_label(f), f

    def scheme(code, value, crit_value, **kw):
        base = dict(
            code=code, name_en=code, name_hi=f"योजना-{code}", authority="A",
            official_url="u", verified_on="2026-09-01", verified_by="a",
            benefit={"annual_value_inr": value, "value_basis": "annual_payout",
                     "summary_hi": "हर साल पैसा"},
            criteria=(C("age", "between", crit_value, "u",
                        pass_hi="उम्र सही है", fail_hi="उम्र इस योजना के दायरे से बाहर है"),),
            exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
        )
        base.update(kw)
        return Scheme(**base)

    schemes = {
        "A": scheme("A", 12000, [18, 40]),
        "B": scheme("B", 5000, [60, 90]),
        "C": scheme("C", 0, [18, 40], stubs=("benefit.annual_value_inr",)),
    }
    # * D is an insurance cover, A is an annual payout. They must never be summed.
    schemes["D"] = scheme("D", 200000, [18, 40])
    schemes["D"] = replace(
        schemes["D"], benefit={**schemes["D"].benefit, "value_basis": "insurance_cover"}
    )
    results = evaluate_all(Profile(age=30), schemes)
    text = result_message(results, schemes, known=frozenset({"A"}))
    assert "योजना-A" in text and "12,000" in text
    assert "2,00,000" in text, "the cover must be stated"
    assert "2,12,000" not in text, "a cover was added to a payout"
    a_line = next(l for l in text.splitlines() if "योजना-A" in l)
    assert s("result.new_badge") not in a_line, "A is already known — no badge"
    assert "पैसा अभी मिला नहीं" in text, "the surfaced-not-delivered caveat must always ship"
    # ! C is unresearched (a stub); E is researched but unsigned. They must not
    # ! give a worker the same sentence — that conflation shipped once already.
    assert "योजना-C" in text and s("result.unknown_reason_data") in text
    unsigned = {"E": replace(scheme("E", 9000, [18, 40]),
                             verified_by="unconfirmed — PENDING HUMAN VERIFICATION")}
    assert not unsigned["E"].is_human_verified and unsigned["E"].is_researched
    text_unsigned = result_message(evaluate_all(Profile(age=30), unsigned), unsigned, frozenset())
    assert s("result.unknown_reason_unsigned") in text_unsigned, text_unsigned

    # ! Three schemes, one shared reason: the sentence appears once, and every
    # ! scheme still carries its own question to ask at the centre.
    many = {c: replace(scheme(c, 9000, [18, 40]),
                       verified_by="unconfirmed — PENDING HUMAN VERIFICATION")
            for c in ("X", "Y", "Z")}
    shared = result_message(evaluate_all(Profile(age=30), many), many, frozenset())
    assert shared.count(s("result.unknown_reason_unsigned")) == 1, shared
    for c in ("X", "Y", "Z"):
        assert f"योजना-{c}" in shared
    assert s("result.unknown_reason_data") not in text_unsigned, \
        "a researched scheme must not claim nobody checked its source"
    assert "उम्र इस योजना के दायरे से बाहर" in text, "ineligible reason must be the authored one"
    assert "{" not in text, "unfilled placeholder reached the worker"

    # ! Insurance alone must not say "on top of that" with nothing above it —
    # ! the exact sentence a real pack shipped with when only PMSBY matched.
    cover_only = {"D": schemes["D"]}
    text_cover = result_message(evaluate_all(Profile(age=30), cover_only), cover_only, frozenset())
    assert s("result.cover_only_line", "hi").split("{")[0][:12] in text_cover, text_cover
    assert "इसके अलावा" not in text_cover, "cover-only result still says 'on top of that'"

    # * Nobody eligible → never a dead end.
    none_text = result_message(evaluate_all(Profile(age=50), schemes), schemes, frozenset())
    assert s("result.no_match_footer") in none_text
    assert documents_block(schemes["A"], missing=("आधार",)).count("आधार") >= 2
    print("templates.py OK")


if __name__ == "__main__":
    _self_check()
