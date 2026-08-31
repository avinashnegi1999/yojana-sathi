"""Which documents the worker needs, and which they say they lack.

# * Document names come from each scheme's paperwork.documents, authored with
# * the scheme. Nothing here invents a document, and nothing here claims to know
# * where a missing one is issued — that answer is "ask at the centre" until
# * somebody researches it with a source. See documents.how_generic.
"""

from sathi.core.schemes import STUB, Scheme
from sathi.rules.engine import Result, Verdict


def required_documents(results: tuple[Result, ...], schemes: dict[str, Scheme],
                       lang: str = "hi") -> tuple[str, ...]:
    """Union of documents across the schemes worth walking to a centre for.

    Eligible schemes only. Carrying paperwork for a scheme they do not qualify
    for wastes the trip we are trying to make worthwhile.
    """
    out: list[str] = []
    for r in results:
        if r.verdict is not Verdict.ELIGIBLE:
            continue
        for doc in schemes[r.scheme_code].docs(lang):
            # * An unresearched documents list reads ["TODO"] — never show that.
            if doc != STUB and doc not in out:
                out.append(doc)
    return tuple(out)


def missing_documents(required: tuple[str, ...], have: frozenset[str]) -> tuple[str, ...]:
    return tuple(d for d in required if d not in have)


def documents_for(scheme: Scheme, lang: str = "hi") -> tuple[str, ...]:
    return tuple(d for d in scheme.docs(lang) if d != STUB)


def _self_check() -> None:
    from sathi.core.profile import Profile
    from sathi.core.schemes import Criterion as C
    from sathi.rules.engine import evaluate_all

    def scheme(code, docs, crit):
        return Scheme(
            code=code, name_en=code, name_hi=code, authority="A", official_url="u",
            verified_on="2026-09-01", verified_by="a",
            benefit={"annual_value_inr": 1000, "value_basis": "annual_payout"},
            criteria=(C("age", "between", crit, "u", pass_hi="ok", fail_hi="no"),),
            exclusions=(), documents=docs, where_to_apply="csc", renewal="none",
        )

    schemes = {
        "A": scheme("A", ("आधार", "बैंक पासबुक"), [18, 40]),
        "B": scheme("B", ("आधार", "राशन कार्ड"), [18, 40]),
        "C": scheme("C", ("वोटर कार्ड",), [60, 90]),  # not eligible at 30
        "D": scheme("D", (STUB,), [18, 40]),
    }
    results = evaluate_all(Profile(age=30), schemes)
    req = required_documents(results, schemes)
    assert req == ("आधार", "बैंक पासबुक", "राशन कार्ड"), req
    assert "वोटर कार्ड" not in req, "documents for an ineligible scheme are noise"
    assert STUB not in req, "a stub document must never be shown to a worker"
    assert missing_documents(req, frozenset({"आधार"})) == ("बैंक पासबुक", "राशन कार्ड")
    print("checklist.py OK")


if __name__ == "__main__":
    _self_check()
