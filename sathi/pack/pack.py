"""The application pack: one page the worker carries into the centre.

# ! Built in memory and handed to the worker. It is never written to disk on the
# ! server — there is no packs/ directory in production and no cleanup job to
# ! forget to run.
#
# ! It contains NO personal detail. Not because we strip it, but because we
# ! never asked: there is no name, phone or Aadhaar anywhere in this project.
# ! What it carries is the list, the questions to ask, and what to bring.
#
# * HTML, not PDF. The stdlib has no PDF writer and the plan's rule is that a
# * dependency needs a reason the stdlib cannot cover. A phone opens this file
# * and prints it; a CSC operator opens it on a laptop. If week-7 users show
# * that a real PDF matters, fpdf2 is the smallest addition — not before.
"""

import html
from datetime import date

from sathi.core.content import s
from sathi.core.schemes import Scheme
from sathi.pack import checklist
from sathi.render import templates
from sathi.rules import engine
from sathi.rules.engine import Result, Verdict

# * Same Apple-inspired language as the browser page (sathi/local_web.py):
# * parchment canvas, near-black ink, one blue, system fonts, white 18px cards
# * with a hairline, no shadows, no gradients. White background and 12pt type
# * when printed, and no card is split across a page.
_CSS = """
:root{--ink:#1d1d1f;--body:#333333;--muted:#6e6e73;--blue:#0066cc;--canvas:#ffffff;--parchment:#f5f5f7;--hairline:#e0e0e0}
*{box-sizing:border-box}
body{margin:0;background:var(--parchment);color:var(--ink);font:400 17px/1.47 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans Devanagari","Nirmala UI",sans-serif;-webkit-font-smoothing:antialiased}
html[lang=hi] body{line-height:1.6}
main{max-width:44rem;margin:0 auto;padding:40px 16px 64px}
.brand{margin:0;color:var(--muted);font-size:14px}
h1{margin:6px 0 6px;font-size:32px;font-weight:600;line-height:1.2;letter-spacing:-.01em}
.sub{margin:0 0 28px;color:var(--muted)}
.card{background:var(--canvas);border:1px solid var(--hairline);border-radius:18px;padding:20px 22px;margin:0 0 14px;break-inside:avoid}
h2{margin:0 0 10px;font-size:19px;font-weight:600;line-height:1.35}
.tag{display:inline-block;margin-left:6px;padding:1px 10px;border-radius:999px;background:#e8f1fb;color:var(--blue);font-size:13px;font-weight:600;vertical-align:middle}
.glance{width:100%;border-collapse:collapse}
.glance td{padding:10px 0;border-top:1px solid var(--hairline);vertical-align:top}
.glance tr:first-child td{border-top:0}
.glance td.where{padding-left:16px;text-align:right;color:var(--muted)}
.hide{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.money{margin:12px 0 0;padding-top:12px;border-top:1px solid var(--hairline)}
.money p{margin:0 0 4px}
.money .caveat{margin-top:8px;font-weight:600}
.lead{margin:0 0 6px;font-weight:600}
.more{margin:0 0 14px;color:var(--muted);font-size:15px}
.row{display:flex;gap:12px;padding:9px 0;border-top:1px solid var(--hairline)}
.row .k{flex:0 0 7.5rem;color:var(--muted);font-size:15px}
.row .v{flex:1}
.checks-title{margin:14px 0 4px;color:var(--muted);font-size:15px}
.checks{list-style:none;margin:0;padding:0}
.checks li{padding:5px 0}
.box{display:inline-block;width:1.6em;color:var(--muted)}
.have .box{color:var(--blue)}
.section{margin:32px 0 12px;font-size:21px;font-weight:600;white-space:pre-line}
.quiet{margin:0;padding:0;list-style:none;color:var(--body);font-size:15px}
.quiet li{padding:8px 0;border-top:1px solid var(--hairline)}
.quiet li:first-child{border-top:0}
.quiet .why{color:var(--muted)}
.note{margin:0 0 10px;color:var(--muted);font-size:15px}
.answers{margin:0;padding:0;list-style:none;columns:2;column-gap:28px;font-size:15px;color:var(--body)}
.answers li{padding:3px 0;break-inside:avoid}
.foot{margin-top:36px;color:var(--muted);font-size:13px}
@media(max-width:520px){h1{font-size:28px}.answers{columns:1}.row .k{flex-basis:6rem}.glance td{display:block}.glance td.where{padding:0 0 10px;border-top:0;text-align:left}}
@media print{body{background:#fff;font-size:12pt}main{max-width:none;padding:0}.card{border-color:#cccccc}}
"""


def _e(text: object) -> str:
    return html.escape(str(text), quote=False).replace("\n", "<br>")


def _row(label: str, value: str) -> str:
    # * The ": " is hidden on screen (the label column already reads as a
    # * label) but kept in the text WhatsApp gets, which has no columns.
    return (f"<div class='row'><span class='k'>{_e(label)}<span class='hide'>: </span></span>"
            f"<span class='v'>{_e(value)}</span></div>")


def build(
    results: tuple[Result, ...],
    schemes: dict[str, Scheme],
    known: frozenset[str],
    have_docs: frozenset[str] = frozenset(),
    today: date | None = None,
    lang: str = "hi",
    recap: str = "",
) -> tuple[str, bytes]:
    """Return (filename, bytes). Nothing touches the filesystem."""
    eligible = [r for r in results if r.verdict is Verdict.ELIGIBLE]
    unknown = [r for r in results if r.verdict is Verdict.UNKNOWN]
    ineligible = [r for r in results if r.verdict is Verdict.INELIGIBLE]
    stamp = (today or date.today()).isoformat()

    parts = [
        f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>{_e(s('pack.title', lang))}</title><style>{_CSS}</style></head><body><main>",
        f"<p class='brand'>{_e(s('pack.brand', lang))} · {_e(stamp)}</p>",
        f"<h1>{_e(s('pack.heading', lang))}</h1>",
        f"<p class='sub'>{_e(s('pack.subtitle', lang))}</p>",
    ]

    # ! The whole plan first: where to walk, and what the money is. A worker
    # ! opening this on a phone should not scroll past paragraphs of insurance
    # ! terms to find the one thing she can act on today.
    if eligible:
        parts.append(f"<div class='card'><h2>{_e(s('pack.at_a_glance', lang))}</h2><table class='glance'>")
        for r in eligible:
            sc = schemes[r.scheme_code]
            # * The hidden arrow keeps "name → place" on one line in the text
            # * version; table cells do not become separate lines there.
            parts.append(f"<tr><td>{_e(sc.name(lang))}</td><td class='where'>"
                         f"<span class='hide'> → </span>{_e(templates.where_label(sc, lang))}</td></tr>")
        parts.append("</table>")
        # ! Same function as the screen, so the sheet can never state a
        # ! different total; payout and cover stay separate lines.
        payout, cover = engine.value_totals(tuple(eligible), schemes)
        if payout or cover:
            parts.append("<div class='money'>")
            if payout:
                parts.append(f"<p>{_e(s('result.value_line', lang, total=templates.rupees(payout)))}</p>")
            if cover:
                key = "result.cover_line" if payout else "result.cover_only_line"
                parts.append(f"<p>{_e(s(key, lang, total=templates.rupees(cover)))}</p>")
            # ! The caveat travels with the number onto paper too. A printed
            # ! sheet outlives the chat, and this is where it would be quoted.
            parts.append(f"<p class='caveat'>{_e(s('result.value_caveat', lang))}</p></div>")
        parts.append("</div>")

    for i, r in enumerate(eligible, start=1):
        sc = schemes[r.scheme_code]
        badge = s("result.new_badge", lang).lstrip("· ").strip() if r.scheme_code not in known else ""
        summary = sc.summary(lang)
        lead = templates.first_sentence(summary)
        more = summary[len(lead):].strip() if summary.startswith(lead) else ""
        parts.append("<div class='card'>")
        # ! name(lang), not name_hi. An English sheet had Hindi scheme headings
        # ! for a worker who chose English — the one line on the page they most
        # ! need to read out at a counter.
        parts.append(f"<h2>{i}. {_e(sc.name(lang))}"
                     + (f"<span class='hide'> ·</span> <span class='tag'>{_e(badge)}</span>" if badge else "") + "</h2>")
        parts.append(f"<p class='lead'>{_e(lead)}</p>")
        if more:
            parts.append(f"<p class='more'>{_e(more)}</p>")
        parts.append(_row(s("pack.where", lang), templates.where_label(sc, lang)))
        # * Same function as the screen, so the sheet cannot state a different cost.
        premium = templates.premium_text(sc, lang)
        if premium:
            parts.append(_row(s("pack.you_pay", lang), premium))
        why = templates._why(r, sc, lang)
        if why:
            parts.append(_row(s("pack.why", lang), why))
        docs = checklist.documents_for(sc, lang)
        if docs:
            # * A checklist to tick on paper: ☑ for what she said she has.
            parts.append(f"<p class='checks-title'>{_e(s('pack.carry', lang))}</p><ul class='checks'>")
            for d in docs:
                have = d in have_docs
                parts.append(f"<li class='{'have' if have else 'need'}'>"
                             f"<span class='box'>{'☑' if have else '☐'} </span>{_e(d)}</li>")
            parts.append("</ul>")
        parts.append("</div>")

    required = checklist.required_documents(results, schemes, lang)
    missing = checklist.missing_documents(required, have_docs)
    if missing:
        # * Said once, not after every paper: the old sheet repeated "ask at
        # * the centre how to get it" four times on one page.
        parts.append(f"<h2 class='section'>{_e(s('pack.still_need', lang))}</h2><div class='card'>")
        parts.append(f"<p class='note'>{_e(s('pack.still_need_how', lang))}</p><ul class='checks'>")
        parts += [f"<li class='need'><span class='box'>☐ </span>{_e(d)}</li>" for d in missing]
        parts.append("</ul></div>")

    if unknown:
        # ! Same grouping as the screen, from the same function. The bullet and
        # ! the question come from <ul>/<li> here, not from the chat string —
        # ! reusing that one printed "• •" inside a list.
        shared, items = templates.unknown_parts(results, schemes, lang)
        parts.append(f"<h2 class='section'>{_e(s('result.unknown_header', lang, count=len(items)))}</h2>")
        parts.append("<div class='card'>")
        if shared:
            parts.append(f"<p class='note'>{_e(s('result.unknown_shared', lang, gap=shared))}</p>")
        parts.append("<ul class='quiet'>")
        for name, gap in items:
            ask = s("pack.ask_at_centre", lang, name_hi=name)
            parts.append(f"<li><b>{_e(name)}</b>{'' if not gap else ' — ' + _e(gap)}"
                         f"<div class='why'>{_e(ask)}</div></li>")
        parts.append("</ul></div>")

    if ineligible:
        # * Every scheme she does not qualify for, with its authored reason.
        # * The screen shows only the names when something matched, so the
        # * reasons must live here or they are lost.
        parts.append(f"<h2 class='section'>{_e(s('result.ineligible_header', lang))}</h2><div class='card'><ul class='quiet'>")
        for r in ineligible:
            reason = templates._blocking_text(r, schemes[r.scheme_code], lang)
            parts.append(f"<li><b>{_e(schemes[r.scheme_code].name(lang))}</b>"
                         + (f"<div class='why'>{_e(reason)}</div>" if reason else "") + "</li>")
        parts.append("</ul></div>")

    # ! The answers go on the sheet, not just on the screen. A counter clerk
    # ! asks the same questions again, and the worker cannot re-open a chat she
    # ! has scrolled past. Still no name, no phone, no Aadhaar — the Profile has
    # ! no such field to leak.
    if recap:
        parts.append(f"<h2 class='section'>{_e(s('pack.your_answers', lang))}</h2><div class='card'><ul class='answers'>")
        parts += [f"<li>{_e(line.lstrip('• '))}</li>" for line in recap.splitlines() if line.strip()]
        parts.append("</ul></div>")

    parts.append(f"<p class='foot'>{_e(s('pack.disclaimer', lang))}</p>")
    parts.append("</main></body></html>")

    return f"scheme-sathi-{stamp}.html", "\n".join(parts).encode("utf-8")


def _self_check() -> None:
    from sathi.core.profile import Profile
    from sathi.core.schemes import Criterion as C
    from sathi.rules.engine import evaluate_all

    def scheme(code, value, crit, **kw):
        base = dict(
            code=code, name_en=code, name_hi=f"योजना-{code}", authority="A",
            official_url="u", verified_on="2026-09-01", verified_by="a",
            benefit={"annual_value_inr": value, "value_basis": "annual_payout",
                     "summary_hi": "हर साल पैसा", "summary_en": "money every year"},
            criteria=(C("age", "between", crit, "u", pass_hi="उम्र सही है", fail_hi="नहीं",
                        pass_en="your age fits", fail_en="no"),),
            exclusions=(), documents=("आधार", "बैंक पासबुक"),
            documents_en=("Aadhaar", "Bank passbook"),
            where_to_apply="csc", renewal="none",
        )
        base.update(kw)
        return Scheme(**base)

    schemes = {"A": scheme("A", 12000, [18, 40]),
               "B": scheme("B", 0, [18, 40], stubs=("benefit.annual_value_inr",))}
    results = evaluate_all(Profile(age=30), schemes)
    name, blob = build(results, schemes, known=frozenset(), have_docs=frozenset({"आधार"}))

    assert name.startswith("scheme-sathi-") and name.endswith(".html")
    text = blob.decode("utf-8")
    assert "योजना-A" in text and "12,000" in text
    assert "बैंक पासबुक" in text
    assert "पैसा अभी मिला नहीं" in text, "the caveat must be on the printed sheet too"
    assert "<script" not in text.lower(), "the pack is a document, not an app"

    # * The same pack in English, for a CSC operator filling it in for someone.
    _, en = build(results, schemes, known=frozenset(), lang="en")
    en_text = en.decode("utf-8")
    assert "12,000" in en_text and s("result.value_caveat", "en") in en_text
    assert "accident insurance" not in s("result.cover_line", "en")
    # ! An English sheet must carry no Devanagari at all — not in the heading,
    # ! not in a label. A real pack shipped with Hindi scheme names and Hindi
    # ! field labels because both were built outside the string files.
    body = en_text.split("<body>", 1)[1]
    assert not any("\u0900" <= ch <= "\u097f" for ch in body), \
        "Devanagari on an English pack: " + \
        "".join(ch for ch in body if "\u0900" <= ch <= "\u097f")[:60]

    # * And the other direction: a scheme with NO English still renders a full
    # * English sheet by falling back to Hindi, rather than printing blanks.
    bare = {"A": Scheme(
        code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
        verified_on="2026-09-01", verified_by="a",
        benefit={"annual_value_inr": 500, "value_basis": "annual_payout",
                 "summary_hi": "हर साल पैसा"},
        criteria=(C("age", "between", [18, 40], "u", pass_hi="उम्र सही है", fail_hi="नहीं"),),
        exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
    )}
    _, blob2 = build(evaluate_all(Profile(age=30), bare), bare, frozenset(), lang="en")
    assert "हर साल पैसा" in blob2.decode("utf-8"), "fallback must print Hindi, never nothing"
    for leak in ("आधार नंबर", "aadhaar number", "phone", "मोबाइल नंबर"):
        assert leak not in text.lower(), leak
    print("pack.py OK")


if __name__ == "__main__":
    _self_check()
