"""Everything about a conversation that is not the wire.

# ! Two adapters now. Every bug this project has shipped lived in the
# ! conversation/adapter boundary — the keyboard that answered the wrong
# ! question, the session dropped by a rate limit, the command that advanced
# ! the flow. There is one copy of that logic here, not one per channel, so a
# ! fix lands once and a new channel inherits it instead of re-earning it.
#
# * Not in base.py: the flow imports base.py for its message types, so a router
# * that builds Conversations cannot live there without a circular import.
#
# * An adapter supplies send() and, where the platform allows it, clear_chat().
# * It translates payloads. It decides nothing.
"""

import time

from sathi.channels.base import Reply
from sathi.conversation.flow import Conversation
from sathi.core.content import DEFAULT_LANG, LANGS, s
from sathi.core.schemes import Scheme
from sathi.metrics.events import SOURCE_SLUGS, EventLog

# * Commands are handled here, not in the flow, because they are a channel
# * affordance. The flow exposes plain methods; this maps slash words onto them.
COMMANDS = {
    "/start": "start", "/restart": "start",
    "/language": "language", "/lang": "language",
    "/help": "help", "/about": "about", "/privacy": "privacy",
    "/demo": "demo",
    "/schemes": "schemes", "/cancel": "cancel", "/stop": "cancel",
    "/clear": "clear", "/clearall": "clearall", "/clear_all": "clearall",
}

# ! Informational replies leave the live question alone. Every other turn
# ! answers, replaces or clears it, even when the state does not change.
INFO_COMMANDS = ("help", "about", "privacy", "schemes", "demo")


class Router:
    """Sessions, commands and the keyboard-retirement rule, for any channel."""

    # * Reaches the event log as the channel name, and the worker as the
    # * platform named in /privacy. Adapters override it.
    channel = "cli"

    # ! Idle limits (AUDIT.md M8). The README says a profile is discarded when
    # ! the screening ends; a worker who simply stopped replying used to leave
    # ! her age, widow status and disability answer in RAM until the next
    # ! restart, and every chat that ever wrote in stayed in these dicts forever.
    # ! After 30 quiet minutes the answers go. The language preference and the
    # ! /clear bookkeeping outlive the session, but not Telegram's own 48-hour
    # ! window for deleting messages.
    SESSION_IDLE_SECONDS = 30 * 60
    CHAT_IDLE_SECONDS = 48 * 60 * 60
    SWEEP_EVERY_SECONDS = 60

    def __init__(self, schemes: dict[str, Scheme], log: EventLog | None = None) -> None:
        self.schemes = schemes
        self.log = log
        self.sessions: dict[str, Conversation] = {}
        # ! The language outlives the session. A Conversation is rebuilt whenever
        # ! one ends — after /cancel, after a completed screening — and a fresh
        # ! one defaults to Hindi, so an English worker's /help came back in
        # ! Hindi. The choice is a preference, not session state.
        self._lang: dict[str, str] = {}
        # ! Only the current question's keyboard may answer this session. The
        # ! reference is whatever the platform uses to identify the message the
        # ! worker tapped: a Telegram message_id, a WhatsApp wamid.
        self._active_keyboard: dict[str, str | int] = {}
        # ! Where this person arrived from, remembered from "/start reddit"
        # ! until they consent — because the count is of people who agreed to
        # ! be counted, and that answer comes several questions later.
        self._source: dict[str, str] = {}
        # * When each chat last did anything. Drives expire_idle(); the clock
        # * is an attribute so the self-check can age a chat without sleeping.
        self._last_seen: dict[str, float] = {}
        self._next_sweep = 0.0
        self.clock = time.monotonic

    # * ---------------------------------------------------------- the wire

    def send(self, key: str, reply: Reply) -> None:
        """Deliver one reply. Supplied by the adapter."""
        raise NotImplementedError

    def clear_chat(self, key: str, lang: str = DEFAULT_LANG,
                   message_ref: str | int | None = None, deep: bool = False) -> Reply:
        """Delete this conversation's messages, if the platform allows it.

        # ! The default is a refusal, not a no-op. A worker who asks to erase a
        # ! conversation about their own poverty must be told plainly that it
        # ! did not happen, and what they can do instead.
        """
        return Reply(text=self._bilingual("commands.clear_unsupported", lang))

    def forget(self, key: str) -> None:
        """Drop whatever an adapter keeps per chat. Adapters with state override it."""

    # * ------------------------------------------------------------ idle expiry

    def expire_idle(self, key: str | None = None) -> None:
        """Drop state nobody has used recently. Call before looking at self.sessions.

        # * Checks `key` itself every time, so a tap on a 40-minute-old keyboard
        # * is refused as stale rather than answering a session that should be
        # * gone. Walks every chat at most once a minute.
        """
        now = self.clock()
        if key is not None and now - self._last_seen.get(key, now) > self.SESSION_IDLE_SECONDS:
            self.sessions.pop(key, None)
            self._active_keyboard.pop(key, None)
        if now < self._next_sweep:
            return
        self._next_sweep = now + self.SWEEP_EVERY_SECONDS
        for chat, seen in list(self._last_seen.items()):
            idle = now - seen
            if idle > self.SESSION_IDLE_SECONDS:
                self.sessions.pop(chat, None)
                self._active_keyboard.pop(chat, None)
            if idle > self.CHAT_IDLE_SECONDS:
                self._lang.pop(chat, None)
                self._source.pop(chat, None)
                self._last_seen.pop(chat, None)
                self.forget(chat)

    # * -------------------------------------------------------------- shared

    @staticmethod
    def _bilingual(key: str, lang: str, **fmt) -> str:
        """The same message in both languages, the worker's own first.

        # ! Used for the clear receipts. After a clear this may be the only
        # ! message left standing in the chat, with no earlier screen to give it
        # ! context — so it has to be readable whichever language the reader
        # ! has. Same reasoning as the language picker.
        """
        first = s(key, lang, **fmt)
        second = next(s(key, other, **fmt) for other in LANGS if other != lang)
        return f"{first}\n\n{second}" if first != second else first

    def _conversation(self, key: str, fresh: bool = False) -> Conversation:
        if fresh or key not in self.sessions:
            # * The arrival slug from the last /start, so a pilot session can be
            # * counted apart from testing (AUDIT.md C2). "" means a plain link.
            convo = Conversation(self.schemes, self.log, channel=self.channel,
                                 cohort=self._source.get(key) or None)
            if self.log is not None:
                convo.person = self.log.feedback_id(key)
            convo.lang = self._lang.get(key, DEFAULT_LANG)
            self.sessions[key] = convo
        return self.sessions[key]

    # ! Where a person arrived from, e.g. "/start reddit" behind
    # ! t.me/YojanaSathiBot?start=reddit. A short slug from a fixed set, so a
    # ! link cannot smuggle free text into the database.
    # * Paid placements get their own slugs so an ad's reach is separable from
    # * an organic post's. Link as t.me/YojanaSathiBot?start=linkedin.
    # * The list lives in sathi/metrics/events.py, beside the only writer, so
    # * the reach table and the events table can never accept different slugs.
    SOURCES = SOURCE_SLUGS

    def _remember_source(self, key: str, answer: str) -> None:
        payload = answer.strip().split()[1:2]
        slug = payload[0].strip().lower()[:20] if payload else ""
        # ! Every /start resets it. A plain /start after an earlier
        # ! "/start linkedin" is a direct visit, not a second LinkedIn one.
        self._source[key] = slug if slug in self.SOURCES else ""

    def _count_person(self, key: str, convo: Conversation) -> None:
        """One person, counted once, after they agreed to be counted.

        # ! Recorded here and not in Conversation because this is the only
        # ! layer that knows the channel id, and Conversation must never learn
        # ! it. The row it writes carries no session id, so the count can say
        # ! how many people and never which person answered what.
        """
        if self.log is None or not getattr(convo, "consent_granted", False):
            return
        # ! No in-memory "already counted" cache here. There was one, and it
        # ! silently diverged from the database the first time the table was
        # ! cleared: the row was gone, the process still believed the person was
        # ! counted, and they were never recorded again for the life of that
        # ! process. INSERT OR IGNORE on a primary key is the real guard and it
        # ! cannot drift; the hash it costs per message is not worth a second
        # ! source of truth.
        try:
            self.log.record_reach(key, self.channel, self._source.get(key, ""))
        except Exception as e:  # noqa: BLE001 — counting must never break a screening
            # ! Say so. A screening must not fail because the counter did, but a
            # ! counter that dies silently is worse than one that crashes: the
            # ! bot looks healthy, every worker is served, and the dashboard
            # ! quietly under-reports until the number reaches a judge.
            # ! Type name only — the message could carry a channel id.
            print(f"[metrics] reach write failed: {type(e).__name__}")

    def dispatch(self, key: str, answer: str,
                 message_ref: str | int | None = None) -> list[Reply]:
        """Slash command, or an answer to the question we asked."""
        word = answer.strip().split()[0].lower() if answer.strip() else ""
        command = COMMANDS.get(word)
        if command not in INFO_COMMANDS:
            self._active_keyboard.pop(key, None)
        if command is None:
            convo = self._conversation(key)
            replies = convo.handle(answer)
            self._count_person(key, convo)
            return replies

        if command == "demo":
            # ! No Conversation/EventLog session is created for fictional data.
            from sathi.demo import replies as demo_replies
            lang = self.sessions[key].lang if key in self.sessions else self._lang.get(key, DEFAULT_LANG)
            return demo_replies(self.schemes, lang)

        if command == "start":
            self._remember_source(key, answer)
            return self._conversation(key, fresh=True).start()

        convo = self._conversation(key)
        if command == "language":
            # * Toggle. Two languages means a switch needs no submenu.
            return convo.set_language("en" if convo.lang == "hi" else "hi")
        if command == "cancel":
            replies = convo.cancel()
            self.sessions.pop(key, None)
            return replies
        if command in ("clear", "clearall"):
            return [self.clear_chat(key, convo.lang, message_ref,
                                    deep=command == "clearall")]
        if command == "schemes":
            return convo.scheme_list()
        return convo.info(command)  # help | about | privacy

    def turn(self, key: str, answer: str,
             message_ref: str | int | None = None) -> None:
        """One answer in, replies out."""
        self.expire_idle(key)
        self._last_seen[key] = self.clock()
        replies = self.dispatch(key, answer, message_ref)
        # * Remember the language for whatever comes after this session ends.
        convo = self.sessions.get(key)
        if convo is not None:
            self._lang[key] = convo.lang
        for reply in replies:
            self.send(key, reply)
            if reply.end:
                # ! Session over: drop the profile from memory immediately. It is
                # ! never written anywhere, and now it is not held anywhere either.
                self.sessions.pop(key, None)
                self._active_keyboard.pop(key, None)

    def abandon(self, key: str) -> None:
        """Drop a conversation this bot can no longer reason about, and say so.

        # ! Only for a fault in OUR handling. The turn may have partly changed the
        # ! profile or sent only some replies, and replay could record answers
        # ! twice — so the answers go, and the worker is told to start again.
        # ! A transport failure is NOT this: see the callers.
        """
        convo = self.sessions.pop(key, None)
        self._active_keyboard.pop(key, None)
        lang = convo.lang if convo else self._lang.get(key, DEFAULT_LANG)
        self._lang[key] = lang
        self.send(key, Reply(text=s("errors.screening_stopped", lang)))


def _self_check() -> None:
    """The routing rules, with the wire replaced by a list."""
    from sathi.core.schemes import Criterion as C

    schemes = {"A": Scheme(
        code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
        verified_on="2026-09-01", verified_by="a",
        benefit={"annual_value_inr": 1000, "value_basis": "annual_payout", "summary_hi": "प"},
        criteria=(C("age", "between", [18, 40], "u", pass_hi="ok", fail_hi="no"),),
        exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
    )}

    class _Recorder(Router):
        channel = "test"

        def __init__(self) -> None:
            super().__init__(schemes)
            self.out: list[Reply] = []

        def send(self, key, reply):
            self.out.append(reply)

    bot = _Recorder()
    bot.turn("k", "/start")
    assert bot.out[-1].buttons, "the language question has no keyboard"
    bot._active_keyboard["k"] = 5

    # ! An info command must not disturb the live question or advance the flow.
    for command in ("/help", "/about", "/privacy", "/schemes"):
        bot.turn("k", command)
        assert bot._active_keyboard.get("k") == 5, command
    assert bot.sessions["k"].state.value == "language"

    # ! Everything else retires the keyboard, even when the state is unchanged.
    bot.turn("k", "nonsense")
    assert "k" not in bot._active_keyboard

    # * A channel that cannot delete its own messages says so, in both languages.
    refusal = bot.clear_chat("k", "en")
    assert "WhatsApp" not in refusal.text  # * the base text names no platform
    assert len(refusal.text.split("\n\n")) == 2, "the clear refusal is not bilingual"

    # ! Language survives the end of a session; a fresh Conversation used to
    # ! default to Hindi and answer an English worker in Hindi.
    bot.turn("k", "lang:en")
    assert bot._lang["k"] == "en"
    bot.turn("k", "/cancel")
    assert "k" not in bot.sessions
    assert bot._conversation("k").lang == "en"

    # ! A broken turn drops the session, retires the keyboard and says so.
    bot._active_keyboard["k"] = 9
    bot.abandon("k")
    assert "k" not in bot.sessions and "k" not in bot._active_keyboard
    assert "/start" in bot.out[-1].text

    # ! AUDIT.md M8: an idle session is dropped after 30 minutes, the chat's
    # ! remaining bookkeeping after 48 hours, and the adapter hears about it.
    now = [0.0]
    forgotten = []

    class _Aging(_Recorder):
        def forget(self, key):
            forgotten.append(key)

    idle = _Aging()
    idle.clock = lambda: now[0]
    idle.turn("w", "/start")
    idle.turn("w", "lang:en")
    assert "w" in idle.sessions
    now[0] += Router.SESSION_IDLE_SECONDS + 1
    idle.expire_idle("w")
    assert "w" not in idle.sessions, "a 31-minute-idle profile is still in memory"
    assert idle._lang["w"] == "en", "the language preference outlives the session"
    now[0] += Router.CHAT_IDLE_SECONDS
    idle.expire_idle()
    assert "w" not in idle._lang and "w" not in idle._last_seen and forgotten == ["w"]
    # * An active chat is never touched by the sweep.
    idle.turn("x", "/start")
    now[0] += Router.SWEEP_EVERY_SECONDS + 1
    idle.expire_idle()
    assert "x" in idle.sessions

    print("router.py OK")


if __name__ == "__main__":
    _self_check()
