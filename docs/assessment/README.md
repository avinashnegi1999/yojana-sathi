> **HISTORICAL SNAPSHOT — superseded.** This describes the project as it stood
> in early September 2026: three schemes, no WhatsApp adapter, and no human
> sign-off on any scheme file. All of that has changed. It is kept because an
> audit trail showing what was wrong and when is worth more than a tidy
> repository, but do not read it as current state.
>
> For current state: [`README.md`](../../README.md) at the repository root, and
> [`ARCHITECTURE.md`](../ARCHITECTURE.md).

# Assessment

A scored breakdown of where this project actually stands, with the evidence for
each number. The point of writing it down is the two low scores, not the high
ones — a scorecard that flatters everything says nothing.

| Dimension | Score |
|---|---|
| Idea / problem | 9 / 10 |
| Architecture | 9 / 10 |
| Testing | 9.5 / 10 |
| Safety / correctness | 9.5 / 10 |
| Documentation | 9 / 10 |
| Code / engineering | 9 / 10 |
| **Current product maturity** | **7 / 10** |
| Portfolio / interview value | 9 / 10 |

---

## Idea / problem — 9

The user is an unorganised worker deciding whether to spend a day walking to a
government centre. A male casual labourer earns ₹455 a day, a female ₹315. That
is the cost of a wrong answer, and it is a cited figure rather than a rhetorical
one. The project is positioned as last-mile delivery on top of `myScheme.gov.in`
— which assumes literacy and a browser — not as a replacement for it.

Not a 10 because the problem is real but the demand is unproven. Nobody outside
the build has used this yet.

## Architecture — 9

`sathi/rules/` decides eligibility and may not import an LLM. Compute the
verdict, then narrate it: the model handles conversation flow, maps free text to
a category — always confirmed back to the worker before it is recorded — and
rephrases Hindi a human wrote. It never sees a threshold, never produces a ₹
figure, never produces a verdict.

The channel layer is separable, so Telegram now and WhatsApp later cannot let
Meta verification block a deploy date. `LLM_API_KEY` unset is a *tested*
configuration, not a degraded one.

Not a 10 because the WhatsApp adapter is designed for but unbuilt, so the
claim that the core is channel-agnostic is argued rather than demonstrated.

## Testing — 9.5

4,140 lines of production Python against 1,716 lines of tests: 15 module
self-checks plus 6 test files, run by one command with no framework to install.
`tests/test_all_paths.py` walks 486 button-by-button paths per language and
asserts its own coverage counters.

The 0.5 is deducted for a specific reason. Twice this suite has been green while
blind: an acceptance test compared answer recaps instead of verdicts and passed
with a deliberately corrupted result, and the all-paths walk fabricated Telegram
message ids so every command was silently exercised against the opening screen.
Both are fixed and both now fail if the bug returns. The lesson stands anyway —
**a green suite is a claim, not evidence**, and this one has twice been wrong.

## Safety / correctness — 9.5

The design rule is that being unsure is a first-class answer:

- Three-valued verdicts — `ELIGIBLE`, `INELIGIBLE`, `UNKNOWN`. A gap is never
  filled with a default.
- Stubs are the literal string `"TODO"` for every type including numbers.
  `annual_value_inr = "TODO"`, never `0`, because a zero looks researched and a
  validator cannot tell the difference.
- No scheme value is served until a human signs it off. Every scheme currently
  reads `PENDING HUMAN VERIFICATION`, so every worker gets `UNKNOWN`, and a test
  enforces that string until the values are checked by a person.
- No name, phone or Aadhaar field exists anywhere in the schema. A field that
  does not exist cannot be stored by accident.
- Every value carries a deep-linked `source_url` and a `verified_on` date.

The 0.5 is deducted because correctness here is *enforced*, not *proven*. The
scheme values are researched from official sources but not yet confirmed by a
person, and a documented failure mode remains: after a transient Telegram
failure a worker's buttons go dead, because restoring them would let an old
question's buttons answer the current one.

## Documentation — 9

`ARCHITECTURE.md`, `BUILD_LOG.md`, `LESSONS.md`, `IMPACT.md`,
`SCHEME_AUTHORING.md`, `VERIFICATION.md`, and a deploy runbook with rollback.
732 comment lines across the source, written to explain the non-obvious
mechanism rather than restate the function name.

`BUILD_LOG.md` records the bugs and the wrong turns, not a cleaned-up narrative.
Not a 10 because none of it has been read by someone who did not build it.

## Code / engineering — 9

Zero third-party dependencies — `dependencies = []`, stdlib only, Python 3.11+.
Multipart upload, the Telegram client and the rule engine are all hand-written
against the documented API. One command runs everything. Docker builds and runs
the full suite at image build time.

Not a 10 because `sathi/channels/telegram.py` and `sathi/conversation/flow.py`
are the two largest modules and carry most of the complexity in the project.

## Current product maturity — 7

**The honest number, and the reason the others are worth reading.**

The engineering is ahead of the product. What is missing is not code:

- No scheme value is signed off, so the bot correctly tells every worker
  `UNKNOWN` for all of them. It cannot yet do the thing it was built to do.
- The Hindi and English strings have never been reviewed by a native speaker.
- 3 schemes (e-Shram, PMSBY, PM-SYM). National coverage is far larger.
- No real user has completed a screening.
- The WhatsApp adapter and the follow-up sender are designed and unbuilt.

Every one of those is blocked on a person — a sign-off, a language review, a
recruited user — rather than on a missing function. That is the correct place
for a project like this to be blocked, and it is still a 7.

## Portfolio / interview value — 9

The defensible parts are the judgement calls, not the line count: refusing to
let an LLM near an eligibility decision, choosing `"TODO"` over `0`, refusing to
ship a scheme value a human has not confirmed, and a privacy model that makes
the wrong thing structurally impossible rather than merely forbidden.

There is also a real debugging record — a double-tap that silently recorded a
worker as an income tax payer and denied them a pension; an age parser that
turned `9.5` into 95; a test suite that was green and blind. Found, traced,
fixed, and covered by regressions that fail without the fix.

Not a 10 until someone who is not the author has used it end to end.

---

## What would move the numbers

Maturity 7 → 9 needs no new code: sign off the scheme values, get the Hindi
reviewed by a native speaker, and put it in front of real workers. The other
scores mostly move on the same evidence — an outside reader, an outside user.
