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
from sathi.rules.engine import Result, Verdict

_CSS = """
body { font-family: system-ui, 'Noto Sans Devanagari', sans-serif; line-height: 1.7;
       max-width: 46rem; margin: 1.5rem auto; padding: 0 1rem; color: #111; }
h1 { font-size: 1.5rem; margin-bottom: .25rem; }
.meta { color: #555; font-size: .9rem; }
.scheme { border: 1px solid #ccc; border-radius: .5rem; padding: 1rem; margin: 1rem 0; }
.scheme h2 { font-size: 1.15rem; margin: 0 0 .5rem; }
.label { color: #555; font-size: .85rem; }
ul { margin: .25rem 0 0 1.1rem; padding: 0; }
.note { background: #fff8e1; border-left: 4px solid #e0a800; padding: .75rem 1rem;
        margin: 1rem 0; }
.foot { border-top: 1px solid #ccc; margin-top: 2rem; padding-top: .75rem;
        color: #555; font-size: .85rem; }
@media print { body { margin: 0; } .scheme { break-inside: avoid; } }
"""


def _e(text: object) -> str:
    return html.escape(str(text), quote=False).replace("\n", "<br>")


def build(
    results: tuple[Result, ...],
    schemes: dict[str, Scheme],
    known: frozenset[str],
    have_docs: frozenset[str] = frozenset(),
    today: date | None = None,
    lang: str = "hi",
) -> tuple[str, bytes]:
    """Return (filename, bytes). Nothing touches the filesystem."""
    eligible = [r for r in results if r.verdict is Verdict.ELIGIBLE]
    unknown = [r for r in results if r.verdict is Verdict.UNKNOWN]
    stamp = (today or date.today()).isoformat()

    parts = [
        f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        f"<title>{_e(s('pack.title', lang))}</title><style>{_CSS}</style></head><body>",
        f"<h1>{_e(s('pack.title', lang))}</h1>",
        f"<p class='meta'>{_e(s('pack.generated_on', lang, date=stamp))}</p>",
    ]

    for i, r in enumerate(eligible, start=1):
        sc = schemes[r.scheme_code]
        badge = s("result.new_badge", lang) if r.scheme_code not in known else ""
        docs = checklist.documents_for(sc, lang)
        parts.append("<div class='scheme'>")
        # ! name(lang), not name_hi. An English sheet had Hindi scheme headings
        # ! for a worker who chose English — the one line on the page they most
        # ! need to read out at a counter.
        parts.append(f"<h2>{i}. {_e(sc.name(lang))} {_e(badge)}</h2>")
        parts.append(f"<p>{_e(sc.summary(lang))}</p>")
        why = templates._why(r, sc, lang)
        if why:
            parts.append(
                f"<p><span class='label'>{_e(s('pack.why', lang))}:</span> {_e(why)}</p>"
            )
        parts.append(
            f"<p><span class='label'>{_e(s('pack.where', lang))}:</span> "
            f"{_e(templates.where_label(sc, lang))}</p>"
        )
        if docs:
            parts.append(f"<p class='label'>{_e(s('pack.carry', lang))}:</p><ul>")
            parts += [f"<li>{_e(d)}</li>" for d in docs]
            parts.append("</ul>")
        parts.append("</div>")

    required = checklist.required_documents(results, schemes, lang)
    missing = checklist.missing_documents(required, have_docs)
    if missing:
        parts.append(f"<div class='note'><b>{_e(s('documents.missing_header', lang))}</b><ul>")
        parts += [
            f"<li>{_e(s('documents.missing_line', lang, doc=d, how=s('documents.how_generic', lang)))}</li>"
            for d in missing
        ]
        parts.append("</ul></div>")

    if unknown:
        parts.append(f"<div class='note'><b>{_e(s('result.unknown_header', lang, count=len(unknown)))}</b><ul>")
        for r in unknown:
            sc = schemes[r.scheme_code]
            parts.append(f"<li>{_e(templates.s('result.unknown_line', lang, name_hi=sc.name(lang), gap=templates._gap(r, lang)))}</li>")
        parts.append("</ul></div>")

    # ! Split, for the same reason as on screen: a cover is not annual income.
    payout = sum(r.annual_value_inr for r in eligible if r.value_basis != "insurance_cover")
    cover = sum(r.annual_value_inr for r in eligible if r.value_basis == "insurance_cover")
    if payout or cover:
        money = []
        if payout:
            money.append(_e(s("result.value_line", lang, total=templates.rupees(payout))))
        if cover:
            key = "result.cover_line" if payout else "result.cover_only_line"
            money.append(_e(s(key, lang, total=templates.rupees(cover))))
        parts.append(
            "<p>" + "<br>".join(money) + "<br>"
            # ! The caveat travels with the number onto paper too. A printed
            # ! sheet outlives the chat, and this is where it would be quoted.
            f"<b>{_e(s('result.value_caveat', lang))}</b></p>"
        )

    parts.append(f"<p class='foot'>{_e(s('pack.disclaimer', lang))}</p>")
    parts.append("</body></html>")

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
    assert "12,000" in en_text and "has not been paid yet" in en_text
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
