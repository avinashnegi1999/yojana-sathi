"""Worker profile — the only data the rule engine reads.

# ! Deliberately minimal. A field that does not exist here cannot be stored by
# ! accident. There is no name, no phone number and no Aadhaar field anywhere in
# ! this project, and there never should be.
"""

from dataclasses import dataclass, fields


# * Bands, not values. We never hold an exact income or an exact age in the
# * event log — see sathi/metrics/. The exact age lives in the Profile only for
# * the duration of the session, because eligibility rules need it.

INCOME_BANDS = (
    # ! "No income at all" is its own band. It sits inside "up to ₹5,000"
    # ! arithmetically, but a worker with nothing coming in does not recognise
    # ! themselves in "up to ₹5,000" and may pick nothing, or pick wrong.
    "no_income",
    "upto_5000",
    "5001_10000",
    "10001_15000",
    "15001_25000",
    "above_25000",
)

LAND_HOLDING_BANDS = (
    "landless",
    "upto_1_hectare",
    "1_to_2_hectare",
    "above_2_hectare",
)

AGE_BANDS = (
    ("18-25", 18, 25),
    ("26-40", 26, 40),
    ("41-59", 41, 59),
    ("60+", 60, 200),
)


@dataclass
class Profile:
    """Held in process memory for one session, then discarded. Never persisted."""

    state: str | None = None                 # ! state only, never district or village
    age: int | None = None
    occupation: str | None = None            # enum, see data/occupations.toml
    income_band: str | None = None           # ! band, never an exact figure
    land_holding_band: str | None = None
    family_size: int | None = None
    has_bank_account: bool | None = None
    is_income_tax_payer: bool | None = None
    # ! Added because the researched exclusion lists need it, not speculatively:
    # ! PM-SYM bars members of NPS, ESIC and EPFO, and e-Shram defines an
    # ! unorganised worker as someone who is not an ESIC or EPFO member.
    # ? One field covers all three schemes. A worker who holds NPS but not
    # ? EPFO/ESIC is therefore also excluded from e-Shram, which is stricter
    # ? than e-Shram's own wording. Splitting the field is the fix if that case
    # ? ever shows up in the field — see docs/ARCHITECTURE.md.
    is_statutory_scheme_member: bool | None = None
    known_schemes: frozenset[str] = frozenset()  # ! drives the headline metric

    def age_band(self) -> str | None:
        """Coarsen age for the event log. Returns None if age is unknown."""
        if self.age is None:
            return None
        for label, lo, hi in AGE_BANDS:
            if lo <= self.age <= hi:
                return label
        # ? Under 18. No scheme we handle covers minors, but the band still has
        # ? to exist so the event log does not silently drop the session.
        return "under-18"

    def is_answered(self, field_name: str) -> bool:
        """True if the field has a value. Used by the engine to decide UNKNOWN."""
        if field_name == "known_schemes":
            return True  # * empty set is a real answer: "I have none of these"
        return getattr(self, field_name, None) is not None


# ! The engine validates every scheme rule against this set at load time, so a
# ! scheme file cannot reference a field we never ask about.
PROFILE_FIELDS = frozenset(f.name for f in fields(Profile))


def _self_check() -> None:
    p = Profile(age=34, income_band="5001_10000")
    assert p.age_band() == "26-40", p.age_band()
    assert Profile(age=60).age_band() == "60+"
    assert Profile(age=17).age_band() == "under-18"
    assert Profile().age_band() is None
    assert p.is_answered("age") and not p.is_answered("state")
    assert p.is_answered("known_schemes"), "empty known_schemes is a real answer"
    assert "age" in PROFILE_FIELDS and "aadhaar" not in PROFILE_FIELDS
    assert "is_statutory_scheme_member" in PROFILE_FIELDS
    print("profile.py OK")


if __name__ == "__main__":
    _self_check()
