"""Channel-agnostic message types.

# ! The conversation must never know it is talking to Telegram. WhatsApp is a
# ! week-8 maybe and Meta verification could stall for weeks — if the flow
# ! imported the Telegram client, that stall would block the deploy gate.
# ! Adapters are thin: they translate these two shapes and hold no logic.
# * (ChannelMessage and Outbox lived here too and were never used; removed
# * 2026-09-25. Adapters read their platform's payload directly.)
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Button:
    """One tappable option. `value` is what the flow receives, not the label."""

    label: str
    value: str


@dataclass
class Reply:
    """Something to send back. Text is always complete on its own."""

    text: str
    buttons: tuple[Button, ...] = ()
    audio: Path | None = None
    document: tuple[str, bytes] | None = None  # (filename, content)
    end: bool = False  # session is over after this

    def button_values(self) -> frozenset[str]:
        return frozenset(b.value for b in self.buttons)
