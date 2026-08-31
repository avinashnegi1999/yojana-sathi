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
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.channels.telegram import keyboard
from sathi.conversation.flow import LANG_EN, LANG_HI, Conversation, State
from sathi.core.schemes import load_all
from sathi.metrics.events import EventLog

MAX_DEPTH = 20
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
    return load_all(ROOT / "data" / "schemes")


# ! Counters, because a test that never reached the thing it checks is the trap
# ! this whole file exists to close. The walk asserts these are non-zero.
CHECKED = {"replies": 0, "buttons": 0, "packs": 0}


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
                    tuple(sorted(convo._known)),
                    tuple(sorted(convo._have_docs)),
                )
                if key in visited:
                    continue
                visited.add(key)

                for b in last.buttons:
                    frontier.append(path + [b.value])
                if convo.state in TYPED_STATES:
                    frontier.append(path + ["30" if convo.state is State.AGE else "ईंट का काम"])

            assert ended, f"[{code}] no path ever reached the end of a session"
            print(f"  .. {code}: {explored} paths walked, {ended} completed sessions")

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
    print(f"  .. checked {CHECKED['replies']} replies, {CHECKED['buttons']} buttons, "
          f"{CHECKED['packs']} packs, {len(rows)} events")

    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def test_commands_at_every_state():
    """/help and friends must answer anywhere without derailing the conversation."""
    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        walk = [LANG_EN, "consent_yes", "state:UK", "30", "occ:construction",
                "inc:upto_5000", "land:landless", "fam:4", "yes", "no", "no", "next"]

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

    assert not problems, "\n".join(f"  - {p}" for p in sorted(set(problems))[:25])


def test_every_command_through_the_adapter_at_every_state():
    """The commands as a WORKER sends them — slash words through the adapter.

    # ! The flow-level test calls convo.info() directly, which skips the routing
    # ! table, the callback plumbing and the send payloads. This drives the real
    # ! entry point with the network stubbed, so a command that crashes the
    # ! adapter shows up here rather than in someone's chat.
    """
    import sathi.channels.telegram as mod
    from sathi.channels.telegram import COMMANDS, TelegramBot

    problems: list[str] = []
    with tempfile.TemporaryDirectory() as d:
        schemes = _schemes(Path(d))
        walk = ["lang:en", "consent_yes", "state:UK", "30", "occ:construction",
                "inc:upto_5000", "land:landless", "fam:4", "yes", "no", "no", "next"]

        sent: list[tuple[str, dict]] = []
        real_call, real_upload = mod._call, mod._upload
        mod._call = lambda token, method, payload: (
            sent.append((method, payload)) or {"ok": True, "result": {"message_id": len(sent)}}
        )
        mod._upload = lambda *a, **k: sent.append(("sendDocument", {"file": a[2]})) or {"ok": True}
        try:
            for stop in range(len(walk) + 1):
                for word in sorted(COMMANDS):
                    bot = TelegramBot(schemes, token="test-token")
                    chat = "77"
                    for i, step in enumerate(walk[:stop]):
                        bot.handle_update({"callback_query": {
                            "id": str(i), "data": step,
                            "message": {"chat": {"id": int(chat)}, "message_id": i + 1}}})
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
