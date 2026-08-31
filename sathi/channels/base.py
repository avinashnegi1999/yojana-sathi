"""Channel-agnostic message types.

# ! The conversation must never know it is talking to Telegram. WhatsApp is a
# ! week-8 maybe and Meta verification could stall for weeks — if the flow
# ! imported the Telegram client, that stall would block the deploy gate.
# ! Adapters are thin: they translate these two shapes and hold no logic.
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Button:
    """One tappable option. `value` is what the flow receives, not the label."""

    label: str
    value: str


@dataclass(frozen=True)
class ChannelMessage:
    """Something a worker did: typed text, or tapped a button.

    # ! `channel_key` identifies the CONVERSATION for the adapter's own routing
    # ! (Telegram chat id). It never reaches the event log — sessions there use
    # ! an unrelated uuid4. See sathi/metrics/events.py.
    """

    channel_key: str
    text: str = ""
    value: str = ""  # button payload, empty for typed text

    @property
    def answer(self) -> str:
        return self.value or self.text.strip()


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


@dataclass
class Outbox:
    """Replies produced by one turn. A turn may legitimately send several."""

    replies: list[Reply] = field(default_factory=list)

    def add(self, reply: Reply) -> None:
        self.replies.append(reply)
