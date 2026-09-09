"""Watch the official pages our scheme rules were transcribed from.

# * The problem this solves. A signature says "on 9 September a person checked
# * these values against the source". It says nothing about 9 November. A
# * ministry can change ₹436, or a state can revise a pension rate, and every
# * signed file in this repo silently becomes a promise we no longer keep — a
# * worker is sent to a branch on last quarter's number. Nothing in the code
# * would notice.
#
# * What is stored, in data/sources/<code>.json:
# *   - the URL, and a SHA-256 of its normalised text on the day it was read
# *   - the CLAIMS: one named pattern per value the scheme file asserts
# *
# ! Deliberately NOT stored: a copy of the page. Republishing a government
# ! page wholesale is someone else's text to publish, and a stale copy in the
# ! repo is worse than no copy — it looks authoritative and cannot tell you the
# ! day it stopped being true. A fingerprint plus the specific sentences we
# ! rely on gives the auditability without either problem: `check` re-reads the
# ! live page and tells you which of OUR claims it still supports.
#
# ! No network access happens at import, in the self-check, or anywhere the bot
# ! runs. `check` is a thing a maintainer runs on purpose.
"""

import hashlib
import json
import re
import sys
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCES_DIR = ROOT / "data" / "sources"

_TAGS = re.compile(r"<(script|style)[\s\S]*?</\1>|<[^>]+>", re.I)
_ENTITIES = {"&nbsp;": " ", "&amp;": "&", "&#8377;": "₹", "&rsquo;": "'",
             "&lsquo;": "'", "&#8217;": "'", "&ndash;": "–", "&#8211;": "–"}


def normalise(html: str) -> str:
    """Page text with markup, entities and whitespace flattened.

    # ! The fingerprint is taken over THIS, not the raw bytes. Government sites
    # ! rotate banners, session ids and CSRF tokens on every request; hashing
    # ! the raw HTML would report a change every single time and the check
    # ! would be ignored within a week.
    """
    text = _TAGS.sub(" ", html)
    for entity, char in _ENTITIES.items():
        text = text.replace(entity, char)
    return re.sub(r"\s+", " ", text).strip()


def fingerprint(html: str) -> str:
    return hashlib.sha256(normalise(html).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Claim:
    """One thing our scheme file says, and the pattern that finds it on the page."""

    name: str
    pattern: str

    def holds(self, text: str) -> bool:
        return re.search(self.pattern, text, re.I | re.S) is not None


@dataclass(frozen=True)
class Record:
    code: str
    url: str
    read_on: str
    sha256: str
    chars: int
    claims: tuple[Claim, ...]
    # ! A claim that must NOT be on the page. "16–59 is absent from the current
    # ! e-Shram FAQ" is a real finding and the reason an ambiguity was closed;
    # ! if it ever reappears we want to hear about it.
    absent: tuple[Claim, ...] = ()

    @classmethod
    def load(cls, path: Path) -> "Record":
        d = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            code=d["code"], url=d["url"], read_on=d["read_on"],
            sha256=d["sha256"], chars=d["chars"],
            claims=tuple(Claim(**c) for c in d.get("claims", ())),
            absent=tuple(Claim(**c) for c in d.get("absent", ())),
        )

    def save(self, directory: Path) -> Path:
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self.code.lower()}.json"
        path.write_text(json.dumps({
            "code": self.code, "url": self.url, "read_on": self.read_on,
            "sha256": self.sha256, "chars": self.chars,
            "claims": [{"name": c.name, "pattern": c.pattern} for c in self.claims],
            "absent": [{"name": c.name, "pattern": c.pattern} for c in self.absent],
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path


def fetch(url: str, timeout: int = 45) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "yojana-sathi source check"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


@dataclass(frozen=True)
class Outcome:
    code: str
    url: str
    reachable: bool
    changed: bool | None          # None when the page could not be read
    failed: tuple[str, ...]       # claims the page no longer supports
    reappeared: tuple[str, ...]   # `absent` claims that came back
    note: str = ""

    @property
    def ok(self) -> bool:
        return self.reachable and not self.failed and not self.reappeared


def check_one(record: Record) -> Outcome:
    try:
        html = fetch(record.url)
    except Exception as e:  # noqa: BLE001 — any failure is "could not read it"
        return Outcome(record.code, record.url, False, None, (), (),
                       f"{type(e).__name__}: {e}")
    text = normalise(html)
    return Outcome(
        code=record.code,
        url=record.url,
        reachable=True,
        changed=fingerprint(html) != record.sha256,
        failed=tuple(c.name for c in record.claims if not c.holds(text)),
        reappeared=tuple(c.name for c in record.absent if c.holds(text)),
    )


def records(directory: Path | None = None) -> list[Record]:
    d = directory or SOURCES_DIR
    return [Record.load(p) for p in sorted(d.glob("*.json"))] if d.is_dir() else []


def main(argv: list[str]) -> int:
    directory = SOURCES_DIR
    all_records = records(directory)
    if not all_records:
        print(f"No source records in {directory}.")
        return 1
    wanted = {a.upper() for a in argv if not a.startswith("-")}
    todo = [r for r in all_records if not wanted or r.code in wanted]

    print(f"Re-reading {len(todo)} official page(s). This is the only part of "
          f"this project that touches the network.\n")
    problems = 0
    for record in todo:
        outcome = check_one(record)
        if not outcome.reachable:
            print(f"  ?  {record.code:12s} could not read the page — {outcome.note}")
            print(f"     {record.url}")
            problems += 1
            continue
        if outcome.failed or outcome.reappeared:
            problems += 1
            print(f"  !! {record.code:12s} THE PAGE NO LONGER MATCHES THIS FILE")
            for name in outcome.failed:
                print(f"       gone:       {name}")
            for name in outcome.reappeared:
                print(f"       reappeared: {name}")
            print(f"     {record.url}")
            print(f"     Re-read it, fix data/schemes/, and re-sign. Until then "
                  f"consider unsigning: python3 -m sathi.review --unsign {record.code}")
        elif outcome.changed:
            print(f"  ~  {record.code:12s} every value still checks out, but the page "
                  f"text changed since {record.read_on}")
            print(f"     Worth a glance for anything new: {record.url}")
        else:
            print(f"  ok {record.code:12s} unchanged since {record.read_on}")
    print()
    if problems:
        print(f"{problems} page(s) need a person. Nothing was changed automatically.")
    return 1 if problems else 0


def _self_check() -> None:
    # ! No network here. The build gate must not depend on a ministry's uptime.
    page = ("<html><body><h1>Scheme</h1><p>The premium payable is "
            "Rs.436/- per annum per subscriber.</p>"
            "<p>age group of 18 to 50 years</p><script>var x=1</script></body></html>")
    text = normalise(page)
    assert "<" not in text and "var x" not in text, text
    assert "Rs.436/- per annum" in text

    # * Whitespace and banner noise must not move the fingerprint...
    noisy = page.replace("<p>", "\n\n   <p>").replace("</p>", "</p>  \t")
    assert fingerprint(noisy) == fingerprint(page), "whitespace changed the hash"
    # * ...but a changed rupee figure must.
    assert fingerprint(page.replace("436", "500")) != fingerprint(page)

    premium = Claim("premium 436", r"premium payable is\s*Rs\.?\s*436")
    age = Claim("age 18-50", r"age group of\s*18\s*to\s*50\s*years")
    missing = Claim("age 16-59", r"16\s*(?:-|to|–)\s*59")
    assert premium.holds(text) and age.holds(text)
    assert not missing.holds(text)

    record = Record("TEST", "https://example.invalid/x", "2026-09-09",
                    fingerprint(page), len(text), (premium, age), (missing,))

    import tempfile
    with tempfile.TemporaryDirectory() as d:
        path = record.save(Path(d))
        again = Record.load(path)
        assert again == record, "a record did not survive a round trip"

    # * An unreachable page is never silently "fine".
    bad = check_one(Record("TEST", "https://example.invalid/nope", "2026-09-09",
                           "0" * 64, 0, (premium,)))
    assert not bad.reachable and not bad.ok and bad.changed is None

    # ! Every shipped record must name a scheme that exists, so a renamed
    # ! scheme cannot leave a source record watching nothing.
    from sathi.core.schemes import load_all
    if SOURCES_DIR.is_dir():
        known = set(load_all())
        for r in records():
            assert r.code in known, f"source record {r.code} has no scheme file"
            assert r.claims, f"{r.code}: a record with no claims checks nothing"
            assert r.url.startswith("https://"), r.code
    print("sources.py OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        raise SystemExit(main(sys.argv[1:]))
