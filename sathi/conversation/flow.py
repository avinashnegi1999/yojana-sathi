"""The intake state machine. Asks, records, then hands off to the engine.

# ! This module collects answers and emits events. It decides NOTHING about
# ! eligibility — that is sathi/rules/engine.py, and the separation is what lets
# ! a reviewer audit every rule in one place.
#
# * Explicit states and one branch per state, on purpose. A table-driven version
# * would be shorter and much harder to defend line by line to anyone asking
# * "what exactly do you ask, and in what order?".
#
# * Every question works with buttons alone. Typed input is accepted where it is
# * genuinely easier (age, state) but never REQUIRED, and free-text occupation
# * always ends in a confirmation before anything is recorded.
"""

from dataclasses import replace
from enum import Enum

from sathi.channels.base import Button, Reply
from sathi.conversation import consent
from sathi.core import content
from sathi.core.content import s
from sathi.core.profile import INCOME_BANDS, LAND_HOLDING_BANDS, Profile
from sathi.core.schemes import Scheme
from sathi.metrics.events import EventLog
from sathi.pack import checklist, pack
from sathi.render import llm, templates
from sathi.rules.engine import Verdict, evaluate_all


class State(Enum):
    LANGUAGE = "language"
    CONSENT = "consent"
    STATE = "state"
    AGE = "age"
    OCCUPATION = "occupation"
    OCCUPATION_FREE = "occupation_free"
    OCCUPATION_CONFIRM = "occupation_confirm"
    INCOME = "income_band"
    LAND = "land_holding_band"
    FAMILY = "family_size"
    BANK = "has_bank_account"
    TAX = "is_income_tax_payer"
    TAX_CONFIRM = "tax_confirm"
    TAX_INCOME = "tax_income"
    EPFO_ESIC = "is_epfo_or_esic_member"
    NPS = "nps_exclusion_applies"
    WORKER = "is_unorganised_worker"
    FOLLOWUP = "followup"
    KNOWN_SCHEMES = "known_schemes"
    DOCUMENTS = "documents"
    PACK = "pack"
    RATING = "rating"
    SUGGESTION = "suggestion"
    DONE = "done"


EXTRA_FIELDS = ('is_woman', 'is_widow', 'uk_pension_income_or_bpl', 'receives_other_pension', 'uk_pension_selected', 'household_has_lpg', 'pmuy_declaration_met')

YES, NO, DK = "yes", "no", "dont_know"
NEXT, OTHER, NONE = "next", "other", "none"
SKIP = "skip"
LANG_HI, LANG_EN = "lang:hi", "lang:en"


def _yes_no(lang: str, *, with_dont_know: bool = False) -> tuple[Button, ...]:
    out = [Button(s("buttons.yes", lang), YES), Button(s("buttons.no", lang), NO)]
    if with_dont_know:
        # ! "Don't know" is a real answer that leaves the field unset, which the
        # ! engine turns into UNKNOWN. Forcing a yes/no here would manufacture a
        # ! fact and the verdict built on it would be confidently wrong.
        out.append(Button(s("buttons.dont_know", lang), DK))
    return tuple(out)


class Conversation:
    """One worker, one screening. Held in memory, discarded when it ends."""

    def __init__(
        self,
        schemes: dict[str, Scheme],
        log: EventLog | None = None,
        channel: str = "cli",
    ) -> None:
        self.schemes = schemes
        self.log = log
        self.channel = channel
        self.session = log.start_session(channel) if log else None
        self.profile = Profile()
        self.lang = content.DEFAULT_LANG
        self.state = State.LANGUAGE
        self._pending_occupation: str | None = None  # LLM/keyword guess, unconfirmed
        self._said_occupation = ""
        self._known: set[str] = set()
        self._have_docs: set[str] = set()
        self._required_docs: tuple[str, ...] = ()
        self._document_page = 0
        self._results: tuple = ()
        # * Set once the worker agrees to anonymous metrics. The adapter uses
        # * it to count one unique person, in a table that has no session id.
        self.consent_granted = False
        self._rating: int | None = None
        self._followup_fields: list[str] = []
        self._followup_index = 0

    # * ------------------------------------------------------------- plumbing

    def _s(self, path: str, **fmt) -> str:
        """Every user-facing string, in whichever language the worker picked."""
        return s(path, self.lang, **fmt)

    def _event(self, event_type: str, **kw) -> None:
        if self.log and self.session:
            self.log.log(self.session, event_type, profile=self.profile, **kw)

    def _set(self, field: str, value) -> None:
        """Record one answer, then log that a field was captured — never its value."""
        self.profile = replace(self.profile, **{field: value})
        self._event("profile_field_captured")

    # * -------------------------------------------------------------- asking

    def start(self) -> list[Reply]:
        # ! Language first, asked in BOTH languages. A worker who cannot read the
        # ! question cannot answer it.
        self.state = State.LANGUAGE
        return [
            Reply(
                text=s("language.ask", self.lang),
                buttons=(Button(s("language.hindi", "hi"), LANG_HI),
                         Button(s("language.english", "en"), LANG_EN)),
            )
        ]

    def _on_language(self, answer: str) -> list[Reply]:
        if answer not in (LANG_HI, LANG_EN):
            return self.start()
        self.lang = content.normalise_lang(answer.split(":", 1)[1])
        self.state = State.CONSENT
        return [consent.ask(self.lang)]

    def set_language(self, lang: str) -> list[Reply]:
        """/language — switch mid-conversation, keeping every answer given so far."""
        was = self.lang
        self.lang = content.normalise_lang(lang)
        if was != self.lang and self._required_docs:
            self._relabel_documents(was)
        return [Reply(text=self._s("language.changed")), self._current_question()]

    def _relabel_documents(self, was: str) -> None:
        """Carry document answers across a language switch.

        # ! Both the buttons and the pack look documents up BY NAME, and the name
        # ! is language-specific. Without this, switching language after ticking
        # ! documents left the chat saying the worker had everything while the
        # ! pack listed the same documents as missing — the worker walks to the
        # ! centre unprepared, which is the exact trip this project exists to
        # ! make worthwhile.
        # * Pair by position WITHIN each scheme, never by index into the deduped
        # * required list: that list drops repeats, and two schemes can share a
        # * document name in one language without sharing it in the other, so the
        # * two lists are not guaranteed to be the same length. Scheme.docs()
        # * already refuses to use a translation of a different length, so
        # * position within one scheme is the one pairing that is always sound.
        """
        rename: dict[str, str] = {}
        for scheme in self.schemes.values():
            for before, after in zip(scheme.docs(was), scheme.docs(self.lang)):
                rename[before] = after
        self._have_docs = {rename.get(d, d) for d in self._have_docs}
        self._required_docs = checklist.required_documents(
            self._results, self.schemes, self.lang)

    def _current_question(self) -> Reply:
        """Re-ask whatever we are waiting on, in the current language."""
        asker = {
            State.LANGUAGE: lambda: self.start()[0],
            State.CONSENT: lambda: consent.ask(self.lang),
            State.STATE: self._ask_state,
            State.AGE: lambda: Reply(text=self._s("questions.age")),
            State.OCCUPATION: self._ask_occupation,
            State.OCCUPATION_FREE: lambda: Reply(text=self._s("questions.occupation_free")),
            State.OCCUPATION_CONFIRM: self._ask_occupation,
            State.INCOME: self._ask_income,
            State.TAX_INCOME: self._ask_income,
            State.LAND: self._ask_land,
            State.FAMILY: self._ask_family,
            State.BANK: lambda: Reply(text=self._s("questions.has_bank_account"),
                                      buttons=_yes_no(self.lang)),
            State.TAX: lambda: Reply(text=self._s("questions.is_income_tax_payer"),
                                     buttons=_yes_no(self.lang, with_dont_know=True)),
            State.TAX_CONFIRM: self._ask_tax_confirm,
            State.EPFO_ESIC: lambda: Reply(
                text=self._s("questions.is_epfo_or_esic_member"),
                buttons=_yes_no(self.lang, with_dont_know=True)),
            State.NPS: self._ask_nps,
            State.FOLLOWUP: self._ask_followup,
            State.KNOWN_SCHEMES: self._ask_known_schemes,
            State.WORKER: lambda: Reply(
                text=self._s("questions.is_unorganised_worker"),
                buttons=_yes_no(self.lang, with_dont_know=True)),
            State.DOCUMENTS: self._ask_documents,
            State.PACK: lambda: Reply(text=self._s("pack.offer"), buttons=_yes_no(self.lang)),
            State.RATING: lambda: Reply(text=self._s("feedback.ask_rating"),
                                        buttons=(Button(self._s("feedback.skip"), SKIP),)),
            State.SUGGESTION: lambda: Reply(text=self._s("feedback.ask_suggestion"),
                                            buttons=(Button(self._s("feedback.skip"), SKIP),)),
            State.DONE: lambda: Reply(text=self._s("closing.done"), end=True),
        }[self.state]
        # * OCCUPATION_CONFIRM re-asks the menu rather than the confirmation: the
        # * pending guess is dropped on a language switch, which is the safe
        # * direction — an unconfirmed guess must never survive quietly.
        if self.state is State.OCCUPATION_CONFIRM:
            self._pending_occupation = None
            self.state = State.OCCUPATION
        return asker()

    # * ------------------------------------------------------------- commands

    def info(self, topic: str) -> list[Reply]:
        """/help, /about, /privacy — static text, no state change."""
        text = self._s(f"commands.{topic}")
        if topic == "help":
            text += "\n" + self._s("demo.help")
        return [Reply(text=text)]

    def scheme_list(self) -> list[Reply]:
        """/schemes — every scheme, its official source, and when it was checked.

        # ! Provenance handed to the worker, not just to a judge. Someone who can
        # ! open the source URL can check us; someone who cannot at least sees
        # ! that a source exists and is dated.
        """
        replies = [Reply(text=self._s("commands.schemes_header"))]
        for code, sc in self.schemes.items():
            lines = [self._s("commands.schemes_line", name=sc.name(self.lang),
                                 code=code, url=sc.official_url,
                                 verified_on=sc.verified_on)]
            # ! Covers both unfinished states — a leftover TODO and a file
            # ! nobody has signed off. Gating this on `sc.stubs` alone showed a
            # ! clean provenance line for schemes served as UNKNOWN.
            if not sc.is_servable:
                lines.append(self._s("commands.schemes_unverified"))
            replies.append(Reply(text="\n".join(lines)))
        return replies

    def cancel(self) -> list[Reply]:
        """/cancel — drop the profile now, not at the end of the session."""
        self.profile = Profile()
        self._known.clear()
        self._followup_fields.clear()
        self._followup_index = 0
        self._have_docs.clear()
        self._results = ()
        self.state = State.DONE
        return [Reply(text=self._s("commands.cancelled"), end=True)]

    def _ask_state(self) -> Reply:
        buttons = tuple(
            Button(st.label(self.lang), f"state:{st.code}")
            for st in content.states() if st.common
        )
        return Reply(text=self._s("questions.state"), buttons=buttons)

    def _ask_occupation(self) -> Reply:
        buttons = tuple(
            Button(o.button_label(self.lang), f"occ:{o.code}")
            for o in content.occupations()
            if o.code != "other"
        ) + (Button(self._s("buttons.other"), OTHER),)
        return Reply(text=self._s("questions.occupation"), buttons=buttons)

    def _ask_income(self) -> Reply:
        return Reply(
            text=self._s("questions.income_band"),
            buttons=tuple(Button(self._s(f"income_bands.{b}"), f"inc:{b}")
                          for b in INCOME_BANDS),
        )

    def _ask_tax_confirm(self) -> Reply:
        # ! Every tax Yes gets the same neutral check. The income band is
        # ! context, never evidence that the worker's tax answer is wrong.
        return Reply(
            text=self._s("confirm.tax", income=self._s(f"income_bands.{self.profile.income_band}")),
            buttons=(Button(self._s("confirm.keep_both"), "tax:keep"),
                     Button(self._s("confirm.change_income"), "tax:income"),
                     Button(self._s("confirm.change_tax"), "tax:answer")),
        )

    def _ask_land(self) -> Reply:
        return Reply(
            text=self._s("questions.land_holding_band"),
            buttons=tuple(Button(self._s(f"land_bands.{b}"), f"land:{b}")
                          for b in LAND_HOLDING_BANDS),
        )

    def _ask_family(self) -> Reply:
        return Reply(
            text=self._s("questions.family_size"),
            buttons=tuple(Button(str(n), f"fam:{n}") for n in range(1, 9))
            + (Button("9+", "fam:9"),),
        )

    def _ask_known_schemes(self) -> Reply:
        """The question the headline metric depends on. It ships in v1, always."""
        buttons = tuple(
            Button(
                ("✅ " if code in self._known else "") + sc.name(self.lang),
                f"known:{code}",
            )
            for code, sc in self.schemes.items()
        ) + (Button(self._s("buttons.none_of_these"), NONE), Button(self._s("buttons.next"), NEXT))
        return Reply(text=self._s("questions.known_schemes"), buttons=buttons)

    def _ask_documents(self) -> Reply:
        # * Eight documents leave room for page navigation and Continue in
        # * WhatsApp's ten-row list. IDs remain absolute across pages.
        page_count = max(1, (len(self._required_docs) + 7) // 8)
        self._document_page %= page_count
        start = self._document_page * 8
        buttons = tuple(
            Button(("✅ " if d in self._have_docs else "") + d, f"doc:{i}")
            for i, d in enumerate(self._required_docs)
            if start <= i < start + 8
        )
        if page_count > 1:
            buttons += (Button(self._s("buttons.show_more"), "docs:more"),)
        buttons += (Button(self._s("buttons.next"), NEXT),)
        return Reply(text=self._s("documents.ask_which"), buttons=buttons)

    # * -------------------------------------------------------------- turning

    def handle(self, answer: str) -> list[Reply]:
        """One worker turn in, one or more replies out."""
        answer = (answer or "").strip()
        handler = getattr(self, f"_on_{self.state.value}", None)
        if handler is None:
            return [Reply(text=self._s("errors.generic"), end=True)]
        return handler(answer)

    def _on_consent(self, answer: str) -> list[Reply]:
        if answer == consent.NO or answer == NO:
            if self.log and self.session:
                self.log.decline_consent(self.session)
            self.state = State.DONE
            return [consent.declined(self.lang)]
        if answer != consent.YES and answer != YES:
            return [consent.ask(self.lang)]
        # ! Read by the channel adapter, which is the only layer that knows who
        # ! it is talking to. The Conversation itself never learns the channel
        # ! id — that separation is the whole reason sessions are unlinkable.
        self.consent_granted = True
        if self.log and self.session:
            self.log.grant_consent(self.session)
        self.state = State.STATE
        return [self._ask_state()]

    def _on_state(self, answer: str) -> list[Reply]:
        code = None
        if answer.startswith("state:"):
            code = answer.split(":", 1)[1]
        else:
            match = content.match_state(answer)
            code = match.code if match else None
        if code not in {st.code for st in content.states()}:
            # * No guessing at a half-recognised state. Re-ask with the buttons.
            retry = self._ask_state()
            return [Reply(text=self._s("questions.state_retry"), buttons=retry.buttons)]
        self._set("state", code)
        self.state = State.AGE
        return [Reply(text=self._s("questions.age"))]

    def _on_age(self, answer: str) -> list[Reply]:
        # ! Reject the whole input, never repair it. Stripping non-digits turned
        # ! "9.5" into 95 and "-5" into 5 — a silently wrong age changes which
        # ! schemes a worker is told about, and nothing in the chat shows it.
        # * isdecimal(), not isdigit(): isdigit() accepts superscripts like "²",
        # * which int() then rejects with ValueError. isdecimal() still accepts
        # * Devanagari "३४" and Arabic-Indic "٣٤", which this bot's users type.
        digits = answer.strip()
        if len(digits) > 3 or not digits.isdecimal() or not (1 <= int(digits) <= 120):
            return [Reply(text=self._s("questions.age_retry"))]
        self._set("age", int(digits))
        self.state = State.OCCUPATION
        return [self._ask_occupation()]

    def _on_occupation(self, answer: str) -> list[Reply]:
        if answer.startswith("occ:"):
            code = answer.split(":", 1)[1]
            if code in content.occupation_codes():
                self._set("occupation", code)
                self.state = State.INCOME
                return [self._ask_income()]
        if answer == OTHER:
            self.state = State.OCCUPATION_FREE
            return [Reply(text=self._s("questions.occupation_free"))]
        # * Typed something instead of tapping: treat it as free text.
        if answer and not answer.startswith("occ:"):
            self.state = State.OCCUPATION_FREE
            return self._on_occupation_free(answer)
        return [self._ask_occupation()]

    # ! A typed answer is the only unbounded thing a worker can put into the
    # ! system, and it gets echoed straight back on the confirmation screen. A
    # ! 4000-character paste would blow past Telegram's message limit and the
    # ! send would fail with a bare 400, killing the session mid-conversation.
    # ! No real occupation needs more than this.
    MAX_TYPED_CHARS = 200

    def _on_occupation_free(self, answer: str) -> list[Reply]:
        """Free text → a PROPOSAL. Nothing is recorded until the worker agrees."""
        if not answer:
            return [Reply(text=self._s("questions.occupation_free"))]
        answer = answer[:self.MAX_TYPED_CHARS]
        self._said_occupation = answer
        # * LLM first when a key is set, plain keywords otherwise. Both paths end
        # * at the same confirmation screen — that is what makes the LLM optional.
        code = llm.propose_occupation(answer)
        if not code:
            guess = content.match_occupation_offline(answer)
            code = guess.code if guess else None
        if not code:
            # ! Never bounce back to the same menu. The menu's own "something
            # ! else" leads here, so re-showing it is a loop with no exit — a
            # ! real tester hit it on the first run with "i dont do any job".
            # ! Offer to record it as "something else", which is a real category
            # ! and still ends in a confirmation the worker can refuse.
            code = "other"
        self._pending_occupation = code
        self.state = State.OCCUPATION_CONFIRM
        occ = content.occupation(code)
        return [
            Reply(
                text=self._s("confirm.occupation", said=answer, label=occ.label(self.lang)),
                buttons=(Button(self._s("buttons.correct"), YES), Button(self._s("buttons.wrong"), NO)),
            )
        ]

    def _on_occupation_confirm(self, answer: str) -> list[Reply]:
        if answer == YES and self._pending_occupation:
            self._set("occupation", self._pending_occupation)
            self._event("occupation_clarified")
            self._pending_occupation = None
            self.state = State.INCOME
            return [self._ask_income()]
        # ! Rejected guess is thrown away, not "close enough". Back to the menu.
        self._pending_occupation = None
        self.state = State.OCCUPATION
        return [Reply(text=self._s("confirm.rejected")), self._ask_occupation()]

    def _on_income_band(self, answer: str) -> list[Reply]:
        band = answer.split(":", 1)[1] if answer.startswith("inc:") else answer
        if band not in INCOME_BANDS:
            return [Reply(text=self._s("errors.pick_from_list"), buttons=self._ask_income().buttons)]
        self._set("income_band", band)
        if self.state is State.TAX_INCOME:
            self.state = State.TAX_CONFIRM
            return [self._ask_tax_confirm()]
        self.state = State.LAND
        return [self._ask_land()]

    def _on_tax_income(self, answer: str) -> list[Reply]:
        return self._on_income_band(answer)

    def _on_land_holding_band(self, answer: str) -> list[Reply]:
        band = answer.split(":", 1)[1] if answer.startswith("land:") else answer
        if band not in LAND_HOLDING_BANDS:
            return [Reply(text=self._s("errors.pick_from_list"), buttons=self._ask_land().buttons)]
        self._set("land_holding_band", band)
        self.state = State.FAMILY
        return [self._ask_family()]

    def _on_family_size(self, answer: str) -> list[Reply]:
        raw = answer.split(":", 1)[1] if answer.startswith("fam:") else answer
        digits = raw.strip()
        if len(digits) > 2 or not digits.isdecimal() or not (1 <= int(digits) <= 30):
            return [Reply(text=self._s("errors.pick_from_list"), buttons=self._ask_family().buttons)]
        self._set("family_size", int(digits))
        self.state = State.BANK
        return [Reply(text=self._s("questions.has_bank_account"), buttons=_yes_no(self.lang))]

    def _on_has_bank_account(self, answer: str) -> list[Reply]:
        if answer not in (YES, NO):
            return [Reply(text=self._s("errors.pick_from_list"), buttons=_yes_no(self.lang))]
        self._set("has_bank_account", answer == YES)
        self.state = State.TAX
        return [
            Reply(text=self._s("questions.is_income_tax_payer"), buttons=_yes_no(self.lang, with_dont_know=True))
        ]

    def _on_is_income_tax_payer(self, answer: str) -> list[Reply]:
        if answer in (YES, NO):
            self._set("is_income_tax_payer", answer == YES)
        elif answer == DK:
            # ! An explicit edit to Don't know must clear a previous Yes too.
            self._set("is_income_tax_payer", None)
        else:
            return [
                Reply(text=self._s("errors.pick_from_list"), buttons=_yes_no(self.lang, with_dont_know=True))
            ]
        self.state = State.TAX_CONFIRM if answer == YES else State.EPFO_ESIC
        return [self._current_question()]

    def _on_tax_confirm(self, answer: str) -> list[Reply]:
        # ! Only the worker's explicit re-answer changes a field. Keep both
        # ! continues at the next question without writing either answer again.
        if answer == "tax:keep":
            self.state = State.EPFO_ESIC
        elif answer == "tax:income":
            self.state = State.TAX_INCOME
        elif answer == "tax:answer":
            self.state = State.TAX
        return [self._current_question()]

    # ! Separate membership questions. PM-SYM's NPS scope needs classification;
    # ! e-Shram excludes only EPFO and ESIC. Asking once and applying
    # ! the answer to both made e-Shram stricter than its own source.
    def _on_is_epfo_or_esic_member(self, answer: str) -> list[Reply]:
        if answer in (YES, NO):
            self._set("is_epfo_or_esic_member", answer == YES)
        elif answer != DK:
            # * Same as the tax question: "don't know" stays unset, and any
            # * scheme that excludes members comes back UNKNOWN rather than a
            # * verdict built on an answer the worker never gave.
            return [
                Reply(text=self._s("errors.pick_from_list"), buttons=_yes_no(self.lang, with_dont_know=True))
            ]
        self.state = State.NPS
        return [self._ask_nps()]

    def _ask_nps(self) -> Reply:
        return Reply(text=self._s("questions.nps_exclusion_applies"), buttons=(
            Button(self._s("nps_choices.none"), NO),
            Button(self._s("nps_choices.central"), YES),
            Button(self._s("nps_choices.other"), OTHER),
            Button(self._s("buttons.dont_know"), DK),
        ))

    def _on_nps_exclusion_applies(self, answer: str) -> list[Reply]:
        if answer not in (YES, NO, OTHER, DK):
            return [self._ask_nps()]
        # ! Other NPS types remain unresolved across official descriptions.
        # ! Do not turn them into either a refusal or a confirmed exemption.
        self._set("nps_exclusion_applies", answer == YES if answer in (YES, NO) else None)
        # * Ask only when a loaded scheme needs this fact; a job title is not proof.
        needs_worker = any(c.field == "is_unorganised_worker"
                           for scheme in self.schemes.values() for c in scheme.criteria)
        if not needs_worker:
            return self._begin_followups()
        self.state = State.WORKER
        return [self._current_question()]

    def _on_is_unorganised_worker(self, answer: str) -> list[Reply]:
        if answer not in (YES, NO, DK):
            return [self._current_question()]
        self._set("is_unorganised_worker", None if answer == DK else answer == YES)
        return self._begin_followups()

    def _begin_followups(self) -> list[Reply]:
        # * Only new yes/no facts used by loaded schemes. State routing avoids
        # * asking Uttarakhand pension questions of residents of another state.
        supported = EXTRA_FIELDS
        self._followup_fields = []
        self._followup_index = 0
        for scheme in self.schemes.values():
            if any(c.field == "state" and c.op == "eq" and
                   self.profile.state is not None and c.value != self.profile.state
                   for c in scheme.criteria):
                continue
            for c in scheme.criteria + scheme.exclusions:
                if c.field in supported and c.field not in self._followup_fields:
                    self._followup_fields.append(c.field)
        self.state = State.FOLLOWUP if self._followup_fields else State.KNOWN_SCHEMES
        return [self._current_question()]

    def _followup_field(self) -> str:
        return self._followup_fields[self._followup_index]

    def _ask_followup(self) -> Reply:
        field = self._followup_field()
        criterion = next(c for sc in self.schemes.values() for c in sc.criteria
                         if c.field == field)
        return Reply(text=criterion.text("ask", self.lang),
                     buttons=_yes_no(self.lang, with_dont_know=True))

    def _on_followup(self, answer: str) -> list[Reply]:
        if answer not in (YES, NO, DK):
            return [self._ask_followup()]
        self._set(self._followup_field(), None if answer == DK else answer == YES)
        self._followup_index += 1
        if self._followup_index == len(self._followup_fields):
            self.state = State.KNOWN_SCHEMES
        return [self._current_question()]

    def _on_known_schemes(self, answer: str) -> list[Reply]:
        if answer.startswith("known:"):
            code = answer.split(":", 1)[1]
            if code in self.schemes:
                self._known.symmetric_difference_update({code})
            return [self._ask_known_schemes()]
        if answer == NONE:
            self._known.clear()
        elif answer != NEXT:
            return [self._ask_known_schemes()]
        self.profile = replace(self.profile, known_schemes=frozenset(self._known))
        self._event("known_schemes_declared")
        return self._evaluate()

    # * ---------------------------------------------------------- answer recap

    def _recap(self, *, header: bool = True) -> str:
        """Every answer read back, because a button press leaves no message.

        # ! Not a debug aid. A worker is about to spend a day's wages acting on
        # ! these answers and has no other way to see what was recorded — the
        # ! taps are callbacks, and nothing in the chat says which one was hit.
        """
        p = self.profile
        unset = self._s("recap.not_answered")

        def yn(value: bool | None) -> str:
            # * "Don't know" leaves the field None, and that is worth showing:
            # * it is why a scheme came back UNKNOWN rather than a verdict.
            return unset if value is None else self._s("buttons." + ("yes" if value else "no"))

        def band(section: str, code: str | None) -> str:
            return self._s(f"{section}.{code}") if code else unset

        state = next((x for x in content.states() if x.code == p.state), None)
        occ = content.occupation(p.occupation) if p.occupation else None
        held = [self.schemes[c].name(self.lang) for c in sorted(self._known) if c in self.schemes]

        pairs = [
            ("state", state.label(self.lang) if state else unset),
            ("age", str(p.age) if p.age is not None else unset),
            ("occupation", occ.label(self.lang) if occ else unset),
            ("is_unorganised_worker", yn(p.is_unorganised_worker)),
            ("income_band", band("income_bands", p.income_band)),
            ("land_holding_band", band("land_bands", p.land_holding_band)),
            ("family_size", str(p.family_size) if p.family_size is not None else unset),
            ("has_bank_account", yn(p.has_bank_account)),
            ("is_income_tax_payer", yn(p.is_income_tax_payer)),
            ("is_epfo_or_esic_member", yn(p.is_epfo_or_esic_member)),
            ("nps_exclusion_applies", self._s("nps_choices.unresolved")
             if p.nps_exclusion_applies is None else yn(p.nps_exclusion_applies)),
            ("known_schemes", ", ".join(held) if held else self._s("recap.none")),
        ]
        pairs.extend((field, yn(getattr(p, field))) for field in self._followup_fields)
        # * The sheet puts the heading on the box, so it asks for the lines only.
        lines = [self._s("recap.line", label=self._s(f"field_labels.{f}"), value=v)
                 for f, v in pairs]
        return "\n".join(([self._s("recap.header")] if header else []) + lines)

    # * -------------------------------------------------------------- results

    def _evaluate(self) -> list[Reply]:
        if not self.schemes:
            self.state = State.DONE
            return [Reply(text=self._s("errors.no_schemes_loaded"), end=True)]

        self._results = evaluate_all(self.profile, self.schemes)
        if self.log and self.session:
            self.log.log_results(
                self.session, self.profile, self._results, frozenset(self._known)
            )

        text = templates.result_message(self._results, self.schemes,
                                        frozenset(self._known), self.lang)
        # * Recap first: the worker sees what was recorded, then the verdict
        # * built on it. Its own message so a long result cannot push it away.
        replies = [Reply(text=self._recap()), Reply(text=text)]
        self._event("guidance_shown")

        self._required_docs = checklist.required_documents(self._results, self.schemes, self.lang)
        if self._required_docs:
            self.state = State.DOCUMENTS
            replies.append(self._ask_documents())
            return replies

        # * Nothing eligible, so there is no paperwork to gather — but the sheet
        # * is not empty. It carries the answers given and the question to ask
        # * for every scheme we could not decide, which is the whole of what this
        # * worker can walk in with today. Skipping the documents step and going
        # * straight to the offer keeps it to one tap.
        self.state = State.PACK
        replies.append(Reply(text=self._s("pack.offer_no_match"), buttons=_yes_no(self.lang)))
        return replies

    def _on_documents(self, answer: str) -> list[Reply]:
        if answer == "docs:more":
            self._document_page += 1
            return [self._ask_documents()]
        if answer.startswith("doc:"):
            index = answer.split(":", 1)[1]
            if not index.isdecimal() or len(index) > 3:
                return [self._ask_documents()]
            try:
                doc = self._required_docs[int(index)]
            except (ValueError, IndexError):
                return [self._ask_documents()]
            self._have_docs.symmetric_difference_update({doc})
            return [self._ask_documents()]
        if answer != NEXT:
            return [self._ask_documents()]

        missing = checklist.missing_documents(self._required_docs, frozenset(self._have_docs))
        replies = []
        if missing:
            self._event("docs_missing")
            replies.append(
                Reply(
                    text="\n".join(
                        [self._s("documents.missing_header")]
                        + [
                            self._s("documents.missing_line", doc=d, how=self._s("documents.how_generic"))
                            for d in missing
                        ]
                    )
                )
            )
        else:
            replies.append(Reply(text=self._s("documents.have_all")))
        self.state = State.PACK
        replies.append(Reply(text=self._s("pack.offer"), buttons=_yes_no(self.lang)))
        return replies

    def _on_pack(self, answer: str) -> list[Reply]:
        replies = []
        if answer == YES:
            filename, blob = pack.build(
                self._results, self.schemes, frozenset(self._known),
                frozenset(self._have_docs), lang=self.lang, recap=self._recap(header=False)
            )
            self._event("pack_generated")
            replies.append(Reply(text=self._s("pack.ready"), document=(filename, blob)))
        elif answer != NO:
            return [Reply(text=self._s("pack.offer"), buttons=_yes_no(self.lang))]

        # ! The screening is finished and logged here, not after the rating.
        # ! Someone who ignores the last two questions must still count as a
        # ! completed session - tying completion to answering an optional
        # ! question would quietly understate the thing that matters.
        if self.log and self.session:
            self.log.log(self.session, "session_complete", profile=self.profile)
        self._rating = None
        self.state = State.RATING
        replies.append(self._current_question())
        return replies

    def _on_rating(self, answer: str) -> list[Reply]:
        if answer != SKIP:
            digits = answer.strip()
            if not (digits.isdigit() and 1 <= int(digits) <= 10):
                return [Reply(text=self._s("feedback.bad_rating"),
                              buttons=(Button(self._s("feedback.skip"), SKIP),))]
            self._rating = int(digits)
        self.state = State.SUGGESTION
        return [self._current_question()]

    def _on_suggestion(self, answer: str) -> list[Reply]:
        note = "" if answer == SKIP else answer.strip()
        if self.log and (self._rating is not None or note):
            # ! Attached to nobody: the feedback table holds no session id and
            # ! no channel id, so a rating cannot be traced back to the person
            # ! who gave it. An honest 3 is worth more than a traceable 9.
            self.log.record_feedback(self._rating, note, self.channel)
        self.state = State.DONE
        replies = []
        if self._rating is not None or note:
            replies.append(Reply(text=self._s("feedback.thanks")))
        replies.append(Reply(text=self._s("closing.done"), end=True))
        return replies

    def _on_done(self, answer: str) -> list[Reply]:
        return [Reply(text=self._s("closing.done"), end=True)]


def _self_check() -> None:
    """A whole session, buttons only, no LLM key, no database."""
    from sathi.core.schemes import Criterion as C

    schemes = {
        "A": Scheme(
            code="A", name_en="A", name_hi="योजना-A", authority="x", official_url="u",
            verified_on="2026-09-01", verified_by="a",
            benefit={"annual_value_inr": 12000, "value_basis": "annual_payout",
                     "summary_hi": "हर साल पैसा"},
            criteria=(C("age", "between", [18, 40], "u", pass_hi="उम्र सही", fail_hi="उम्र बाहर"),),
            exclusions=(), documents=("आधार",), where_to_apply="csc", renewal="none",
        )
    }
    c = Conversation(schemes)
    assert c.start()[0].button_values() == {LANG_HI, LANG_EN}
    assert c.handle(LANG_HI)[0].button_values() == {consent.YES, consent.NO}

    c.handle(consent.YES)
    assert c.state is State.STATE
    c.handle("state:UK")
    c.handle("34")
    assert c.profile.age == 34 and c.profile.state == "UK"

    # ! A pasted essay must not reach the confirmation screen whole — Telegram
    # ! rejects an oversized message and the session would die on a bare 400.
    flood = Conversation(schemes)
    flood.handle(LANG_HI); flood.handle(consent.YES)
    flood.handle("state:UK"); flood.handle("34")
    replies = flood.handle("क" * 5000)
    assert len(flood._said_occupation) <= Conversation.MAX_TYPED_CHARS
    assert all(len(r.text) < 4096 for r in replies), "a reply exceeded Telegram's limit"

    c.handle("occ:construction")
    c.handle("inc:upto_5000")
    c.handle("land:landless")
    c.handle("fam:4")
    c.handle(YES)          # bank account
    c.handle(DK)           # income tax: don't know, stays unset
    c.handle(NO)           # not an EPFO/ESIC member
    c.handle(NO)           # not in NPS either — a separate question since the split
    assert c.profile.is_income_tax_payer is None
    assert c.profile.is_epfo_or_esic_member is False
    assert c.profile.nps_exclusion_applies is False
    out = c.handle(NEXT)   # knows none of them

    # ! The recap ships BEFORE the verdict. A tapped answer is a callback and
    # ! leaves nothing in the chat, so this is the worker's only chance to see
    # ! what the verdict was built on. Assert the shape, an unanswered field,
    # ! and a value that came from a button rather than from typing.
    uk = next(x for x in content.states() if x.code == "UK")
    assert s("recap.header") in out[0].text
    assert uk.label("hi") in out[0].text and "34" in out[0].text
    assert content.occupation("construction").label("hi") in out[0].text
    assert s("recap.not_answered") in out[0].text, "the skipped tax question must say so"
    assert "योजना-A" in out[1].text and c.state is State.DOCUMENTS
    c.handle("doc:0")
    out = c.handle(NEXT)
    assert s("documents.have_all") in out[0].text
    out = c.handle(YES)
    # ! The sheet arrives, then two optional questions. The screening is
    # ! already complete and logged at this point; skipping them changes
    # ! nothing except that no feedback row is written.
    assert out[0].document is not None and c.state is State.RATING
    assert not out[-1].end, "the session ended before the optional questions"
    c.handle(SKIP)
    assert c.state is State.SUGGESTION
    out = c.handle(SKIP)
    assert out[-1].end and c.state is State.DONE
    assert len(out) == 1, "a skipped rating must not be thanked"

    # * And the answered path, including a rating outside 1-10.
    c_fb = Conversation(schemes)
    c_fb.state, c_fb._rating = State.RATING, None
    assert c_fb.handle("11")[0].text == s("feedback.bad_rating")
    assert c_fb.state is State.RATING, "a bad rating must re-ask, not advance"
    c_fb.handle("9")
    assert c_fb.state is State.SUGGESTION and c_fb._rating == 9

    # * Free-text occupation with no LLM: keyword guess, then confirmation.
    c2 = Conversation(schemes)
    c2.handle(LANG_HI); c2.handle(consent.YES); c2.handle("उत्तराखंड"); c2.handle("29")
    out = c2.handle("मैं ईंट लगाता हूँ")
    assert c2.state is State.OCCUPATION_CONFIRM and c2.profile.occupation is None, \
        "a guess must not be recorded before the worker confirms it"
    c2.handle(NO)
    assert c2.profile.occupation is None and c2.state is State.OCCUPATION
    c2.handle("occ:transport")
    assert c2.profile.occupation == "transport"

    # * Declining consent stores nothing and ends.
    c3 = Conversation(schemes)
    c3.start()
    c3.handle(LANG_HI)
    out = c3.handle(consent.NO)
    assert out[0].end and c3.profile.age is None

    # * English, and a mid-conversation switch that keeps the answers.
    c4 = Conversation(schemes)
    c4.start()
    assert "Yojana Sathi" in c4.handle(LANG_EN)[0].text
    c4.handle(consent.YES); c4.handle("state:UK"); c4.handle("30")
    assert "What work do you do?" in c4._current_question().text
    out = c4.set_language("hi")
    assert c4.profile.age == 30, "switching language must not lose answers"
    assert "आप क्या काम करते हैं" in out[-1].text

    # * Commands do not disturb the conversation.
    assert "myScheme" in c4.info("about")[0].text
    assert "आधार" in c4.info("privacy")[0].text
    assert "example.gov.in" not in c4.scheme_list()[0].text
    assert c4.state is State.OCCUPATION, "an info command must not advance the flow"
    assert c4.cancel()[0].end and c4.profile.age is None, "cancel drops the profile"

    # * Age is rejected whole, never repaired. Every one of these used to be
    # * silently accepted as a DIFFERENT number, or to raise inside int().
    c5 = Conversation(schemes)
    c5.start(); c5.handle(LANG_HI); c5.handle(consent.YES); c5.handle("state:UK")
    for bad in ("9.5", "-5", "\u00b2", "3_4", "34 \u0938\u093e\u0932", "0", "200", "", "  "):
        c5.handle(bad)
        assert c5.profile.age is None, f"{bad!r} must be re-asked, not repaired into an age"
        assert c5.state is State.AGE, f"{bad!r} must not advance past the age question"
    # * Devanagari and Arabic-Indic digits are what these users actually type.
    for good, want in (("34", 34), ("\u0969\u096a", 34), ("\u0663\u0664", 34), ("  29  ", 29)):
        c6 = Conversation(schemes)
        c6.start(); c6.handle(LANG_HI); c6.handle(consent.YES); c6.handle("state:UK")
        c6.handle(good)
        assert c6.profile.age == want, f"{good!r} must be accepted as {want}"

    # * A language switch must carry document answers with it. Before this, the
    # * chat said "you have everything" while the pack listed the same documents
    # * as missing, and the worker walked to the centre without the paperwork.
    from sathi.core.schemes import load_all as _load_all
    live = _load_all()
    assert live, "shipped scheme files must load for this check to mean anything"
    sample = next(iter(live.values()))
    en_doc, hi_doc = sample.docs("en")[0], sample.docs("hi")[0]
    assert en_doc != hi_doc, "pick a scheme whose translation actually differs"

    c7 = Conversation(live)
    c7.lang = "en"
    c7._results = ()
    c7._required_docs = (en_doc,)
    c7._have_docs = {en_doc}
    c7.lang = "hi"
    c7._relabel_documents("en")
    assert hi_doc in c7._have_docs, \
        "a document ticked in English must stay ticked after switching to Hindi"
    assert en_doc not in c7._have_docs, \
        "the stale English label must not linger — the pack compares Hindi names"

    # * And back again, so neither direction is the special case.
    c7.lang = "en"
    c7._relabel_documents("hi")
    assert c7._have_docs == {en_doc}, c7._have_docs

    print("flow.py OK")


if __name__ == "__main__":
    _self_check()
