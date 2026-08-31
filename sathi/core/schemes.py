"""Load and validate scheme rule files from data/schemes/*.toml.

# * Two kinds of problem, handled very differently:
# *   STRUCTURAL  — unknown key, bad operator, a field we never ask about.
# *                 Raises SchemeError. The app refuses to start.
# *   UNVERIFIED  — a value still reads "TODO" because nobody has researched it.
# *                 Loads fine, but the scheme is flagged and the rule engine
# *                 must return UNKNOWN for it rather than guess.
#
# ! That split is the whole anti-hallucination mechanism. A missing threshold
# ! never becomes a plausible default; it becomes a visible admission.
"""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from sathi.core.profile import PROFILE_FIELDS

# ! Every stub in a scheme file is this exact string, whatever the real type
# ! would be. `annual_value_inr = "TODO"` is detectable; `= 0` is not.
STUB = "TODO"

OPERATORS = frozenset({"between", "in", "not_in", "lte", "gte", "eq", "exists"})

# ! "gateway" exists because e-Shram turned out to be a registration and a UAN,
# ! not a benefit with a ₹ value of its own. Giving it a rupee figure would
# ! double-count the PMSBY cover it unlocks.
VALUE_BASES = frozenset(
    {"annual_payout", "insurance_cover", "one_time", "subsidy", "gateway"}
)

APPLY_LOCATIONS = frozenset(
    {"csc", "bank_branch", "post_office", "eshram_centre", "online"}
)

_TOP_KEYS = frozenset(
    {
        "code", "name_en", "name_hi", "authority", "official_url",
        "verified_on", "verified_by", "benefit", "paperwork",
        "criteria", "exclusions", "prerequisites",
    }
)
_TOP_REQUIRED = _TOP_KEYS - {"exclusions", "prerequisites"}

# ! Paperwork lives in its own table on purpose. In TOML a bare key written
# ! after a [[table]] header belongs to that table, so top-level keys placed at
# ! the bottom of the file silently land inside the last [[exclusions]] block.
_PAPERWORK_KEYS = frozenset({"documents", "where_to_apply", "renewal"})
# * English is optional everywhere. A scheme file authored only in Hindi still
# * loads and still works — the English screen falls back to the Hindi text
# * rather than showing a blank line. Missing translation, never missing fact.
_PAPERWORK_OPTIONAL = frozenset({"documents_en", "renewal_en"})

_BENEFIT_KEYS = frozenset(
    {"annual_value_inr", "value_basis", "premium_inr", "summary_hi", "summary_en"}
)

_CRITERION_KEYS = frozenset(
    {"field", "op", "value", "ask_hi", "pass_hi", "fail_hi", "source_url"}
)
_CRITERION_OPTIONAL = frozenset({"ask_en", "pass_en", "fail_en"})

_EXCLUSION_KEYS = frozenset({"field", "op", "value", "reason_hi", "source_url"})
_EXCLUSION_OPTIONAL = frozenset({"reason_en"})


class SchemeError(Exception):
    """A scheme file is structurally wrong. Fix the file; do not catch this."""


@dataclass(frozen=True)
class Criterion:
    field: str
    op: str
    value: object
    source_url: str
    ask_hi: str = ""
    pass_hi: str = ""
    fail_hi: str = ""
    reason_hi: str = ""
    ask_en: str = ""
    pass_en: str = ""
    fail_en: str = ""
    reason_en: str = ""

    def text(self, kind: str, lang: str = "hi") -> str:
        """One authored line — 'pass', 'fail', 'reason' or 'ask' — in a language.

        # ! Falls back to Hindi when the English is missing. A criterion with no
        # ! authored text at all returns "", and the caller then says nothing
        # ! rather than inventing a reason.
        """
        if lang == "en":
            return getattr(self, f"{kind}_en", "") or getattr(self, f"{kind}_hi", "")
        return getattr(self, f"{kind}_hi", "")


@dataclass(frozen=True)
class Scheme:
    code: str
    name_en: str
    name_hi: str
    authority: str
    official_url: str
    verified_on: str
    verified_by: str
    benefit: dict
    criteria: tuple[Criterion, ...]
    exclusions: tuple[Criterion, ...]
    documents: tuple[str, ...]
    where_to_apply: str
    renewal: str
    documents_en: tuple[str, ...] = ()
    renewal_en: str = ""
    prerequisites: tuple[str, ...] = ()
    # ! Dotted paths of every value still reading "TODO". Empty means research
    # ! is complete and the engine may return a real verdict.
    stubs: tuple[str, ...] = ()
    source_path: str = ""

    @property
    def is_verified(self) -> bool:
        return not self.stubs

    def name(self, lang: str = "hi") -> str:
        return self.name_en if lang == "en" and self.name_en else self.name_hi

    def summary(self, lang: str = "hi") -> str:
        key = "summary_en" if lang == "en" else "summary_hi"
        value = self.benefit.get(key) or self.benefit.get("summary_hi") or ""
        return value if isinstance(value, str) else ""

    def docs(self, lang: str = "hi") -> tuple[str, ...]:
        # ! Only use the English list if it is the same length. A mismatched
        # ! translation would pair a document with the wrong "do you have it?"
        # ! answer, because the flow tracks documents by position.
        if lang == "en" and len(self.documents_en) == len(self.documents):
            return self.documents_en
        return self.documents

    def annual_value_inr(self) -> int:
        """₹ figure for the impact metric. 0 while unverified — never a guess."""
        v = self.benefit.get("annual_value_inr")
        return v if isinstance(v, int) else 0


def _find_stubs(node, path: str = "") -> list[str]:
    """Walk the parsed TOML and collect the dotted path of every STUB value."""
    found = []
    if isinstance(node, dict):
        for k, v in node.items():
            found += _find_stubs(v, f"{path}.{k}" if path else k)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found += _find_stubs(v, f"{path}[{i}]")
    elif node == STUB:
        found.append(path)
    return found


def _require_keys(got, allowed, required, where: str) -> None:
    got = set(got)
    unknown = got - allowed
    if unknown:
        raise SchemeError(f"{where}: unknown key(s) {sorted(unknown)}")
    missing = required - got
    if missing:
        raise SchemeError(f"{where}: missing key(s) {sorted(missing)}")


def _check_str(value, where: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SchemeError(f"{where}: expected a non-empty string, got {value!r}")


def _parse_criterion(raw: dict, where: str, *, exclusion: bool) -> Criterion:
    keys = _EXCLUSION_KEYS if exclusion else _CRITERION_KEYS
    optional = _EXCLUSION_OPTIONAL if exclusion else _CRITERION_OPTIONAL
    _require_keys(raw, keys | optional, keys, where)

    if raw["field"] not in PROFILE_FIELDS and raw["field"] != STUB:
        raise SchemeError(
            f"{where}: field {raw['field']!r} is not a Profile field. "
            f"Add it to sathi/core/profile.py first, or fix the typo."
        )
    if raw["op"] not in OPERATORS and raw["op"] != STUB:
        raise SchemeError(f"{where}: unknown op {raw['op']!r}, expected one of {sorted(OPERATORS)}")

    # * Shape of `value` has to match the operator, but only once it is real.
    v = raw["value"]
    if v != STUB:
        if raw["op"] == "between":
            if not (isinstance(v, list) and len(v) == 2):
                raise SchemeError(f"{where}: op 'between' needs a [low, high] pair, got {v!r}")
            if any(x != STUB and not isinstance(x, (int, float)) for x in v):
                raise SchemeError(f"{where}: 'between' bounds must be numbers, got {v!r}")
        elif raw["op"] in ("in", "not_in") and not isinstance(v, list):
            raise SchemeError(f"{where}: op {raw['op']!r} needs a list, got {v!r}")
        elif raw["op"] in ("lte", "gte") and not isinstance(v, (int, float)):
            raise SchemeError(f"{where}: op {raw['op']!r} needs a number, got {v!r}")

    for k in keys - {"field", "op", "value"}:
        _check_str(raw[k], f"{where}.{k}")
    for k in optional:
        if k in raw:
            _check_str(raw[k], f"{where}.{k}")

    return Criterion(
        field=raw["field"],
        op=raw["op"],
        value=v,
        source_url=raw["source_url"],
        ask_hi=raw.get("ask_hi", ""),
        pass_hi=raw.get("pass_hi", ""),
        fail_hi=raw.get("fail_hi", ""),
        reason_hi=raw.get("reason_hi", ""),
        ask_en=raw.get("ask_en", ""),
        pass_en=raw.get("pass_en", ""),
        fail_en=raw.get("fail_en", ""),
        reason_en=raw.get("reason_en", ""),
    )


def load_scheme(path: Path) -> Scheme:
    """Parse and validate one scheme file. Raises SchemeError on bad structure."""
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as e:
        raise SchemeError(f"{path.name}: not valid TOML — {e}") from e

    where = path.name
    _require_keys(raw, _TOP_KEYS, _TOP_REQUIRED, where)

    for k in ("code", "name_en", "name_hi", "authority", "official_url",
              "verified_on", "verified_by"):
        _check_str(raw[k], f"{where}.{k}")

    _require_keys(raw["benefit"], _BENEFIT_KEYS, _BENEFIT_KEYS, f"{where}.benefit")
    b = raw["benefit"]
    # ! annual_value_inr stays strictly an integer: it feeds the headline metric
    # ! and a string there would silently become 0 in a total.
    if b["annual_value_inr"] != STUB and not isinstance(b["annual_value_inr"], int):
        raise SchemeError(
            f"{where}.benefit.annual_value_inr: expected ₹ as an integer, "
            f"got {b['annual_value_inr']!r}"
        )
    # * premium_inr may be a sentence instead of a number, because some schemes
    # * really do charge by entry age — PM-SYM is ₹55/month at 18 and ₹200 at 40.
    # * It is never summed, only shown, so prose is safe here. It must still be
    # * non-empty: an empty string would read as "free".
    if b["premium_inr"] != STUB and not isinstance(b["premium_inr"], (int, str)):
        raise SchemeError(
            f"{where}.benefit.premium_inr: expected ₹ as an integer, or a short "
            f"description when it varies, got {b['premium_inr']!r}"
        )
    if isinstance(b["premium_inr"], str) and not b["premium_inr"].strip():
        raise SchemeError(f"{where}.benefit.premium_inr: empty string reads as free")
    if b["value_basis"] != STUB and b["value_basis"] not in VALUE_BASES:
        raise SchemeError(
            f"{where}.benefit.value_basis: {b['value_basis']!r} not in {sorted(VALUE_BASES)}"
        )
    _require_keys(raw["paperwork"], _PAPERWORK_KEYS | _PAPERWORK_OPTIONAL,
                  _PAPERWORK_KEYS, f"{where}.paperwork")
    pw = raw["paperwork"]
    for k in ("where_to_apply", "renewal"):
        _check_str(pw[k], f"{where}.paperwork.{k}")
    if pw["where_to_apply"] != STUB and pw["where_to_apply"] not in APPLY_LOCATIONS:
        raise SchemeError(
            f"{where}.paperwork.where_to_apply: {pw['where_to_apply']!r} "
            f"not in {sorted(APPLY_LOCATIONS)}"
        )

    if not isinstance(raw["criteria"], list) or not raw["criteria"]:
        raise SchemeError(f"{where}: needs at least one [[criteria]] block")
    if not isinstance(pw["documents"], list) or not pw["documents"]:
        raise SchemeError(f"{where}.paperwork: needs a non-empty documents list")

    criteria = tuple(
        _parse_criterion(c, f"{where}.criteria[{i}]", exclusion=False)
        for i, c in enumerate(raw["criteria"])
    )
    exclusions = tuple(
        _parse_criterion(c, f"{where}.exclusions[{i}]", exclusion=True)
        for i, c in enumerate(raw.get("exclusions", []))
    )

    return Scheme(
        code=raw["code"],
        name_en=raw["name_en"],
        name_hi=raw["name_hi"],
        authority=raw["authority"],
        official_url=raw["official_url"],
        verified_on=raw["verified_on"],
        verified_by=raw["verified_by"],
        benefit=b,
        criteria=criteria,
        exclusions=exclusions,
        documents=tuple(pw["documents"]),
        where_to_apply=pw["where_to_apply"],
        renewal=pw["renewal"],
        documents_en=tuple(pw.get("documents_en", [])),
        renewal_en=pw.get("renewal_en", ""),
        prerequisites=tuple(raw.get("prerequisites", [])),
        stubs=tuple(_find_stubs(raw)),
        source_path=str(path),
    )


def load_all(directory: Path | str = "data/schemes") -> dict[str, Scheme]:
    """Load every scheme file. Files starting with '_' are templates, skipped."""
    directory = Path(directory)
    schemes: dict[str, Scheme] = {}
    for path in sorted(directory.glob("*.toml")):
        if path.name.startswith("_"):
            continue
        scheme = load_scheme(path)
        if scheme.code in schemes:
            raise SchemeError(f"duplicate scheme code {scheme.code!r} in {path.name}")
        schemes[scheme.code] = scheme
    return schemes
