"""Exhaustive walk of the conversation. Run: python3 tests/test_all_paths.py

# ! Every other test drives one path a human thought of. This one presses EVERY
# ! button at every reachable state, in both languages, and checks the same
# ! invariants at each node. It exists because the first day of real use found
# ! six faults the hand-written tests walked straight past — all of them in
# ! screens nobody had clicked.
#
# * Paths are replayed from scratch rather than cloned, so the walk needs no
# * deep-copy of the Conversation and cannot leak state between branches. The
# * visited set is keyed on what actually changes the screen, which keeps the
# * multi-select states (known schemes, documents) from exploding.
"""

import sys
import tempfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.channels import whatsapp
from sathi.channels.telegram import keyboard
from sathi.conversation.flow import LANG_EN, LANG_HI, Conversation, State
from sathi.core.schemes import load_all
from sathi.metrics.events import EventLog

# ! Deepest complete session, plus headroom. Splitting the statutory-membership
# ! question in two on 2026-09-03 added a step and tripped this at exactly 20.
MAX_DEPTH = 40
DEVANAGARI = ("ऀ", "ॿ")

# * States that legitimately show no buttons: they want typed input.
TYPED_STATES = {State.AGE, State.OCCUPATION_FREE}


# * The one Devanagari word allowed in an English session: the NAME of the other
# * language. "/language — Switch हिंदी / English" is correct exactly as it is —
# * a Hindi reader has to be able to recognise the option they want.
ALLOWED_IN_ENGLISH = ("हिंदी",)


def _has_devanagari(text: str) -> bool:
    for allowed in ALLOWED_IN_ENGLISH:
        text = text.replace(allowed, "")
    return any(DEVANAGARI[0] <= ch <= DEVANAGARI[1] for ch in text)


def _schemes(directory: Path):
    # ! The real scheme files, not fixtures. A walk over invented data would not
    # ! catch a long scheme name breaking a button or a missing English string.
    #
    # ! Signed for the walk, though. The engine refuses a verdict for any scheme
    # ! whose `verified_by` still says PENDING HUMAN VERIFICATION, which is
    # ! correct in production and useless here: every worker would come out
    # ! UNKNOWN and the whole eligible-result half of the conversation — the
    # ! result screen, the document checklist, the application pack — would stop
    # ! being reachable, so this walk would silently stop covering it.
    # !
    # ! And stubs are cleared for the same reason. A file with a documented
    # ! "TODO" (UK_WIDOW's benefit amount, whose source went 404) is unservable
    # ! too, so its documents would silently vanish from the checklist and the
    # ! walk would quietly shrink — it went from 2,109 paths to 669, and 216
    # ! document screens to 63, the first time this was missed.
    # !
    # ! Only the signature and the stub flag are faked. Every threshold, name,
    # ! string and document list is the shipped one. tests/test_schemes.py
    # ! asserts separately that the shipped files are still honestly marked as
    # ! unsigned, and that every remaining stub is a recorded one.
    real = load_all(ROOT / "data" / "schemes")
    return {
        code: replace(sc, verified_by="test-signature (tests/test_all_paths.py)",
                      stubs=())
        for code, sc in real.items()
    }


# ! Counters, because a test that never reached the thing it checks is the trap
# ! this whole file exists to close. The walk asserts these are non-zero.
CHECKED = {"replies": 0, "buttons": 0, "packs": 0, "wa_rows": 0, "wa_buttons": 0}


def _check_reply(reply, path, lang, problems, echoed=()):
    CHECKED["replies"] += 1
    CHECKED["buttons"] += len(reply.buttons)
    where = f"[{lang}] after {path}"
    text = reply.text
    # * The confirmation screen quotes the worker back to themselves. Someone can
    # * type Hindi in an English session and the echo must survive verbatim, so
    # * their own words are removed before the language check.
    for said in echoed:
        text = text.replace(said, "")

    if not reply.text.strip():
        problems.append(f"{where}: empty message")
    if "{" in text or "}" in text:
        problems.append(f"{where}: unfilled placeholder in {reply.text[:60]!r}")

    seen = set()
    for b in reply.buttons:
        if not b.label.strip():
            problems.append(f"{where}: button with no label")
        if len(b.value.encode()) > 64:
            problems.append(f"{where}: callback_data over 64 bytes: {b.value!r}")
        if b.value in seen:
            problems.append(f"{where}: duplicate button value {b.value!r}")
        seen.add(b.value)
        if lang == "en" and _has_devanagari(b.label):
            problems.append(f"{where}: Hindi button {b.label!r} in an English session")

    # ! The one screen that is bilingual on purpose is the language picker.
    if lang == "en" and path and _has_devanagari(text):
        problems.append(f"{where}: Hindi text in an English session: {reply.text[:60]!r}")

    # ! The generated pack is a reply like any other and gets the same checks.
    # ! It is the one artefact that outlives the chat, and it shipped twice with
    # ! faults nobody saw because no test opened it.
    if reply.document is not None:
        CHECKED["packs"] += 1
        name, blob = reply.document
        page = blob.decode("utf-8")
        if not name.endswith(".html") or len(blob) < 500:
            problems.append(f"{where}: implausible pack {name!r} ({len(blob)} bytes)")
        body = page.split("<body>", 1)[-1]
        for said in echoed:
            body = body.replace(said, "")
        if "{" in body.replace("{{", "") and "}" in body:
            problems.append(f"{where}: unfilled placeholder in the pack")
        if lang == "en" and _has_devanagari(body):
            leak = "".join(c for c in body if DEVANAGARI[0] <= c <= DEVANAGARI[1])[:40]
            problems.append(f"{where}: Hindi on an English pack: {leak!r}")
        if "<script" in page.lower():
            problems.append(f"{where}: the pack must be a document, not an app")

    # * What the channel would actually put on the wire.
    payload = {"chat_id": "1", "text": reply.text}
    markup = keyboard(reply.buttons)
    if markup is not None:
        payload["reply_markup"] = markup
    if None in payload.values():
        problems.append(f"{where}: null in the outgoing payload")

    # ! And what the OTHER channel would put on the wire. WhatsApp's limits are
    # ! far tighter than Telegram's — three buttons, ten list rows, a 24
    # ! character row title — so a screen that outgrows them has to fail here
    # ! rather than as a 400 in front of a worker.
    try:
        rendered = whatsapp.interactive(reply.text, reply.buttons, lang)
    except whatsapp.WhatsAppError as e:
        problems.append(f"{where}: WhatsApp cannot render this screen: {e}")
    else:
        action = rendered["interactive"]["action"] if reply.buttons else {}
        for row in (action.get("sections") or [{}])[0].get("rows", []):
            CHECKED["wa_rows"] += 1
            if len(row["title"]) > whatsapp._ROW_TITLE:
                problems.append(f"{where}: list row title too long: {row['title']!r}")
            if len(row.get("description", "")) > whatsapp._ROW_DESC:
                problems.append(f"{where}: list row description too long: {row}")
            if not row["id"]:
                problems.append(f"{where}: list row with no id: {row}")
        for button in action.get("buttons", []):
            CHECKED["wa_buttons"] += 1
            title = button["reply"]["title"]
            if len(title) > whatsapp._BUTTON_TITLE:
                problems.append(f"{where}: reply button title too long: {title!r}")


def test_every_button_in_both_languages():
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        # ! Every path also writes to a real event log. The consent gate raises
        # ! rather than returning, so any path that emits an event too early
        # ! crashes here instead of shipping.
        log = EventLog(Path(d) / "paths.db")

        for lang in (LANG_HI, LANG_EN):
            code = lang.split(":")[1]
            frontier = [[lang]]  # * BFS: first visit to a screen is its shortest path
            visited = set()
            ended = 0
            explored = 0

            while frontier:
                path = frontier.pop(0)
                if len(path) > MAX_DEPTH:
                    problems.append(f"[{code}] path longer than {MAX_DEPTH}: {path}")
                    continue

                convo = Conversation(schemes, log, channel="cli")
                replies = convo.start()
                for step in path:
                    replies = convo.handle(step)
                explored += 1

                typed = [step for step in path if not step.startswith(
                    ("lang:", "state:", "occ:", "inc:", "land:", "fam:", "doc:", "known:"))]
                for r in replies:
                    _check_reply(r, path[1:], code, problems, echoed=typed)

                if any(r.end for r in replies):
                    ended += 1
                    continue

                last = replies[-1]
                if not last.buttons and convo.state not in TYPED_STATES:
                    problems.append(
                        f"[{code}] dead end at {convo.state.value} after {path[1:]}: "
                        f"no buttons and no typed answer expected"
                    )

                # * Key on what changes the screen. Without this the two
                # * multi-select states alone would fan out to thousands of paths.
                key = (
                    convo.state,
                    convo._followup_field() if convo.state is State.FOLLOWUP else None,
                    convo._document_page,
                    # * Cover empty, each singleton and multiple selections.
                    # * Seven schemes and paged documents would otherwise
                    # * enumerate millions of equivalent checkbox subsets.
                    tuple(sorted(convo._known)) if len(convo._known) <= 1 else ("multiple",),
                    tuple(sorted(convo._have_docs)) if len(convo._have_docs) <= 1 else ("multiple",),
                )
                if key in visited:
                    continue
                visited.add(key)

                for b in last.buttons:
                    frontier.append(path + [b.value])
                if convo.state in TYPED_STATES:
                    frontier.append(path + ["30" if convo.state is State.AGE else "ईंट का काम"])

            assert ended, f"[{code}] no path ever reached the end of a session"
            assert {State.TAX_CONFIRM, State.TAX_INCOME} <= {key[0] for key in visited}, \
                "the exhaustive button walk missed the tax confirmation or income edit"
            print(f"  .. {code}: {explored} paths walked, {ended} completed sessions")
            # ! A floor, not an exact number. It caught a stub silently making
            # ! a scheme unservable and cutting the walk from 2,109 paths to
            # ! 669. It is deliberately loose, because the count also moves for
            # ! an honest reason: this BFS keys on the screen, so all answers to
            # ! a follow-up question collapse to one key, and whichever branch
            # ! reaches the document screen first decides how many documents
            # ! exist there. Adding the "already receiving another pension"
            # ! question moved that branch to one where both pensions are
            # ! INELIGIBLE, so their documents are legitimately absent.
            # !
            # ! That is why the real guarantee — a fully eligible worker still
            # ! gets every scheme's documents — is asserted directly in
            # ! test_every_document_of_every_scheme_is_reachable() below, not
            # ! inferred from this number.
            assert explored >= 600, (
                f"[{code}] the walk shrank to {explored} paths — a scheme file "
                f"probably became unservable in the fixture; see _schemes()"
            )

        # ! Whatever those hundreds of sessions wrote, it must still be coarse.
        from sathi.core.profile import INCOME_BANDS
        from sathi.metrics.events import COARSE_FIELDS

        rows = log.query("SELECT * FROM events")
        assert rows, "the walk wrote no events at all"
        for row in rows:
            if row["income_band"] is not None and row["income_band"] not in INCOME_BANDS:
                problems.append(f"event log holds a non-band income {row['income_band']!r}")
            if row["age_band"] is not None and row["age_band"].isdigit():
                problems.append(f"event log holds an exact age {row['age_band']!r}")
        assert set(COARSE_FIELDS) <= set(rows[0].keys())
        log.close()

    assert CHECKED["packs"] >= 2, f"no pack was ever generated or checked: {CHECKED}"
    assert CHECKED["buttons"] > 500, f"too few buttons exercised: {CHECKED}"
    # ! Both WhatsApp shapes have to be exercised, or the caps above are checked
    # ! on paper only: three options ride on reply buttons, more become a list.
    assert CHECKED["wa_rows"] > 100 and CHECKED["wa_buttons"] > 100, \
        f"a WhatsApp render path was never walked: {CHECKED}"
    print(f"  .. checked {CHECKED['replies']} replies, {CHECKED['buttons']} buttons, "
          f"{CHECKED['packs']} packs, {len(rows)} events, "
          f"{CHECKED['wa_buttons']}+{CHECKED['wa_rows']} WhatsApp buttons/rows")

    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def test_every_document_of_every_scheme_is_reachable():
    """Between them, two eligible workers are shown every scheme's documents.

    # ! The button walk cannot promise this. It keys on the screen, so only ONE
    # ! set of follow-up answers is ever carried through to the document page,
    # ! and which set that is depends on the search order — adding a follow-up
    # ! question silently changed it once already.

    # ! Two workers, because no single one can qualify for all seven: PM-SYM
    # ! stops taking entries at 40, PMJJBY at 50, and the old-age pension does
    # ! not start until 60. That is a fact about the schemes, not a gap here.
    """
    keep = {"is_woman": "yes", "is_widow": "yes", "household_has_lpg": "no",
            "pmuy_declaration_met": "yes", "uk_pension_income_or_bpl": "yes",
            "receives_other_pension": "no", "uk_pension_selected": "yes"}

    def run(schemes, lang: str, age: str):
        convo = Conversation(schemes, None)
        convo.start()
        for step in (LANG_EN if lang == "en" else LANG_HI, "consent_yes",
                     "state:UK", age, "occ:construction", "inc:upto_5000",
                     "land:landless", "fam:4", "yes", "no", "no", "no", "yes"):
            convo.handle(step)
        while convo.state is State.FOLLOWUP:
            field = convo._followup_field()
            assert field in keep, f"new follow-up {field} — decide its eligible answer"
            convo.handle(keep[field])
        assert convo.state is State.KNOWN_SCHEMES, convo.state
        convo.handle("next")
        assert convo.state is State.DOCUMENTS, convo.state
        eligible = {r.scheme_code for r in convo._results if r.is_eligible}
        offered: set[str] = set()
        for _ in range(10):
            reply = convo._ask_documents()
            assert len(reply.buttons) <= 10, "WhatsApp allows ten rows"
            offered |= {b.label for b in reply.buttons if b.value.startswith("doc:")}
            if not any(b.value == "docs:more" for b in reply.buttons):
                break
            convo.handle("docs:more")
        return eligible, offered

    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        for lang in ("hi", "en"):
            # ! Three ages, because no single worker qualifies for everything
            # ! and the age bands do not overlap: entry schemes cap at 40, the
            # ! state pensions start at 60, and PM-JAY's income-blind cover
            # ! starts at 70. A scheme nobody in this list can reach is a
            # ! scheme whose documents were never offered to anyone, which is
            # ! precisely what this test exists to catch - it caught PMJAY_70
            # ! on the day it was added.
            young_codes, young_docs = run(schemes, lang, "30")
            old_codes, old_docs = run(schemes, lang, "65")
            eldest_codes, eldest_docs = run(schemes, lang, "72")
            reached = young_codes | old_codes | eldest_codes
            assert reached == set(schemes), (
                f"[{lang}] no eligible path to {sorted(set(schemes) - reached)}"
            )
            expected = {doc for sc in schemes.values() for doc in sc.docs(lang)}
            missing = expected - (young_docs | old_docs | eldest_docs)
            assert not missing, f"[{lang}] documents never offered: {sorted(missing)}"


def test_commands_at_every_state():
    """/help and friends must answer anywhere without derailing the conversation."""
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        # ! The walk used to end "no, next" and stall at NPS, so KNOWN_SCHEMES,
        # ! DOCUMENTS, PACK and DONE were never reached by a test that claims to
        # ! cover every state. NPS needs its own answer before "next" means
        # ! anything.
        walk = [LANG_EN, "consent_yes", "state:UK", "30", "occ:construction",
                "inc:upto_5000", "land:landless", "fam:4", "yes", "no", "no", "no", "yes",
                # ! The seven follow-ups, in the order they are asked:
                # ! is_woman, household_has_lpg, pmuy_declaration_met,
                # ! uk_pension_income_or_bpl, receives_other_pension,
                # ! uk_pension_selected, is_widow. The fifth must be "no" —
                # ! answering that a pension is already being drawn makes both
                # ! state pensions INELIGIBLE, and this walk needs the eligible
                # ! half of the conversation to stay reachable.
                "yes", "no", "yes", "yes", "no", "yes", "yes",
                # ! The sheet, then the two optional questions after it. Both
                # ! skipped here: the point of this walk is that a command works
                # ! at every state, not that anyone rates the bot.
                "next", "next", "yes", "skip", "skip"]
        reached = set()

        for stop in range(len(walk) + 1):
            for command in ("help", "about", "privacy"):
                convo = Conversation(schemes, None)
                convo.start()
                for step in walk[:stop]:
                    convo.handle(step)
                before = (convo.state, convo.profile)
                for reply in convo.info(command):
                    _check_reply(reply, walk[:stop], "en", problems)
                if (convo.state, convo.profile) != before:
                    problems.append(f"/{command} at {before[0].value} changed the conversation")

            convo = Conversation(schemes, None)
            convo.start()
            for step in walk[:stop]:
                convo.handle(step)
            state_before = convo.state
            reached.add(state_before)
            for reply in convo.scheme_list():
                _check_reply(reply, walk[:stop], "en", problems)
            if convo.state is not state_before:
                problems.append(f"/schemes at {state_before.value} changed the state")

            # ! /language must keep every answer already given.
            convo2 = Conversation(schemes, None)
            convo2.start()
            for step in walk[:stop]:
                convo2.handle(step)
            profile_before = convo2.profile
            convo2.set_language("hi")
            if convo2.profile != profile_before:
                problems.append(f"/language at {state_before.value} lost an answer")

        assert reached == set(State) - {
            State.OCCUPATION_FREE, State.OCCUPATION_CONFIRM, State.TAX_CONFIRM, State.TAX_INCOME,
        }, "the tax-No command walk must reach DONE without entering confirmation"
    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def test_every_command_through_the_adapter_at_every_state():
    """The commands as a WORKER sends them — slash words through the adapter.

    # ! The flow-level test calls convo.info() directly, which skips the routing
    # ! table, the callback plumbing and the send payloads. This drives the real
    # ! entry point with the network stubbed, so a command that crashes the
    # ! adapter shows up here rather than in someone's chat.
    """
    import sathi.channels.telegram as mod
    from sathi.channels.router import COMMANDS
    from sathi.channels.telegram import TelegramBot

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        walk = ["lang:en", "consent_yes", "state:UK", "30", "occ:construction",
                "inc:upto_5000", "land:landless", "fam:4", "yes", "no", "no", "no", "yes",
                # ! Same seven follow-ups as the walk above, same reason for the
                # ! "no" in fifth place: receives_other_pension.
                "yes", "no", "yes", "yes", "no", "yes", "yes",
                "next", "next", "yes", "skip", "skip"]
        reached = set()

        sent: list[tuple[str, dict]] = []
        # ! The adapter accepts a tap only from the keyboard it last delivered,
        # ! so a fabricated message_id is now rejected as stale. Record what the
        # ! wire actually returned and tap THAT. Fabricated ids left this whole
        # ! walk rejected — every command below was being exercised against the
        # ! opening screen while the suite still reported green.
        live_keyboard: dict[str, int] = {}
        real_call, real_upload = mod._call, mod._upload

        def _wire(token, method, payload):
            sent.append((method, payload))
            mid = len(sent)
            if method == "sendMessage":
                # * Mirror the adapter: any reply replaces the live keyboard, and
                # * a reply without buttons leaves none — which is how we know the
                # * next answer has to be typed rather than tapped.
                live_keyboard.pop(str(payload["chat_id"]), None)
                if payload.get("reply_markup"):
                    live_keyboard[str(payload["chat_id"])] = mid
            return {"ok": True, "result": {"message_id": mid}}

        mod._call = _wire
        mod._upload = lambda *a, **k: sent.append(("sendDocument", {"file": a[2]})) or {"ok": True}
        try:
            for stop in range(len(walk) + 1):
                for word in sorted(COMMANDS):
                    bot = TelegramBot(schemes, token="test-token")
                    chat = "77"
                    live_keyboard.pop(chat, None)
                    # * A real worker arrives via /start; that is what puts the
                    # * first keyboard on screen. The walk used to skip it and
                    # * invent ids instead.
                    path_start = len(sent)
                    bot.handle_update({"message": {
                        "chat": {"id": int(chat)}, "message_id": 1, "text": "/start"}})
                    for i, step in enumerate(walk[:stop]):
                        mid = live_keyboard.get(chat)
                        if mid is None:
                            # * No buttons on screen — the age question. A worker
                            # * types here, so the walk must type here too.
                            bot.handle_update({"message": {
                                "chat": {"id": int(chat)},
                                "message_id": 400 + i, "text": step}})
                            continue
                        bot.handle_update({"callback_query": {
                            "id": str(i), "data": step,
                            "message": {"chat": {"id": int(chat)}, "message_id": mid}}})
                    assert not any(m == "answerCallbackQuery" and p.get("text")
                                   for m, p in sent[path_start:]), "a walk tap was rejected as stale"
                    if stop == len(walk):
                        assert chat not in bot.sessions
                        assert sent[-1][0] == "sendMessage"
                        assert sent[-1][1]["text"] == mod.s("closing.done", "en")
                        reached.add(State.DONE)
                    else:
                        assert chat in bot.sessions, "walk lost its session before DONE"
                        reached.add(bot.sessions[chat].state)
                    before = len(sent)
                    try:
                        bot.handle_update({"message": {
                            "chat": {"id": int(chat)}, "message_id": 500, "text": word}})
                    except Exception as e:  # noqa: BLE001 — the point is that it must not
                        problems.append(f"{word} at step {stop} raised {type(e).__name__}: {e}")
                        continue
                    replies = sent[before:]
                    if not any(m == "sendMessage" for m, _ in replies):
                        problems.append(f"{word} at step {stop} answered nothing")
                    for method, payload in replies:
                        if method == "sendMessage":
                            if not payload.get("text", "").strip():
                                problems.append(f"{word} at step {stop} sent an empty message")
                            if "{" in payload.get("text", ""):
                                problems.append(f"{word} at step {stop} sent a placeholder")
                        if None in payload.values():
                            problems.append(f"{word} at step {stop}: null in payload")
        finally:
            mod._call, mod._upload = real_call, real_upload

        assert reached == set(State) - {
            State.OCCUPATION_FREE, State.OCCUPATION_CONFIRM, State.TAX_CONFIRM, State.TAX_INCOME,
        }, "the adapter's tax-No walk must reach DONE without entering confirmation"
    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def test_junk_input_at_every_typed_question():
    """Nonsense must re-ask, never crash and never be recorded as an answer."""
    junk = ["", "   ", "?????", "-5", "0", "999", "12.5", "٣٤", "🙂🙂🙂",
            "<script>alert(1)</script>", "'; DROP TABLE events; --", "x" * 500]
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        for bad in junk:
            convo = Conversation(schemes, None)
            convo.start()
            convo.handle(LANG_EN)
            convo.handle("consent_yes")

            for reply in convo.handle(bad):           # state question
                _check_reply(reply, [f"state={bad!r}"], "en", problems)
            if convo.profile.state is not None and convo.state is not State.AGE:
                problems.append(f"junk state {bad!r} was recorded as {convo.profile.state!r}")

            convo.handle("state:UK")
            for reply in convo.handle(bad):           # age question
                _check_reply(reply, [f"age={bad!r}"], "en", problems)
            age = convo.profile.age
            if age is not None and not (1 <= age <= 120):
                problems.append(f"junk age {bad!r} was recorded as {age!r}")

            if convo.state is State.OCCUPATION:
                # * Age was accepted (e.g. "999" is digits) — it must still be sane.
                if not (1 <= (convo.profile.age or 0) <= 120):
                    problems.append(f"age {bad!r} accepted out of range")

    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def run() -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"  ok  {name}")
    print("test_all_paths.py OK")


if __name__ == "__main__":
    run()
