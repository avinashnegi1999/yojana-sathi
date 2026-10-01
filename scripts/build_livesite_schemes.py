"""Build livesite/assets/schemes.json from the signed rule files.

The expandable scheme cards on the live page read this file, so every word a
visitor sees when they open a card comes from data/schemes/*.toml, not from
the page. Unsigned files (verified_by not a person) are skipped.

Run from the repository root:  python scripts/build_livesite_schemes.py
"""
import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMES = ROOT / "data" / "schemes"
OUT = ROOT / "livesite" / "assets" / "schemes.json"

# Card title on the page -> rule file(s) behind it.
CARDS = {
    "PM Shram Yogi Maandhan": ["pm_sym"],
    "National Pension Scheme for Traders": ["nps_traders"],
    "Atal Pension Yojana": ["apy"],
    "PM Jeevan Jyoti Bima Yojana": ["pmjjby"],
    "PM Suraksha Bima Yojana": ["pmsby"],
    "Ayushman Bharat PM-JAY, 70+": ["pmjay_70"],
    "PM Vishwakarma": ["pm_vishwakarma"],
    "PM Ujjwala Yojana": ["pmuy"],
    "Jan Dhan bank account": ["pmjdy"],
    "e-Shram registration": ["eshram"],
    "Indira Gandhi National Old Age Pension": ["ignoaps"],
    "Indira Gandhi National Widow Pension": ["ignwps"],
    "Indira Gandhi National Disability Pension": ["igndps"],
    "Uttarakhand old-age pension": ["uk_old_age"],
    "Uttarakhand widow pension": ["uk_widow"],
    "Sikkim old-age pension": ["sk_ignoaps"],
    "Sikkim widow pension": ["sk_ignwps"],
    "Sikkim disability pension": ["sk_igndps"],
    "Madhya Pradesh Kalyani pension": ["mp_kalyani"],
    "Punjab old-age pension": ["pb_old_age_women", "pb_old_age_men"],
}


def signed(d):
    return d.get("verified_by", "").lower().startswith("avinash")


def entry(stem):
    d = tomllib.loads((SCHEMES / f"{stem}.toml").read_text(encoding="utf-8"))
    if not signed(d):
        return None
    asks, seen = [], set()
    for rule in d.get("criteria", []) + d.get("exclusions", []):
        q = rule.get("ask_en")
        if q and q not in seen:
            seen.add(q)
            asks.append(q)
    p = d.get("paperwork", {})
    return {
        "name": d.get("name_en"),
        "name_hi": d.get("name_hi"),
        "authority": d.get("authority"),
        "summary": d.get("benefit", {}).get("summary_en"),
        "asks": asks,
        "documents": p.get("documents_en", []),
        "renewal": p.get("renewal_en"),
        "source": d.get("official_url"),
        "verified": d.get("verified_on"),
    }


def main():
    out = {}
    for title, stems in CARDS.items():
        parts = [e for e in (entry(s) for s in stems) if e]
        if parts:
            out[title] = parts
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(out)} cards to {OUT}")


if __name__ == "__main__":
    main()
