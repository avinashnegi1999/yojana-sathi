# How it's built.

Python 3.11+. Standard library only.

```
channels/       telegram.py · whatsapp.py · local_web.py (browser)    thin adapters, no logic
     │
conversation/   intake flow, question order, consent, state
     │                                    │
     ▼ Profile                            ▼ facts
rules/          DETERMINISTIC             render/    templated Hindi / English
  evaluate(profile, scheme)                          (TTS module present, not wired)
  → ELIGIBLE | INELIGIBLE | UNKNOWN
     │ reads
data/schemes/*.toml    human-authored, every value cited
     │
metrics/        SQLite event log — counts and coarse bands only
```

<br>

## The boundary.

**`sathi/rules/` decides eligibility. It may not import a language model.**

- **`evaluate(profile, scheme)` is a pure function.** No I/O, no clock, no network. Same inputs, same output — testable with a plain table, and defensible when someone asks how a result was reached.
- **The model has one job:** suggest an occupation category for free text, which the worker confirms before it's recorded. It doesn't drive the conversation or rephrase anything.
- **In normal use it's never called.** No signed scheme has an occupation rule, so the selected-scheme flow never asks occupation. Only a typed state name at the "all or choose" screen reaches the old full route that does.
- **It never sees** a threshold, a ₹ figure or a verdict.
- **With `LLM_API_KEY` unset,** everything runs on buttons and templated text with identical results. A tested configuration, not a degraded one.

<br>

## Three answers.

`UNKNOWN` exists because the honest answer is often "we can't tell". It is returned when a profile field is missing, or when a value the rule needs is still `"TODO"`. The system never fills a gap with a plausible default.

<br>

## Two kinds of file problem.

| Problem | Example | What happens |
|---|---|---|
| **Structural** | Unknown key, bad operator, a field never asked | `SchemeError` — the app refuses to start. A malformed file is a bug. |
| **Unresearched** | A value still reads `"TODO"` | Loads, is listed in `Scheme.stubs`, and returns `UNKNOWN`. A known gap, not a bug. |

<br>

## Decisions worth knowing.

- **Computed once, then narrated.** `flow.py` calls `evaluate_all()` once. The result text, checklist and sheet all read that same tuple. Nothing re-decides.
- **"Don't know" is an answer.** It leaves the field unset, which gives `UNKNOWN` plus a question to ask at the centre. Forcing yes or no would manufacture a fact.
- **Selection changes questions, never rules.** `flow.py` asks only the fields the chosen schemes' criteria and exclusions touch, then passes those schemes unchanged to the engine. A dependency may skip an irrelevant question; it never invents a fact.
- **A rejected model guess is discarded,** not softened. The confirmation step is the whole guard.
- **Age is typed.** Every other question has buttons (state also accepts typing). A keypad beats 120 buttons, and a band would lose the exact boundary a rule needs — 40 versus 41.
- **The recap shows only what was asked.** It used to print "you did not say" for every skipped question.
- **The sheet is HTML, not PDF.** The standard library has no PDF writer, and a phone opens and prints HTML. If users show a real PDF matters, `fpdf2` is the smallest addition.
- **Idle sessions expire.** Every channel drops a conversation's answers after 30 minutes without a reply. Per-chat bookkeeping (language, `/clear` ids) goes after 48 hours.
- **Follow-ups are opt-in** (`FOLLOWUP_SALT` unset = off). The only feature that stores a channel id — salted, hashed, in a table with no `session_id`, purged on completion or after 30 days. **The sender isn't built,** and a hash can't address a message, so the table records intent only.
- **Two hashes, one key.** `feedback.person` and `reach.anon_id` hash the same key with different namespaces. One tester's repeat ratings collapse to one row; a join across the tables finds nothing.

<details>
<summary><b>A known, accepted gap: state commits before the reply is sent</b></summary>

<br>

`Conversation.handle` updates the profile, then the adapter sends the next question. If Telegram or Meta fails on that one send, the worker is at the new step with no live keyboard — the next thing they type re-asks the current question. A durable outbox with retry is a few hundred lines across two adapters for a window one HTTP call wide. Revisit if pilot logs show `send failed` more than once a day.

WhatsApp also acknowledges Meta's POST before its in-memory queue drains, so a crash in between loses that one message. Same accepted trade.

</details>

<br>

## Scheme files.

- **TOML,** because `tomllib` is standard library and read-only — people write these files, code only reads them — and comments let a citation sit beside its value. Rules in Python would be unreviewable by an NGO or a government partner.
- **`[paperwork]` sits at the bottom** on purpose. In TOML, a bare key after a `[[table]]` header belongs to that table, so top-level keys at the end would silently land in the last `[[exclusions]]` block.
- **`Profile` has no name, phone or Aadhaar field.** A field that doesn't exist can't be stored by accident.

How to write one: [`SCHEME_AUTHORING.md`](SCHEME_AUTHORING.md).

<details>
<summary><b>What the scheme research changed in the code</b></summary>

<br>

Each change was forced by a source, not by taste.

- **`value_basis = "gateway"`.** e-Shram is a registration and a UAN, not a benefit — its FAQ describes a database "to facilitate delivery of various social security benefits" and states no payout. It carries `annual_value_inr = 0`, a fact, not a stub. The accident cover a registrant gets *is* PMSBY, already counted in its own file; valuing e-Shram would double-count it.
- **No `prerequisites` link.** Neither PMSBY nor PM-SYM requires the e-Shram UAN in its own rules, so adding one would invent a rule. The loader accepts `prerequisites` if a scheme ever needs it.
- **`is_epfo_or_esic_member` and `nps_exclusion_applies`.** PM-SYM bars NPS, ESIC and EPFO members; e-Shram defines an unorganised worker as not ESIC or EPFO, and never mentions NPS. Until 2026-09-03 these were one field, which gave e-Shram PM-SYM's NPS bar and refused the gateway to a worker who held NPS alone. Two fields, not three: no scheme separates EPFO from ESIC, and every field is another question on a phone.
- **`nps_exclusion_applies` is a finding, not membership.** Intake maps no NPS to false, central-government contributions to true, and other or uncertain types to unknown.
- **`is_unorganised_worker` is asked** when a loaded scheme needs it. Occupation and income never fill it in.
- **`before_nearest_birthday`.** Takes completed age and a positive whole-number cutoff. At cutoff − 1 it returns unknown, because that year spans both sides of the half-year line; at or past the cutoff, false. PMSBY uses it for the source's termination age. No scheme code or threshold is hard-coded in the operator.
- **`premium_inr` may be a sentence.** PM-SYM's contribution runs from ₹55 a month at 18 to ₹200 at 40 — one integer would be wrong for nearly everyone. It is shown, never summed; `annual_value_inr` stays an integer because it feeds the metric.
- **Payout and cover are never added.** See [`IMPACT.md`](IMPACT.md).

Session-only fields stay out of the event schema. Sources and open questions: [`history/SCHEME_AUDIT.md`](history/SCHEME_AUDIT.md).

</details>

<br>

## Two languages.

- **Telegram and WhatsApp ask first,** with the picker written in both languages — someone who can't read the question can't answer it. **The browser opens in English** with a हिंदी switch in the top bar. Hindi is the fallback for any missing text.
- **UI text** lives in `data/strings_hi.toml` and `data/strings_en.toml`. `sathi/core/content.py` asserts English has every Hindi key — a half-translated screen is worse than either language.
- **Scheme text** has optional `ask_en` · `pass_en` · `fail_en` · `reason_en` · `documents_en` · `renewal_en`. A Hindi-only contribution still loads and falls back, but `tests/test_schemes.py` holds every shipped file to full coverage in both.
- **`documents_en` is used only when it matches `documents` in length.** "Do you have this paper?" is tracked by position, so a mismatch would pair an answer with the wrong document.
- **Switching mid-chat** keeps every answer and re-asks the current question. An unconfirmed occupation guess is dropped — it must never survive quietly.
- **The engine isn't bilingual, and never will be.** Only the words change. `tests/test_flow.py` asserts both languages give the same `Profile` and the same verdicts.

<br>

## Clearing a Telegram chat.

Best effort by design: **Telegram won't let a bot delete anything older than 48 hours**, so every reply says what was deleted and that older messages remain. Someone clearing a chat about their own poverty deserves to know exactly what is gone.

- **`/clear`** deletes the message ids this process tracked. Exact, a few API calls. Its blind spot is a restart — the list is in memory — which is why the reply points to `/clearall`.
- **`/clearall`** also walks ids backwards from the command. Private-chat ids are sequential, so it reaches messages this process never saw. `deleteMessages` takes 100 ids per call: a 1,000-message window is about 10 requests, not 1,000. It returns a bare `True`, so the reply describes what it did in words instead of quoting a number nobody measured. If the batch call is unavailable, it falls back to one at a time for that chunk.

Message ids live in memory only, capped per chat, and die with the process. Nothing about a chat is written to disk.

<details>
<summary><b>Every command</b></summary>

<br>

Handled in the adapter, not the flow. The flow exposes plain methods (`info`, `scheme_list`, `set_language`, `cancel`).

| Command | What it does |
|---|---|
| `/start` `/restart` | Begin, or start over |
| `/language` `/lang` | Switch Hindi ↔ English, keeping answers |
| `/schemes` | Every scheme, its official source, and when it was checked |
| `/privacy` | What is stored, what is never asked |
| `/about` | What this is — and that it is not a government service |
| `/help` | The command list |
| `/clear` | Delete the messages this process still tracks |
| `/clearall` | Also walk ids backwards over the full 48 hours |
| `/cancel` `/stop` | Drop the profile now and end |
| `/demo` | Fictional people through the real rules, labelled a demo; opens no session, logs nothing |

</details>

<br>

## Tests.

`python3 check.py` runs 21 module self-checks and 15 test files. No framework, nothing to install.

| File | Proves |
|---|---|
| `tests/test_rule_boundaries.py` | The **answers** are right: a separately written version of each scheme's official rules, compared over 1,377,810 shared-field combinations, then per signed scheme over every combination of its own fields (each must reach `ELIGIBLE`), then each named threshold one per line. |
| `tests/test_rules.py` | `(profile, scheme) → verdict` tables, every `UNKNOWN` path, and that importing `sathi.rules` pulls in no model and no HTTP client. |
| `tests/test_privacy.py` | Every event type goes through the log; only coarse columns survive, nothing is written before consent, and one channel id gives unlinkable sessions. |
| `tests/test_flow.py` | Full sessions with no model key: eligible, ineligible, excluded, "don't know", declined consent, the sheet, and a restart-survival check followed by a dashboard render. |
| `tests/test_schemes.py` | The loader accepts good files and rejects the mistakes people actually make. |

<details>
<summary><b>Module map</b></summary>

<br>

| Path | What it does |
|---|---|
| `sathi/core/profile.py` | The `Profile` dataclass; income, land and age bands |
| `sathi/core/schemes.py` | TOML loader, structural validator, stub detection |
| `sathi/core/content.py` | Loaders for occupations, states and UI strings |
| `sathi/rules/operators.py` | The eight operators, three-valued (`True` / `False` / `None`) |
| `sathi/rules/engine.py` | `evaluate()` — the only place eligibility is decided |
| `sathi/conversation/consent.py` | The consent screen |
| `sathi/conversation/flow.py` | Intake state machine, selected-scheme planner, question order, `known_schemes` |
| `sathi/render/templates.py` | Result → Hindi or English, from authored strings only |
| `sathi/render/llm.py` | Optional: free text → occupation proposal (the only model call) |
| `sathi/render/audio.py` | TTS through `TTS_CMD` — **not called by any channel yet** |
| `sathi/pack/checklist.py` | Which papers are needed, which are missing |
| `sathi/pack/pack.py` | The one-page sheet, built in memory, never written on the server |
| `sathi/channels/base.py` | `Button` / `Reply` — the channel boundary |
| `sathi/channels/router.py` | Sessions, slash commands, keyboard retirement, idle expiry — shared by the chat channels |
| `sathi/channels/telegram.py` | Long-polling adapter, `urllib` only |
| `sathi/channels/whatsapp.py` | Cloud API adapter: signed webhook in, `urllib` out |
| `sathi/local_web.py` | Browser channel: one page, JSON turns, a cookie that is a random routing key, request limits, idle expiry, `?start=` cohort. Opens in English. Drives `Conversation` directly — no slash commands, no reach row. |
| `sathi/metrics/events.py` | The **only** writer to the event log |
| `sathi/metrics/report.py` | `impact.html` — headline numbers, provenance, method; `--cohort`, `--since`, terminal runs excluded |
| `sathi/main.py` | Terminal session, one channel per process, startup verification report |

</details>
