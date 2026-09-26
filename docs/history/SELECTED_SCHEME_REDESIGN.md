# Selected-scheme screening redesign

Status: **implemented and deployed to AWS on 2026-09-14.** The server ran its
full `check.py` gate before `sathi.service` was restarted; GitHub was not
changed.

## Problem

The original route asks one broad intake and evaluates every loaded scheme. A
worker who only wants to check one scheme can therefore receive questions that
do not affect that scheme. The bot should ask the smallest honest set of
questions while keeping the same deterministic eligibility rules.

## User experience

After language and consent, offer two routes:

1. **All verified schemes** — current broad screening, restricted to schemes
   personally signed by Avinash.
2. **Choose schemes** — multi-select one or more signed schemes, then press
   **Done — check selected**.

The picker is paginated for WhatsApp's ten-row list limit:

- up to seven scheme rows
- Show more, when another page exists
- All verified schemes
- Done — check selected

“Schemes to check” is not the existing “schemes already held” question. The
first chooses what the worker wants screened; the latter declares memberships
that can affect a rule, for example PM-SYM membership and NPS-Traders.

Unsigned schemes are excluded from the picker. They must not add questions or
appear to offer a usable answer: they remain `UNKNOWN` until human sign-off.

## Question planner

The planner receives the selected signed scheme codes and derives the fields
from their existing criteria and exclusions. It asks the union of those fields,
in a fixed humane order. It does not copy thresholds, benefits, exclusions or
verdict logic into the conversation layer.

Example:

```text
PMSBY selected
  → age, bank account

PMUY selected
  → age, woman applicant, household LPG status, declaration

NPS-Traders selected
  → age, small trader status, existing PM-SYM membership
```

If more schemes are selected later, preserve answered fields and ask only the
new fields that are still missing.

## Dependencies

Some questions depend on earlier answers. Dependencies control **whether to
ask** a question; the scheme rule remains the only thing that decides a verdict.

```text
woman = yes        → widow status may be relevant
woman = no         → do not ask widow status
woman = unknown    → never invent a value; a widow scheme can stay UNKNOWN

household LPG = no → PMUY declaration may be relevant
household LPG = yes → do not ask PMUY declaration

state = Uttarakhand → Uttarakhand pension conditions may be relevant
```

The current gender answer is a routing fact only: it prevents an irrelevant
widow-status question after the worker says they are not a woman. The scheme
TOML remains the only source of a verdict. `Don't know` never triggers this
skip.

## Result route

Only selected schemes are evaluated and shown. Each result keeps the current
three-valued behaviour:

- `ELIGIBLE` — reported answers meet every verified condition.
- `INELIGIBLE` — a verified condition definitely fails.
- `UNKNOWN` — an answer or signed source value is missing.

The result shows the authored reason, documents and application location. It is
screening, not government approval. A later button should allow “check all
verified schemes” while retaining already answered facts.

## Current core logic

```text
language
  → consent
  → scheme route (all verified / selected)
  → only needed intake questions, in dependency order
  → deterministic rule engine
  → recap + verdicts + documents + application pack
```

The deterministic engine reads `data/schemes/*.toml` and returns only
`ELIGIBLE`, `INELIGIBLE`, or `UNKNOWN`. It never imports an LLM. The conversation
layer asks and records coarse answers; it never calculates a threshold, amount,
or verdict. Telegram and WhatsApp are thin adapters over the same conversation
and rule engine.

## Full core logic: how the bot actually works

### 1. Startup is a safety gate

`sathi.main` loads every TOML scheme file before either channel starts. The
loader refuses malformed files: unknown fields, unsupported operators, missing
source URLs, invalid money shapes, or rules using a profile field the bot cannot
ask. A structurally broken rule stops startup.

An unresearched value is different. It is the literal string `"TODO"`; the file
loads, but that scheme is marked unservable. The engine returns `UNKNOWN` for
it. A human signature (`verified_by`) is the second gate: a source-researched
but unsigned scheme also remains unservable.

### 2. The profile is temporary and deliberately small

The conversation creates an in-memory `Profile`: state, age, coarse income and
land bands, work facts, and scheme-specific answers. It has no name, phone,
Aadhaar, address, date of birth, or free-text identity field. `/cancel` and
normal completion discard it.

The worker chooses Hindi or English, gives consent, and then answers one screen
at a time. Buttons are the normal path. Age and state may be typed; free-text
occupation is treated as a proposal, shown back for confirmation, and discarded
if rejected. An optional LLM may propose an occupation category, but it never
sees scheme thresholds, money, or verdicts; buttons alone work identically.

### 3. Conversation collects facts; it does not decide eligibility

`conversation/flow.py` is a state machine. Its job is only:

```text
ask → validate answer shape → store answer in Profile → ask next useful fact
```

It may skip a question when earlier verified criteria already make a scheme
impossible. It must never turn a skipped or unknown answer into `yes` or `no`.
Question order is centralised so broad facts come first and sensitive questions
such as disability or widowhood come last.

### 4. Rules are deterministic and three-valued

`rules/engine.py` evaluates each scheme against the completed profile. It reads
criteria and exclusions from the scheme TOML; it has no network, database,
clock, or LLM import.

Each comparison is `True`, `False`, or `None`:

```text
all criteria true and no exclusion true → ELIGIBLE
any criterion false or exclusion true   → INELIGIBLE
otherwise                               → UNKNOWN
```

`None` is intentional. It means a worker did not know a required fact, or a
scheme value is still TODO/unsigned. The bot explains the missing condition
instead of pretending it is a refusal.

### 5. Results are computed once

After the final question, `evaluate_all()` returns one immutable result tuple.
The result message, document checklist, application pack, and metrics event all
read that same tuple. Nothing recalculates eligibility later. This prevents a
worker seeing one verdict in chat and a different verdict in their pack.

Money has bases: annual payouts, insurance cover, gateways, and one-time help.
The total metric sums only compatible annual payouts; it never adds an insurance
cover or a loan to a pension total.

### 6. Documents and pack

For eligible results, `pack/checklist.py` unions the authored document lists,
shows them page by page, and records only in-memory ticks. `pack/pack.py` makes
an HTML application sheet in memory. Telegram receives it as a file and may get
a short-lived link; WhatsApp receives safe plain text because its API rejects
HTML. The pack is preparation, never an auto-submission to a government portal.

### 7. Privacy and metrics

Nothing is written before consent. `metrics/events.py` is the only database
writer and accepts a whitelist of coarse values only: for example an age band,
not an exact age. Channel identifiers do not enter session events. Optional
follow-up reach counting uses a separately salted hash and is intentionally not
joinable to the screening-event table.

### 8. Channel adapters contain transport logic only

Telegram long-polls, manages callback acknowledgement, retires stale keyboards,
splits text above Telegram's 4,096-character limit, and supports `/clear`.
WhatsApp verifies webhook signatures, obeys its smaller button/list limits, and
does not offer impossible message deletion. Both adapters pass the same plain
answer into the same conversation state machine and receive the same `Reply`
objects back. Therefore channel choice cannot change a rule verdict.

### 9. Testing and deployment

`check.py` runs module self-checks plus tests for scheme validation, rule
boundaries, exhaustive conversation paths, Telegram/WhatsApp rendering,
webhook safety, privacy, metrics, and pack generation. AWS deployment copies
only bot code/data/tests, preserves the server database and secrets, runs
`check.py` on the VM, and restarts `sathi.service` only if tests pass.

## Implementation result

1. The signed-scheme picker and selected-code state are live.
2. The planner derives core and follow-up fields from selected schemes.
3. Woman → widow and LPG/PNG → PMUY declaration dependency skips are live.
4. The already-held-schemes picker appears only when a selected scheme has a
   membership exclusion that can change its result.
5. Regression tests cover the reduced PMSBY route plus both dependency skips;
   the exhaustive channel path test and full `check.py` pass locally and on
   AWS.
