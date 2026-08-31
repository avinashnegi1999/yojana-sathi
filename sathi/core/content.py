"""Loaders for the non-scheme data files: occupations, states, Hindi strings.

# * Scheme rules live in sathi/core/schemes.py and are validated hard, because a
# * wrong threshold sends a worker on a wasted trip. The files here are UI
# * content — menus and phrasing — so they get a lighter check: they must exist,
# * parse, and contain the keys the code actually reads.
#
# ! Everything a worker ever sees comes from data/strings_*.toml. No Hindi or
# ! English string literal belongs in a .py file: a reviewer reads two files,
# ! not twelve.
"""

import os
import tomllib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

# * Repo root is two levels up from sathi/core/. SATHI_DATA_DIR overrides it so
# * a container can mount data elsewhere without a code change.
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def data_dir() -> Path:
    return Path(os.environ.get("SATHI_DATA_DIR", _DEFAULT_DATA_DIR))


class ContentError(Exception):
    """A content file is missing or malformed. The app refuses to start."""


def _load_toml(name: str) -> dict:
    path = data_dir() / name
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ContentError(f"{path} not found") from e
    except tomllib.TOMLDecodeError as e:
        raise ContentError(f"{path}: not valid TOML — {e}") from e


@dataclass(frozen=True)
class Occupation:
    code: str
    label_hi: str
    label_en: str
    emoji: str
    keywords_hi: tuple[str, ...]
    keywords_en: tuple[str, ...]

    def label(self, lang: str = "hi") -> str:
        return self.label_en if lang == "en" else self.label_hi

    def button_label(self, lang: str = "hi") -> str:
        return f"{self.emoji} {self.label(lang)}".strip()


@dataclass(frozen=True)
class State:
    code: str
    label_hi: str
    label_en: str
    aliases: tuple[str, ...]
    common: bool

    def label(self, lang: str = "hi") -> str:
        return self.label_en if lang == "en" else self.label_hi


@lru_cache(maxsize=1)
def occupations() -> tuple[Occupation, ...]:
    raw = _load_toml("occupations.toml").get("occupation", [])
    if not raw:
        raise ContentError("occupations.toml: no [[occupation]] blocks")
    out = []
    for i, o in enumerate(raw):
        try:
            out.append(
                Occupation(
                    code=o["code"],
                    label_hi=o["label_hi"],
                    label_en=o["label_en"],
                    emoji=o.get("emoji", ""),
                    keywords_hi=tuple(o.get("keywords_hi", [])),
                    keywords_en=tuple(o.get("keywords_en", [])),
                )
            )
        except KeyError as e:
            raise ContentError(f"occupations.toml[{i}]: missing key {e}") from e
    return tuple(out)


@lru_cache(maxsize=1)
def occupation_codes() -> frozenset[str]:
    return frozenset(o.code for o in occupations())


def occupation(code: str) -> Occupation | None:
    for o in occupations():
        if o.code == code:
            return o
    return None


@lru_cache(maxsize=1)
def states() -> tuple[State, ...]:
    raw = _load_toml("states.toml").get("state", [])
    if not raw:
        raise ContentError("states.toml: no [[state]] blocks")
    return tuple(
        State(
            code=s["code"],
            label_hi=s["label_hi"],
            label_en=s["label_en"],
            aliases=tuple(s.get("aliases", [])),
            common=bool(s.get("common", False)),
        )
        for s in raw
    )


def match_state(text: str) -> State | None:
    """Match typed text to a state. Plain string work — no LLM, no network.

    # * Deliberately strict-ish: exact code, then exact label, then substring on
    # * labels and aliases. A wrong state is a wrong screening, so an unmatched
    # * answer re-asks with a button list rather than picking the closest guess.
    """
    t = text.strip().lower()
    if not t:
        return None
    for s in states():
        if t == s.code.lower() or t == s.label_hi.lower() or t == s.label_en.lower():
            return s
    hits = [
        s
        for s in states()
        if t in s.label_hi.lower()
        or t in s.label_en.lower()
        or any(t == a.lower() or t in a.lower() for a in s.aliases)
    ]
    # ! Ambiguous ("pradesh" matches six states) is not a match. Re-ask instead.
    return hits[0] if len(hits) == 1 else None


def match_occupation_offline(text: str) -> Occupation | None:
    """Keyword match for the no-LLM path. Result is ALWAYS confirmed by the user.

    Returns None rather than a weak guess — the caller then shows the menu.
    """
    t = text.strip().lower()
    if not t:
        return None
    best: tuple[int, Occupation] | None = None
    for o in occupations():
        score = sum(1 for k in o.keywords_hi if k in text)
        score += sum(1 for k in o.keywords_en if k in t)
        if score and (best is None or score > best[0]):
            best = (score, o)
    return best[1] if best else None


# ! Hindi is the default and the fallback. English exists because plenty of
# ! younger workers, and every CSC operator running this for someone, read
# ! English faster — but a missing English string must never blank the screen,
# ! so lookup falls back to Hindi rather than raising.
LANGS = ("hi", "en")
DEFAULT_LANG = "hi"


def normalise_lang(lang: str | None) -> str:
    return lang if lang in LANGS else DEFAULT_LANG


@lru_cache(maxsize=len(LANGS))
def strings(lang: str = DEFAULT_LANG) -> dict:
    """The whole of strings_<lang>.toml, as nested dicts."""
    return _load_toml(f"strings_{normalise_lang(lang)}.toml")


def _lookup(path: str, lang: str) -> str | None:
    node: object = strings(lang)
    for part in path.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node if isinstance(node, str) else None


def s(path: str, lang: str = DEFAULT_LANG, **fmt) -> str:
    """Fetch a dotted string path, e.g. s("consent.ask") or s("result.new_badge").

    Missing in the requested language → falls back to Hindi. Missing in Hindi
    too → raises, because that is a bug that must break the test run rather than
    appear in front of a worker as "{name_hi}".
    """
    lang = normalise_lang(lang)
    node = _lookup(path, lang)
    if node is None and lang != DEFAULT_LANG:
        node = _lookup(path, DEFAULT_LANG)
    if node is None:
        raise ContentError(f"strings_{lang}.toml: no string at {path!r}")
    if not fmt:
        return node
    try:
        return node.format(**fmt)
    except KeyError as e:
        raise ContentError(f"strings_{lang}.toml: {path!r} needs placeholder {e}") from e


def _self_check() -> None:
    assert occupation("construction").label_hi == "निर्माण मजदूर"
    assert "other" in occupation_codes()
    assert match_state("uttarakhand").code == "UK"
    assert match_state("उत्तराखंड").code == "UK"
    assert match_state("UP").code == "UP"
    assert match_state("नरनिया") is None, "unknown state must not resolve to a guess"
    assert match_state("pradesh") is None, "ambiguous input must not resolve"
    assert match_occupation_offline("मैं ईंट लगाता हूँ").code == "construction"
    assert match_occupation_offline("i drive a taxi").code == "transport"
    assert match_occupation_offline("zzzz") is None

    assert "योजना साथी" in s("consent.ask")
    assert "Yojana Sathi" in s("consent.ask", "en")
    assert s("result.new_badge") and s("result.new_badge", "en")
    got = s("confirm.occupation", said="ईंट", label="निर्माण मजदूर")
    assert "{" not in got, got
    assert "{" not in s("confirm.occupation", "en", said="bricks", label="Construction worker")

    # ! Every key in the Hindi file must exist in the English one. A half
    # ! translated screen is worse than either language on its own.
    def flat(d, prefix=""):
        out = set()
        for k, v in d.items():
            out |= flat(v, f"{prefix}{k}.") if isinstance(v, dict) else {f"{prefix}{k}"}
        return out

    missing = flat(strings("hi")) - flat(strings("en"))
    assert not missing, f"strings_en.toml is missing: {sorted(missing)}"
    assert normalise_lang("fr") == "hi" and normalise_lang("en") == "en"
    assert occupation("construction").label("en") == "Construction worker"

    for missing in ("nope.nope", "consent"):
        try:
            s(missing)
        except ContentError:
            pass
        else:
            raise AssertionError(f"s({missing!r}) should have raised")
    print("content.py OK")


if __name__ == "__main__":
    _self_check()
