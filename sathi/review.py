"""Sign a scheme file off — the last gate before a worker is told anything.

# ! This is the ONLY supported way to put a human name into `verified_by`, and
# ! it is deliberately a person sitting at a keyboard with the official page
# ! open. It refuses to run without a terminal, refuses a name that looks
# ! automated, and makes you type the scheme code back before it writes.
#
# * Why this exists. Every scheme ships unsigned, so every worker gets UNKNOWN
# * and the bot says the same thing to everybody. That is correct — nobody
# * should be sent to a CSC on a number one machine transcribed once — but it
# * also means the product does nothing until a person checks the values. The
# * checking was the slow part: seven files, forty-odd values, each needing its
# * source opened. So this prints every value NEXT TO the URL it came from and
# * the sentence it was transcribed from, one scheme at a time.
#
# ! What this tool does NOT do: it does not check anything for you. It shows
# ! you what to check. Typing "yes" is you saying you opened the page and read
# ! the values. If you have not, say no — an unsigned scheme is a working
# ! state, not a failure.
"""

import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sathi.core.schemes import PENDING_MARKER, STUB, Scheme, load_all

SCHEMES_DIR = Path(__file__).resolve().parent.parent / "data" / "schemes"

# ! A signature has to name a person who can be asked about it later. These are
# ! the ways the field has actually been filled in wrongly so far, plus the
# ! obvious attempts to hand the responsibility back to a machine.
#
# ! Matched as whole words, NOT as substrings. The first version matched
# ! substrings and refused "Avinash Negi", because "Avinash" contains "na" —
# ! a name check that rejects the maintainer's own name is worse than useless,
# ! because the way round it is to weaken the check.
_REFUSED_WORDS = frozenset({
    "ai", "bot", "auto", "assistant", "agent", "model", "machine",
    "unconfirmed", "pending", "todo", "tbd", "na", "none", "nobody",
    "test", "testing", "example", "anon", "anonymous", "admin", "user",
})
# ! These are refused anywhere in the name — no real person is called this.
_REFUSED_ANYWHERE = ("claude", "codex", "chatgpt", "gpt-", "copilot", "gemini",
                     "llm", "openai", "anthropic", "auto-research")


class ReviewError(Exception):
    """The reviewer's input was refused. Never caught to carry on regardless."""


@dataclass(frozen=True)
class Row:
    """One thing to check, and where to check it."""

    what: str
    value: str
    source: str


def rows_for(scheme: Scheme, lang: str = "en") -> list[Row]:
    """Every value in the file that a reviewer has to confirm, with its source.

    # ! Built from the loaded Scheme, not by re-reading the TOML, so what you
    # ! are shown is what the engine will actually use. A comment in the file
    # ! that disagrees with the parsed value cannot mislead you here.
    """
    rows = [
        Row("scheme name", scheme.name(lang), scheme.official_url),
        Row("authority", scheme.authority, scheme.official_url),
        Row("benefit ₹/year", str(scheme.benefit.get("annual_value_inr")),
            scheme.official_url),
        Row("benefit basis", str(scheme.benefit.get("value_basis")),
            scheme.official_url),
        Row("premium/cost", str(scheme.benefit.get("premium_inr")),
            scheme.official_url),
        Row("what the worker is told", scheme.summary(lang), scheme.official_url),
    ]
    group = scheme.exclusive_group
    if group:
        rows.append(Row("counted as an alternative to", group, scheme.official_url))
    for c in scheme.criteria:
        rows.append(Row(f"must have: {c.field} {c.op}", str(c.value), c.source_url))
    for e in scheme.exclusions:
        rows.append(Row(f"ruled out if: {e.field} {e.op}", str(e.value), e.source_url))
    rows.append(Row("documents to bring", " · ".join(scheme.docs(lang)),
                    scheme.official_url))
    rows.append(Row("where to apply", scheme.where_to_apply, scheme.official_url))
    rows.append(Row("renewal / timing", scheme.renewal_en or scheme.renewal,
                    scheme.official_url))
    return rows


def source_notes(scheme: Scheme) -> list[str]:
    """The `# !` and `# ?` comments the file author left, in file order.

    # * These carry the quoted source sentences and the open questions. They are
    # * the difference between "confirm 12 numbers" and "confirm 12 numbers and
    # * also notice the two that nobody could settle".
    """
    if not scheme.source_path:
        return []
    text = Path(scheme.source_path).read_text(encoding="utf-8")
    return [line.strip() for line in text.splitlines()
            if line.lstrip().startswith(("# !", "# ?", "#!", "#?"))]


def check_name(name: str) -> str:
    """A signature must name a person. Raises rather than quietly accepting."""
    name = " ".join(name.split())
    low = name.lower()
    refused = (
        len(name) < 3
        or not re.search(r"[A-Za-z]{2}", name)
        or any(bad in low for bad in _REFUSED_ANYWHERE)
        or bool(_REFUSED_WORDS & set(re.findall(r"[a-z]+", low)))
    )
    if refused:
        raise ReviewError(
            f"{name!r} is refused: a signature has to name the person who "
            f"checked the values and can be asked about them later. "
            f"An assistant cannot sign this."
        )
    return name


def sign(code: str, name: str, on: str = "", schemes_dir: Path | None = None) -> Path:
    """Replace verified_by/verified_on in one scheme file. Returns the path.

    # ! Rewrites exactly two lines and touches nothing else, so a signature can
    # ! never smuggle in a changed threshold. The whole file is re-loaded and
    # ! re-validated afterwards; if it does not load, the write is rolled back.
    """
    name = check_name(name)
    on = on or date.today().isoformat()
    directory = schemes_dir or SCHEMES_DIR
    schemes = load_all(directory)
    if code not in schemes:
        raise ReviewError(f"No scheme {code!r}. Known: {', '.join(sorted(schemes))}")
    path = Path(schemes[code].source_path)
    before = path.read_text(encoding="utf-8")

    signature = f'"{name}, checked {on}"'
    text, n_by = re.subn(r'(?m)^(verified_by\s*=\s*).*$', lambda m: m.group(1) + signature, before, count=1)
    text, n_on = re.subn(r'(?m)^(verified_on\s*=\s*).*$', lambda m: m.group(1) + f'"{on}"', text, count=1)
    if not (n_by and n_on):
        raise ReviewError(f"{path.name}: could not find verified_by/verified_on to replace")

    path.write_text(text, encoding="utf-8")
    try:
        after = load_all(directory)[code]
    except Exception:
        path.write_text(before, encoding="utf-8")
        raise
    if not after.is_human_verified:
        path.write_text(before, encoding="utf-8")
        raise ReviewError(f"{code}: signature did not take; file restored unchanged")
    return path


def unsign(code: str, schemes_dir: Path | None = None) -> Path:
    """Put a scheme back behind the gate. Always available, never questioned."""
    directory = schemes_dir or SCHEMES_DIR
    schemes = load_all(directory)
    if code not in schemes:
        raise ReviewError(f"No scheme {code!r}")
    path = Path(schemes[code].source_path)
    text = re.sub(r'(?m)^(verified_by\s*=\s*).*$',
                  lambda m: m.group(1) + f'"unconfirmed — {PENDING_MARKER}"',
                  path.read_text(encoding="utf-8"), count=1)
    path.write_text(text, encoding="utf-8")
    return path


# * ------------------------------------------------------------------ terminal


def _status_line(code: str, s: Scheme) -> str:
    if s.stubs:
        return f"  {code:12s} UNRESEARCHED — {len(s.stubs)} value(s) still TODO"
    if not s.is_human_verified:
        return f"  {code:12s} awaiting your signature"
    return f"  {code:12s} SIGNED — {s.verified_by}"


def _print_scheme(code: str, s: Scheme, lang: str) -> None:
    print("=" * 72)
    print(f"{code} — {s.name(lang)}")
    print(f"Open this and keep it beside you: {s.official_url}")
    print("=" * 72)
    for note in source_notes(s):
        print(f"  {note}")
    print()
    seen_sources: list[str] = []
    for row in rows_for(s, lang):
        if row.source not in seen_sources:
            seen_sources.append(row.source)
        mark = seen_sources.index(row.source) + 1
        value = row.value if len(row.value) <= 300 else row.value[:297] + "..."
        print(f"  [{mark}] {row.what}")
        print(f"      {value}")
    print()
    for i, url in enumerate(seen_sources, start=1):
        print(f"  [{i}] {url}")
    print()


def _ask(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        raise ReviewError("no answer given") from None


def main(argv: list[str]) -> int:
    if not sys.stdin.isatty():
        print("sathi.review needs a terminal. A signature is a person's act, "
              "so it cannot be piped in or scripted.", file=sys.stderr)
        return 2

    args = [a for a in argv if not a.startswith("-")]
    lang = "hi" if "--hi" in argv else "en"
    schemes = load_all(SCHEMES_DIR)

    if "--unsign" in argv:
        for code in args:
            print(f"unsigned: {unsign(code).name}")
        return 0

    codes = args or sorted(schemes)
    print()
    print("Scheme sign-off. Nothing here checks anything for you — it shows you")
    print("every value beside the page it came from, so you can. Say no freely:")
    print("an unsigned scheme answers 'I could not check this yet', which is a")
    print("working state. A wrong yes sends someone on a day's wasted travel.")
    print()
    for code in sorted(schemes):
        print(_status_line(code, schemes[code]))
    print()

    signed_now = []
    for code in codes:
        s = schemes.get(code)
        if s is None:
            print(f"!! no scheme {code!r}, skipping")
            continue
        if s.stubs:
            print(f"-- {code}: still has {len(s.stubs)} unresearched value(s) "
                  f"({', '.join(s.stubs[:3])}). Research it before signing.")
            continue
        if s.is_human_verified:
            print(f"-- {code}: already signed by {s.verified_by}")
            continue

        _print_scheme(code, s, lang)
        answer = _ask(f"Did you open the source(s) and confirm every value above? "
                      f"Type {code} to sign, anything else to skip: ")
        if answer != code:
            print(f"-- {code} left unsigned.\n")
            continue
        try:
            name = check_name(_ask("Your full name, as the person who checked it: "))
        except ReviewError as e:
            print(f"!! {e}\n")
            continue
        path = sign(code, name)
        signed_now.append(code)
        print(f"++ {code} signed by {name} — {path.name}\n")

    if signed_now:
        print()
        print(f"Signed: {', '.join(signed_now)}")
        print("These schemes now produce real verdicts and real ₹ figures for")
        print("every worker who talks to the bot. Before deploying:")
        print("  python3 check.py")
        print("To undo any of them:")
        print(f"  python3 -m sathi.review --unsign {' '.join(signed_now)}")
    else:
        print("Nothing signed. Every scheme still answers 'I could not check this yet'.")
    return 0


def _self_check() -> None:
    import shutil
    import tempfile

    schemes = load_all(SCHEMES_DIR)
    assert schemes, "no scheme files found"

    # * Every shipped scheme must produce a reviewable list with a source on
    # * every row — a blank source is a row nobody can actually check.
    for code, s in schemes.items():
        rows = rows_for(s)
        assert rows, code
        for r in rows:
            assert r.source.startswith("https://"), f"{code}: {r.what} has no source"

    for bad in ("", "ai", "Claude", "claude opus", "auto-researched", "TODO", "x"):
        try:
            check_name(bad)
        except ReviewError:
            pass
        else:
            raise AssertionError(f"check_name accepted {bad!r}")
    assert check_name("  Avinash   Negi ") == "Avinash Negi"

    # * Sign and unsign a real copy, and prove nothing else in the file moved.
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "schemes"
        shutil.copytree(SCHEMES_DIR, tmp)
        code = sorted(c for c, s in schemes.items() if not s.stubs)[0]
        path = Path(load_all(tmp)[code].source_path)
        before = path.read_text(encoding="utf-8")

        assert not load_all(tmp)[code].is_servable, "fixture must start unsigned"
        sign(code, "A Real Person", on="2026-09-09", schemes_dir=tmp)
        after = load_all(tmp)[code]
        assert after.is_human_verified and after.is_servable
        assert after.verified_by == "A Real Person, checked 2026-09-09"
        assert after.verified_on == "2026-09-09"

        # ! Only the two signature lines may differ. This is what stops a
        # ! signature from ever carrying a data change in with it.
        diff = [(a, b) for a, b in zip(before.splitlines(),
                                       path.read_text(encoding="utf-8").splitlines())
                if a != b]
        assert len(diff) == 2, diff
        assert all(x.startswith(("verified_by", "verified_on")) for x, _ in diff), diff

        unsign(code, schemes_dir=tmp)
        assert not load_all(tmp)[code].is_servable

        try:
            sign(code, "Claude", schemes_dir=tmp)
        except ReviewError:
            pass
        else:
            raise AssertionError("an assistant was allowed to sign")
        assert not load_all(tmp)[code].is_servable, "refused sign must not write"

    print("review.py OK")


if __name__ == "__main__":
    if "--self-check" in sys.argv:
        _self_check()
    else:
        try:
            raise SystemExit(main(sys.argv[1:]))
        except ReviewError as e:
            print(f"!! {e}", file=sys.stderr)
            raise SystemExit(1) from None
