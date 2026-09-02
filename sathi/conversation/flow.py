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
    EPFO_ESIC = "is_epfo_or_esic_member"
    NPS = "is_nps_member"
    KNOWN_SCHEMES = "known_schemes"
    DOCUMENTS = "documents"
    PACK = "pack"
    DONE = "done"


YES, NO, DK = "yes", "no", "dont_know"
NEXT, OTHER, NONE = "next", "other", "none"
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
        self.session = log.start_session(channel) if log else None
        self.profile = Profile()
        self.lang = content.DEFAULT_LANG
        self.state = State.LANGUAGE
        self._pending_occupation: str | None = None  # LLM/keyword guess, unconfirmed
        self._said_occupation = ""
        self._known: set[str] = set()
        self._have_docs: set[str] = set()
        self._required_docs: tuple[str, ...] = ()
        self._results: tuple = ()

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
        self.lang = content.normalise_lang(lang)
        return [Reply(text=self._s("language.changed")), self._current_question()]

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
            State.LAND: self._ask_land,
            State.FAMILY: self._ask_family,
            State.BANK: lambda: Reply(text=self._s("questions.has_bank_account"),
                                      buttons=_yes_no(self.lang)),
            State.TAX: lambda: Reply(text=self._s("questions.is_income_tax_payer"),
                                     buttons=_yes_no(self.lang, with_dont_know=True)),
            State.EPFO_ESIC: lambda: Reply(
                text=self._s("questions.is_epfo_or_esic_member"),
                buttons=_yes_no(self.lang, with_dont_know=True)),
            State.NPS: lambda: Reply(
                text=self._s("questions.is_nps_member"),
                buttons=_yes_no(self.lang, with_dont_know=True)),
            State.KNOWN_SCHEMES: self._ask_known_schemes,
            State.DOCUMENTS: self._ask_documents,
            State.PACK: lambda: Reply(text=self._s("pack.offer"), buttons=_yes_no(self.lang)),
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
        return [Reply(text=self._s(f"commands.{topic}"))]

    def scheme_list(self) -> list[Reply]:
        """/schemes — every scheme, its official source, and when it was checked.

        # ! Provenance handed to the worker, not just to a judge. Someone who can
        # ! open the source URL can check us; someone who cannot at least sees
        # ! that a source exists and is dated.
        """
        lines = [self._s("commands.schemes_header")]
        for code, sc in self.schemes.items():
            lines.append(self._s("commands.schemes_line", name=sc.name(self.lang),
                                 code=code, url=sc.official_url,
                                 verified_on=sc.verified_on))
            # ! Covers both unfinished states — a leftover TODO and a file
            # ! nobody has signed off. Gating this on `sc.stubs` alone showed a
            # ! clean provenance line for schemes served as UNKNOWN.
            if not sc.is_servable:
                lines.append(self._s("commands.schemes_unverified"))
        return [Reply(text="\n".join(lines))]

    def cancel(self) -> list[Reply]:
        """/cancel — drop the profile now, not at the end of the session."""
        self.profile = Profile()
        self._known.clear()
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
        buttons = tuple(
            Button(("✅ " if d in self._have_docs else "") + d, f"doc:{i}")
            for i, d in enumerate(self._required_docs)
        ) + (Button(self._s("buttons.next"), NEXT),)
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
        if not code:
            # * No guessing at a half-recognised state. Re-ask with the buttons.
            retry = self._ask_state()
            return [Reply(text=self._s("questions.state_retry"), buttons=retry.buttons)]
        self._set("state", code)
        self.state = State.AGE
        return [Reply(text=self._s("questions.age"))]

    def _on_age(self, answer: str) -> list[Reply]:
        digits = "".join(ch for ch in answer if ch.isdigit())
        if not digits or not (1 <= int(digits) <= 120):
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
        self.state = State.LAND
        return [self._ask_land()]

    def _on_land_holding_band(self, answer: str) -> list[Reply]:
        band = answer.split(":", 1)[1] if answer.startswith("land:") else answer
        if band not in LAND_HOLDING_BANDS:
            return [Reply(text=self._s("errors.pick_from_list"), buttons=self._ask_land().buttons)]
        self._set("land_holding_band", band)
        self.state = State.FAMILY
        return [self._ask_family()]

    def _on_family_size(self, answer: str) -> list[Reply]:
        raw = answer.split(":", 1)[1] if answer.startswith("fam:") else answer
        digits = "".join(ch for ch in raw if ch.isdigit())
        if not digits or not (1 <= int(digits) <= 30):
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
            # * Left unset on purpose → any scheme excluding tax payers comes
            # * back UNKNOWN, with "ask this at the centre" attached.
            pass
        else:
            return [
                Reply(text=self._s("errors.pick_from_list"), buttons=_yes_no(self.lang, with_dont_know=True))
            ]
        self.state = State.EPFO_ESIC
        return [
            Reply(text=self._s("questions.is_epfo_or_esic_member"),
                  buttons=_yes_no(self.lang, with_dont_know=True))
        ]

    # ! Two questions where there used to be one. PM-SYM excludes EPFO, ESIC and
    # ! NPS alike; e-Shram excludes only EPFO and ESIC. Asking once and applying
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
        return [
            Reply(text=self._s("questions.is_nps_member"),
                  buttons=_yes_no(self.lang, with_dont_know=True))
        ]

    def _on_is_nps_member(self, answer: str) -> list[Reply]:
        if answer in (YES, NO):
            self._set("is_nps_member", answer == YES)
        elif answer != DK:
            return [
                Reply(text=self._s("errors.pick_from_list"), buttons=_yes_no(self.lang, with_dont_know=True))
            ]
        self.state = State.KNOWN_SCHEMES
        return [self._ask_known_schemes()]

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
        replies = [Reply(text=text)]
        self._event("guidance_shown")

        self._required_docs = checklist.required_documents(self._results, self.schemes, self.lang)
        if self._required_docs:
            self.state = State.DOCUMENTS
            replies.append(self._ask_documents())
            return replies

        # * Nothing eligible → no paperwork to carry. End honestly, not with an
        # * offer of a pack that would list nothing.
        self.state = State.DONE
        replies.append(Reply(text=self._s("closing.done"), end=True))
        if self.log and self.session:
            self.log.log(self.session, "session_complete", profile=self.profile)
        return replies

    def _on_documents(self, answer: str) -> list[Reply]:
        if answer.startswith("doc:"):
            try:
                doc = self._required_docs[int(answer.split(":", 1)[1])]
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
                frozenset(self._have_docs), lang=self.lang
            )
            self._event("pack_generated")
            replies.append(Reply(text=self._s("pack.ready"), document=(filename, blob)))
        elif answer != NO:
            return [Reply(text=self._s("pack.offer"), buttons=_yes_no(self.lang))]

        self.state = State.DONE
        replies.append(Reply(text=self._s("closing.done"), end=True))
        if self.log and self.session:
            self.log.log(self.session, "session_complete", profile=self.profile)
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
    assert c.profile.is_nps_member is False
    out = c.handle(NEXT)   # knows none of them
    assert "योजना-A" in out[0].text and c.state is State.DOCUMENTS
    c.handle("doc:0")
    out = c.handle(NEXT)
    assert s("documents.have_all") in out[0].text
    out = c.handle(YES)
    assert out[0].document is not None and out[-1].end
    assert c.state is State.DONE

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
    print("flow.py OK")


if __name__ == "__main__":
    _self_check()
