"""Consent, asked first, in plain Hindi, before anything is recorded.

# ! Consent is a gate in the code, not a screen we show and forget: the event
# ! log refuses every profile event until consent_granted lands for that session
# ! (sathi/metrics/events.py). This module is only the asking.
"""

from sathi.channels.base import Button, Reply
from sathi.core.content import s

YES = "consent_yes"
NO = "consent_no"


def ask(lang: str = "hi") -> Reply:
    return Reply(
        text=s("consent.ask", lang),
        buttons=(Button(s("consent.yes", lang), YES), Button(s("consent.no", lang), NO)),
    )


def declined(lang: str = "hi") -> Reply:
    """Nothing was stored and the message says so. The exit is not a failure."""
    return Reply(text=s("consent.declined", lang), end=True)


def _self_check() -> None:
    r = ask()
    assert r.button_values() == {YES, NO}
    assert not r.end and declined().end
    assert "Yojana Sathi" in ask("en").text and declined("en").end
    print("consent.py OK")


if __name__ == "__main__":
    _self_check()
