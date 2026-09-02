# Architecture

Python 3.11+, standard library only.

```
channels/       telegram.py · whatsapp.py     thin adapters, no logic
     │
conversation/   intake flow, question order, consent, state
     │                                    │
     ▼ Profile                            ▼ facts
rules/          DETERMINISTIC             render/    templated Hindi (default)
  evaluate(profile, scheme)                          LLM rephrase (optional)
  → ELIGIBLE | INELIGIBLE | UNKNOWN                  TTS audio note
     │ reads
data/schemes/*.toml    human-authored, provenance-stamped
     │
metrics/        SQLite event log — counts and coarse bands only
```

## The boundary that defines the project

**`sathi/rules/` decides eligibility. It may not import a language model.**

`evaluate(profile, scheme)` is a pure function: no I/O, no clock, no network.
Same inputs, same output, always. That makes it testable with a plain table of
profiles and expected verdicts, and defensible when someone asks how a result
was reached.

The model is used for conversation flow, mapping free text to a category, and
rephrasing Hindi a human wrote. It never sees a threshold, never produces a ₹
figure, and never produces a verdict. With `LLM_API_KEY` unset the whole system
runs on buttons and templated strings with identical results — that is a tested
configuration, not a degraded one.

## Three-valued verdicts

`UNKNOWN` exists because the honest answer is often "we cannot tell". It is
returned when a profile field is missing, or when the scheme file still has a
`"TODO"` in a value the rule needs. The system never fills a gap with a
plausible default.

## Two kinds of scheme-file problem

- **Structural** — unknown key, bad operator, a field we never ask about.
  `SchemeError`, and the app refuses to start. A malformed rule file is a bug.
- **Unverified** — a value still reads `"TODO"`. Loads fine, flagged in
  `Scheme.stubs`, engine returns `UNKNOWN`. An unresearched rule is a known gap,
  not a bug.

## Data model notes

- Scheme rules are TOML because `tomllib` is stdlib and read-only — humans
  write these files, code only reads them — and because TOML supports comments,
  so a citation sits next to the value it justifies. Encoding rules in Python
  would make them unreviewable by an NGO or a government partner, which defeats
  the purpose of open-sourcing this.
- `[paperwork]` is a table at the bottom of each file on purpose. In TOML a
  bare key written after a `[[table]]` header belongs to that table, so
  top-level keys placed at the end silently land inside the last
  `[[exclusions]]` block.
- `Profile` has no name, phone or Aadhaar field. A field that does not exist
  cannot be stored by accident.

## Module map

| Path | What it does |
|---|---|
| `sathi/core/profile.py` | The `Profile` dataclass, income/land/age bands |
| `sathi/core/schemes.py` | TOML loader, structural validator, stub detection |
| `sathi/core/content.py` | Loaders for `occupations.toml`, `states.toml`, `strings_hi.toml` |
| `sathi/rules/operators.py` | The seven operators, three-valued (`True` / `False` / `None`) |
| `sathi/rules/engine.py` | `evaluate()` — the only place eligibility is decided |
| `sathi/conversation/consent.py` | The consent screen |
| `sathi/conversation/flow.py` | Intake state machine, question order, `known_schemes` capture |
| `sathi/render/templates.py` | Result → Hindi, from authored strings only |
| `sathi/render/llm.py` | Optional: free-text → category proposal, rephrasing |
| `sathi/render/audio.py` | Optional: TTS via whatever `TTS_CMD` names |
| `sathi/pack/checklist.py` | Which documents are needed, which are missing |
| `sathi/pack/pack.py` | The one-page pack, built in memory, never written server-side |
| `sathi/channels/base.py` | `ChannelMessage` / `Reply` — the channel boundary |
| `sathi/channels/telegram.py` | Long-polling adapter, `urllib` only |
| `sathi/metrics/events.py` | The **only** writer to the event log |
| `sathi/metrics/report.py` | `impact.html` — the six numbers, provenance, methodology |
| `sathi/main.py` | Terminal session, Telegram bot, startup verification report |

## Decisions worth knowing before you change something

- **The result is computed once, then narrated.** `flow.py` calls
  `evaluate_all()` exactly once and every later screen — result text, document
  checklist, pack — reads that same tuple of `Result`s. Nothing re-decides.
- **"Don't know" is a first-class answer.** It leaves the field unset, which
  produces `UNKNOWN` for any scheme that needed it, plus a question to ask at
  the centre. Forcing a yes/no would manufacture a fact.
- **A rejected LLM guess is discarded, not softened.** The confirmation step is
  the whole guard on free-text intake; "close enough" would defeat it.
- **The pack is HTML, not PDF.** The stdlib has no PDF writer, and a dependency
  needs a reason the stdlib cannot cover. A phone opens and prints this. If
  week-7 users show a real PDF matters, `fpdf2` is the smallest addition.
- **Follow-ups are opt-in** (`FOLLOWUP_SALT` unset = off). They are the only
  real outcome measure available, and the only feature that stores a channel
  id — salted, hashed, in a table with no `session_id` column so it cannot be
  joined back to the event log, purged on completion or after 30 days.
- **The terminal accepts a typed age.** Every question is answerable by picking
  a number from a list; age and state also accept typing, because a keypad beats
  120 buttons. Neither needs a language model, which is what "works with
  `LLM_API_KEY` unset" actually means.

## Verification

`python3 check.py` runs 15 module self-checks and 6 test files, with no
framework and nothing to install.

- `tests/test_schemes.py` — the loader accepts good files and rejects the
  mistakes a human actually makes while authoring rules.
- `tests/test_rule_boundaries.py` — asks whether the ANSWERS are right, not
  just whether the code runs: an independent oracle of each scheme's official
  rules is compared against the engine across every combination of the fields
  any rule touches (~30,000 verdicts), plus each named threshold one per line.
- `tests/test_rules.py` — a table of `(profile, scheme) → verdict`, every
  `UNKNOWN` path, and an assertion that importing `sathi.rules` pulls in no
  LLM module and no HTTP client at all.
- `tests/test_privacy.py` — drives every event type through the log, then
  asserts column by column that only coarse dimensions survived, that no
  profile event can be written before consent, and that the same channel id
  produces unlinkable sessions.
- `tests/test_flow.py` — full sessions with `LLM_API_KEY` unset: eligible,
  ineligible, excluded, "don't know", declined consent, pack generation, and a
  restart-survival check on the event DB followed by a dashboard render.

## What the scheme research changed in the code

The rules were filled from official sources on 2026-08-31, and three of them did
not fit the model as designed. Each change is small and each is forced by a
source, not by taste.

- **`value_basis = "gateway"`.** e-Shram turned out to be a registration and a
  UAN, not a benefit — its FAQ describes a database "to facilitate delivery of
  various social security benefits" and states no payout. It carries
  `annual_value_inr = 0`, which is a fact, not a stub. The accident cover a
  registrant receives *is* PMSBY, already counted in its own file; giving
  e-Shram a rupee value would double-count it.
- **No `prerequisites` link was added.** Neither PMSBY nor PM-SYM requires the
  e-Shram UAN in its own rules, so asserting one would be an invented rule. The
  loader already accepts `prerequisites` if a scheme is ever found that needs it.
- **`Profile.is_epfo_or_esic_member` and `Profile.is_nps_member`.** PM-SYM bars
  members of NPS, ESIC and EPFO; e-Shram defines an unorganised worker as someone
  who is not an ESIC or EPFO member, and never mentions NPS. These were one
  `is_statutory_scheme_member` field until 2026-09-03, which silently gave
  e-Shram PM-SYM's NPS bar and refused the gateway scheme to a worker who held
  NPS alone. Two fields, not three: no scheme distinguishes EPFO from ESIC, and
  every extra field is another question a worker answers on a phone.
- **`premium_inr` may be a sentence.** PM-SYM's contribution runs ₹55/month at
  entry age 18 to ₹200/month at 40. One integer would be wrong for nearly every
  worker. The field is never summed, only shown, so prose is safe there;
  `annual_value_inr` stays strictly an integer because it feeds the metric.
- **Payout and cover are never summed.** See `docs/IMPACT.md`.

## Two languages

The worker picks Hindi or English before anything else — the picker itself is
written in both, because someone who cannot read the question cannot answer it.
Hindi is the default and the fallback.

- UI text lives in `data/strings_hi.toml` and `data/strings_en.toml`.
  `sathi/core/content.py` asserts the English file has **every** key the Hindi
  one has: a half-translated screen is worse than either language alone.
- Scheme text carries optional `ask_en` / `pass_en` / `fail_en` / `reason_en`,
  `documents_en` and `renewal_en`. Optional in the loader, so a Hindi-only
  contribution still works and falls back rather than going blank — but
  `tests/test_schemes.py` holds *our* three files to full bilingual coverage.
- `documents_en` is used only when it has the same length as `documents`. The
  flow tracks "do you have this paper?" by position, so a mismatched
  translation would pair an answer with the wrong document.
- `/language` switches mid-conversation and keeps every answer already given.
  It re-asks the current question in the new language. An unconfirmed
  occupation guess is dropped on switch — an unconfirmed guess must never
  survive quietly.
- **The engine is not bilingual and never will be.** Verdicts are identical in
  both languages; only the words change. `tests/test_flow.py` asserts the two
  paths produce the same `Profile` and the same verdicts.

## Telegram commands

Handled in the adapter, not the flow — they are a channel affordance. The flow
exposes plain methods (`info`, `scheme_list`, `set_language`, `cancel`).

| Command | What it does |
|---|---|
| `/start` `/restart` | Begin, or start over |
| `/language` `/lang` | Toggle Hindi ↔ English, keeping answers |
| `/schemes` | Every scheme, its official source URL, and when it was checked |
| `/privacy` | What is stored, what is never asked |
| `/about` | What this is — and, in plain words, that it is not a government service |
| `/help` | The command list |
| `/clear` | Delete the messages this process still has a record of |
| `/clearall` | Also walk ids backwards to cover the full 48-hour window |
| `/cancel` `/stop` | Drop the profile now and end |

Clearing is best-effort by design: **Telegram refuses to let a bot delete
anything older than 48 hours**, so every reply states the count deleted and says
plainly that older messages remain. Someone clearing a chat about their own
poverty deserves to know exactly what is and is not gone.

Two commands, because one mechanism cannot do both jobs well:

- **`/clear`** deletes the ids this process tracked. Exact, a handful of API
  calls. Its blind spot is a restart: the tracking table is in memory, so
  anything sent before the last restart is invisible to it even when it is well
  inside the 48-hour window. That is a real gap — the first tester hit it — and
  it is why the reply points at `/clearall`.
- **`/clearall`** additionally walks message ids backwards from the command
  itself. In a private chat ids are sequential, so this reaches messages this
  process never saw. It uses `deleteMessages`, which takes **100 ids per call**,
  so a 1000-message window costs ~10 requests rather than ~1000. One call per
  message made it unusable on a long chat.

  The trade: `deleteMessages` returns a bare `True` and never says which ids it
  removed, so the deep clear cannot count what it deleted. Its reply therefore
  says what it did in words instead of quoting a number nobody measured — the
  same rule the ₹ figures follow. If the batch method is unavailable, it falls
  back to one-at-a-time for that chunk only.

Message ids are held in memory only, capped per chat, and die with the process
like the profiles do. Nothing about a chat is written to disk.
