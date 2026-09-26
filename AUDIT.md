# Scheme Sathi / Yojana Sathi — Audit

**Audited:** 2026-09-25, commit `271f182` (branch `main`), working tree at `E:\project Scheme Sathi`.
**Scope:** files inside this folder only. Rounds 1–3 were read-only. **Round 4, at the owner's request, changed code, tests and docs** — see "Fixes applied". They are committed on branch `audit-fixes-2026-09-25` and not merged or deployed. The live bot, website and production host were never checked. Network use in round 2 was read-only: the GitHub API (CI result for this commit), the 7 official pages `sathi.sources` re-reads, packages.ubuntu.com, and Caddy's GitHub releases.
**Context:** Telegram/web/WhatsApp screening bot for unorganised workers. It runs a deterministic TOML rule engine (stdlib Python 3.11+, zero dependencies, SQLite event log) and is deployed on AWS EC2. It is an entry for Code for a Billion 2026, where 25% of the score is "proven impact". Deploy gate is 11 Oct 2026 and submissions close 15 Nov 2026.

---

## What I ran

| Command | Result |
|---|---|
| `python check.py` (the README's `python3` is the Microsoft Store stub on this machine; `python` is 3.12.10) | Exit 0 in 59.7 s. `all checks passed`, `1,377,810 verdicts checked`, `hi: 4930 paths walked, 1145 completed sessions` (same for `en`). |
| `python -m sathi.main --db <scratch>/cli.db` with piped input (README "one screening in the terminal") | **Crashed** at startup: `UnicodeEncodeError: 'charmap' codec can't encode character '\u2192'` (see m1). With `PYTHONIOENCODING=utf-8` it ran a full session. |
| `python -m sathi.main --preview telegram --no-db` with the exact inputs in `docs/DEMO_SCRIPT.md` | Ran, but went down a different path than the script describes (see Docs vs Code). |
| `python -m sathi.metrics.report --db <copy of sathi.db> --out <scratch>/impact.html` | `wrote …impact.html`, exit 0. |
| Throwaway scripts (in scratchpad, not in the repo) against `sathi.*` and a loopback `local_web` server | Results quoted in each issue below. |
| **Round 2**, after tools were installed: `check.py` under **Python 3.11.16** (installed with `uv`) | Exit 0 in 75 s, `all checks passed`. The declared `requires-python >=3.11` holds. |
| GitHub Actions for commit `271f182` (public API, run `35489462474`) | `checks` = success. Step `python3 check.py` passed, and step `docker build` passed (04:34:50 → 04:35:40 UTC, 2026-09-20). This is the Linux container build, which itself runs `check.py`. |
| `python -m sathi.sources` (read-only: it fetches pages and writes nothing) | Exit 0. `Re-reading 7 official page(s)`. All 44 claims still hold. `~ ESHRAM` and `~ PM_SYM`: "every value still checks out, but the page text changed since 2026-09-09". No record exists for IGNOAPS, IGNWPS, IGNDPS or NPS_TRADERS (m4). |
| `local_web` behind **Caddy 2.6.2** and **2.11.4** (official builds, SHA-512 verified), with the exact site block `deploy/enable-web.sh` writes | Results in M6 and M8. 2.6.2 is what `apt install caddy` gives on Ubuntu 24.04 (`2.6.2-6ubuntu0.24.04.3`, packages.ubuntu.com), and `provision-aws.sh:100` provisions 24.04. |
| `TelegramBot.poll_once()` with the wire stubbed, worker at the rating prompt, typing `²` | The session is dropped and the worker gets "screening stopped" (M7). |
| `echo "Avinash Negi" \| python -m sathi.review PMJJBY` on a copy of the repo | `sathi.review needs a terminal…`, exit 2, file unchanged. Works as documented. |
| **Still not run** | A local `docker build`: Docker Desktop and WSL2 need administrator approval and a reboot, and this account is not an administrator. The CI result above stands in for it. `--telegram` / `--whatsapp` with real tokens: CLAUDE.md forbids a second poller. The production Caddyfile and host. |

Side effect: running Python regenerated gitignored `__pycache__/*.pyc`. `git status` is otherwise unchanged apart from this file. Installed at user level: `uv` 0.12.19 (`pip install --user uv`) and CPython 3.11.16 under `%APPDATA%\uv\python`. The Caddy binaries were unzipped into the session scratchpad only.

---

## Re-verification (round 3, same commit `271f182`)

I re-checked each Critical and Major item from scratch. For each one I re-read the cited lines, looked specifically for counter-evidence (code paths, tests or docs that would make it wrong), and re-ran the reproduction. **11 are confirmed and none is wholly a false positive.** Four needed corrections, and one sub-point (M9's Docker bullet) was a false positive and has been withdrawn. Each issue below carries a *Re-verification* line with the evidence.

| # | Verdict | Deciding evidence (round 3) |
|---|---|---|
| C1 | **CONFIRMED** | The Hindi result screen **and** the sheet both render `इनसे आपको साल भर में लगभग 36,000 रुपये मिल सकते हैं।` for a 25-year-old. `grep premium sathi/render sathi/pack sathi/conversation sathi/channels sathi/local_web.py` finds nothing. The contribution amount appears on neither screen nor sheet. |
| C2 | **CONFIRMED**, one claim softened | No channel, cohort or role filter anywhere in `report.py` or `links.py`. On a copy of the local DB, `report.numbers()` gives `screened: 7` from 6 Telegram and 1 WhatsApp test sessions. The report's own self-check counts `cli` sessions (`report.py:461-482`). |
| C3 | **CONFIRMED** (per repo docs) | `SUBMISSION_DRAFT.md:27, 197`. The latest status is `CLAUDE.md:111`, "still unresolved, still the top project risk", and `HANDOFF_2026-09-14.md:62`: `hello@` bounced; `partners@` and Discussion #13 unanswered. The organisers' current position can't be verified from the repo. |
| M1 | **CONFIRMED**, scope corrected | No scheme rule uses `occupation`. A branching walk of all 11 button routes never reached `OCCUPATION`. It **is** reachable when a worker types a state name at the all-or-choose screen (`flow.py:479-483`), so "never asked on any live route" became "no button route asks it". |
| M2 | **CONFIRMED** | `synthesise` has no caller. `Reply(audio=…)` appears only inside `whatsapp.py`'s `_self_check` (lines 931-933). `llm.py` defines one model function, `propose_occupation`. |
| M3 | **CONFIRMED** | The re-run gives 1,377,810 verdicts, and **6 of 10** signed schemes get zero ELIGIBLE. `test_the_named_boundaries_individually` (`test_rule_boundaries.py:255-313`) covers only PMSBY, PM-SYM, e-Shram and PM Vishwakarma. The NSAP pensions have no eligible assertion in any test. |
| M4 | **CONFIRMED**, narrowed | All 4 files: line 1 says "NO HUMAN SIGN-OFF IS CLAIMED" next to `verified_by = "Avinash Negi, …"`. The myScheme citations are in **IGNOAPS and IGNWPS only**. IGNDPS cites a government PDF on s3waas.gov.in, and NPS-Traders cites maandhan.in. |
| M5 | **CONFIRMED** | The only `check.py` run on the host (`install-on-vm.sh:76`) comes after the `rsync` into `/opt/sathi` (`:62`), with no staging check or rollback. All three units have `Restart=always`. |
| M6 | **CONFIRMED**, fix corrected | Fresh run: `[1,2]` raises `AttributeError`. A worker mid-consent was evicted after 500 anonymous `/start`s, and their next tap silently opened a new session. A negative Content-Length hangs directly but gets 400 through Caddy. The page JS has no `catch`/`r.ok`. Neither Caddy build has a `rate_limit` module, so the suggested fix is corrected. |
| M7 | **CONFIRMED** | `flow.py:978` still uses `isdigit()`. `²`, `④` and 5,000 digits all raise `ValueError`. The stubbed Telegram run drops the session and sends "screening stopped". |
| M8 | **CONFIRMED** | The only removals are `router.py:175, 197, 208` and the FIFO caps at `local_web.py:105, 134`. No time-based expiry exists; Telegram's time code only serves `/clear`. The Caddy re-run logged `uri=/document/PACKTOKEN_abc123` with IP and User-Agent on 2.6.2 and 2.11.4. |
| M9 | **CONFIRMED** (2 of 3 points); **Docker point FALSE POSITIVE** | Confirmed: "Ten signed schemes" sits over an **11-row** table that includes the unsigned widow pension. The sole-authorship line conflicts with **4** public `verified_by = "claude — AUTO-RESEARCHED…"` files. Withdrawn: `Docker` is in an unlabelled stack strip beside "Ubuntu + systemd", and the repo does ship a Dockerfile that CI builds, so it claims nothing false. |

---

## Fixes applied (round 4, working tree on top of `271f182`)

**Committed on branch `audit-fixes-2026-09-25`, not merged, pushed or
deployed.** `bd28a75` holds the code, tests and deploy scripts (27 files);
`32f53e6` holds the docs, landing page and comment-only scheme headers (16
files); the commit after them adds this report. The live bot and site still run
`271f182` until the branch is merged and `deploy/install-on-vm.sh` is run.
Scheme values, sources and signatures were not touched: the only changes under
`data/schemes/` are comment lines (checked with `git diff -U0`).

**Proof it still works:**
- `python check.py` → `all checks passed` on **Python 3.12.10 and 3.11.16**, including the new per-scheme sweep (`22,248 per-scheme verdicts across 10 signed schemes, each reaching ELIGIBLE`).
- The demo path (`python -m sathi.main --preview telegram|whatsapp --no-db`) was re-run end to end in both languages.
- The browser page was driven in the preview pane: taps, `?start=csc`, and a simulated 500 or network error.
- The new Caddy block was generated by `enable-web.sh` itself, passes `caddy validate` on 2.6.2 and 2.11.4, and was run on both to confirm redaction.
- `python -m sathi.sources` now watches 8 pages.

| # | Status | What changed | Evidence |
|---|---|---|---|
| C1 | **Fixed in code**; new Hindi needs native review | The total now says each pension is paid only from its own starting age. Every scheme with a cost shows **"You pay"** / **"आपको देना होगा"** on the screen and the sheet, via one function (`templates.premium_text`). Integer premiums use `_TEMPLATE.toml`'s own unit (₹ a year). Prose premiums are shown only in their own language, with a generic "ask at the centre" line otherwise. | `tests/test_flow.py::test_a_future_pension_is_never_shown_as_money_this_year` renders the 25-year-old case in both languages, on the screen and the sheet. |
| C2 | **Instrument fixed. Evidence still zero (not fixable in code).** | The `events.cohort` column holds the arrival slug (`?start=csc`), written only after consent, from a fixed list in `events.SOURCE_SLUGS`. The report and `/stats.json` exclude `cli` by default; `--cohort`, `--include-cli`, and `--db` defaulting to `DB_PATH` were added. | `test_privacy.py::test_cohort_is_a_fixed_slug_and_only_after_consent` covers the whitelist, the before-consent case, and the `/start csc` path through the router. The `report.py` self-check proves `cli` is excluded and `--cohort csc` narrows every number. |
| C3 | **Not fixable in code** | — | Needs a written organiser answer. |
| M1 | **Fixed** (recap and docs); product decision left open | The recap lists only questions actually asked. README, ARCHITECTURE, IMPACT, SUBMISSION_DRAFT and `.env.example` now say the model is not called in normal use. | `python -m sathi.main --preview …`: the recap has no "work / land / household: you did not say". Deciding what the model *should* do is Avinash's call. |
| M2 | **Fixed by correcting the claims** | README and ARCHITECTURE no longer claim voice notes or rephrasing. `audio.synthesise()` is marked "not wired". Voice itself is **not built**. | `grep -n rephras README.md docs/ARCHITECTURE.md` shows only the corrected sentences. |
| M3 | **Fixed** | A per-scheme sweep over exactly each signed scheme's own fields, with ELIGIBLE required for each. It found and fixed a gap in the oracle: NPS-Traders' PM-SYM exclusion, from `docs/audit-evidence/nps-traders-maandhan-faq-2026-09-14.txt:11`. UK widow's stale oracle note is marked, not copied from the TOML. | A planted IGNOAPS BPL slip is caught: `IGNOAPS {'age': 60, 'is_bpl': True}: got ineligible, oracle says eligible`. |
| M4 | **Headers fixed; citations deferred to the next re-sign** | Line 1 of the four files now names the signature date and the evidence PDF, instead of "NO HUMAN SIGN-OFF IS CLAIMED". IGNOAPS and IGNWPS still cite myScheme per value, because changing a `source_url` under an existing signature is exactly what `sathi.review` exists to prevent. | `git diff -U0 -- data/schemes/` shows comment lines only. |
| M5 | **Fixed** | `check.py` runs on `/tmp/sathi-stage` before the rsync into `/opt/sathi`, which also skips `__pycache__`. | `bash -n deploy/install-on-vm.sh` passes. The gate is at line 68, and the rsync follows at 70–71. |
| M6 | **Fixed** | Exactly one non-negative Content-Length, ≤ 10 000 bytes, a JSON object with a string answer, else 400/413. A 10 s socket timeout. A crashing turn returns a 500 message and drops the session. Idle-LRU replaces FIFO eviction. 30 new sessions per client per 10 min, keyed on the last `X-Forwarded-For` entry. The page handles `!ok` and network errors. | The `local_web` self-check does real HTTP for `[1,2]`, `42`, `{}`, a negative length, an oversized body, the crash path, the rate limit, and a neighbour unaffected by it. The browser pane showed the error message on a 500 and a network drop. |
| M7 | **Fixed** | `isdecimal()` and a length cap, like age. | `tests/test_input_privacy.py::test_rating_reasks_on_digits_int_cannot_read` covers `²`, `④`, 5,000 digits, `0`, `11`, `-3`, `7.5`, and accepts `७`. |
| M8 | **Fixed in code and deploy scripts; the live Caddyfile still needs a manual edit** | Router sessions expire after 30 idle minutes (Telegram, WhatsApp) and per-chat bookkeeping after 48 h. Web sessions expire after 30 min and sheets after 1 h. `enable-web.sh` writes a redacting log block, and refuses to continue if an unredacted one is already there. | The router self-check uses a fake clock. Redaction was run on Caddy 2.6.2 and 2.11.4: no token, User-Agent, forwarded IP or cookie reached the log. |
| M9 | **Fixed** (the authorship line needs Avinash's approval — it is his voice) | The signed-schemes table has 10 rows, and the widow pension is described as not served. The authorship line now says an AI assistant wrote code and first drafts under his review, matching CLAUDE.md. | A row count under "Ten signed schemes" gives 10. |
| m1 | **Fixed** | `sathi.main` reconfigures stdout/stderr to UTF-8. | Piped `python -m sathi.main --no-db` runs with no encoding override. |
| m2 | **Fixed** | `.env.example` now documents `REACH_HMAC_KEY`, `PACK_*`, `BOT_URL`, `STATS_ORIGIN`, `LLM_BASE_URL`/`LLM_MODEL`, `WHATSAPP_BIND`, `FOLLOWUP_SALT` and `SATHI_DATA_DIR`. | — |
| m3 | **Fixed** | `ChannelMessage` and `Outbox` removed. `set_purpose`, `schedule_followup` and `audio.synthesise` are marked as not called by any channel. | — |
| m4 | **Partly fixed** | NPS-Traders is now watched (`data/sources/nps_traders.json`, 6 claims). Visitor counters and "Last Update" stamps no longer make every maandhan.in and eshram.gov.in fetch look changed. The three NSAP pensions **cannot** be watched by this tool (a JavaScript page, a PDF, an unresolvable host); that is documented in `data/sources/official-text/README.md`. | Two fetches seconds apart now fingerprint identically. ESHRAM and PM_SYM keep showing `~` until a person re-reads them and re-saves their records. |
| m5 | **Fixed** | A `docs/README.md` index marks each doc as current or historical. The README calls the assessment historical and points here. | Every file in `docs/` is listed. |
| (found while fixing) | **Fixed** | Added `.gitattributes` with `*.sh`/`*.service` `eol=lf`, and converted `deploy/` to LF. With `core.autocrlf=true` these were checked out as CRLF, and `enable-web.sh` is copied to the Linux host from the working tree, where bash fails on `
`. | Byte count: 0 CR in every `deploy/*.sh` and `*.service`; `bash -n` passes on each. |
| Docs vs Code | **Fixed**, except one historical note | Every row in the table below was corrected in its file. The exception is `HANDOFF_2026-09-14.md:27`, which lists local untracked files and is left as history. | The relative-link check finds only that one path. |

### What stops this being a 10/10 — none of it can be done in code

1. **No field evidence.** Proven impact is 25% of the score, and it is still zero. The pilot link and cohort report now exist; the pilot itself does not.
2. **AgentFoundry.** The required checkbox needs a written organiser answer (C3).
3. **Hindi review.** A native speaker needs to read aloud all Hindi, including the new strings (marked `# ? Hindi review` in `data/strings_hi.toml`).
4. **Re-signing** IGNOAPS and IGNWPS against their PIB releases (to drop the myScheme citations), writing UK widow's oracle from the department page before re-signing it, and re-baselining the ESHRAM and PM_SYM drift records after reading them.
5. **Deploying:** commit, then `deploy/install-on-vm.sh`, then replace the live web host's `log` line per `deploy/RUNBOOK.md`.
6. **Product choices** only Avinash can make: what, if anything, the model should do (M1), and whether to build voice (M2) for a low-literacy track.

---

## Critical

### C1. The worker is told a future, contributory pension is money "in a year"

> **Re-verification: CONFIRMED.** Re-rendered for the same 25-year-old. The Hindi result screen and the Hindi sheet (`pack.build`) both print `इनसे आपको साल भर में लगभग 36,000 रुपये मिल सकते हैं।`. `premium_inr` has no reader in `sathi/render`, `sathi/pack`, `sathi/conversation`, `sathi/channels` or `local_web.py`.

This is the headline ₹ figure, and the target user reads it in Hindi.

- `data/strings_hi.toml:174`
  ```toml
  value_line = "इनसे आपको साल भर में लगभग {total} रुपये मिल सकते हैं।"
  ```
- `data/strings_en.toml:160`
  ```toml
  value_line = "These could be worth about ₹{total} to you in a year."
  ```
- `sathi/render/templates.py:159`
  ```python
  lines.append(s("result.value_line", lang, total=rupees(payout)))
  ```

`payout` includes PM-SYM and NPS-Traders at ₹36,000. Both pay nothing until age 60, and both require the worker to contribute every month.

**Reproduced.** For a 25-year-old in Bihar, the Hindi result says `इनसे आपको साल भर में लगभग 36,000 रुपये मिल सकते हैं।` ("you could get about ₹36,000 in a year"). The PM-SYM line above it shows only `60 साल की उम्र के बाद हर महीने ₹3,000 पेंशन।`. The result screen trims each summary to one sentence (commit `271f182`), so the contribution is not mentioned at all. The sheet repeats the same total line; its full summary says the worker contributes (`जितना आप जमा करेंगे…`) but never how much.

The contribution amount exists in the data but is never rendered:
- `data/schemes/pm_sym.toml:43`
  ```toml
  premium_inr = "₹55 से ₹200 प्रति माह — प्रवेश आयु पर निर्भर …"
  ```
- `sathi/core/schemes.py:326` claims `# * It is never summed, only shown, so prose is safe here.`
- `grep -rn premium sathi` finds only `review.py` and `sources.py`. Nothing in `templates.py` or `pack.py` renders it.

The dashboard carries the right caveat (`report.py:349` says "PM-SYM is a future pension from age 60, subject to contributions"). The worker never sees it.

**Fix:**
- Split the total into "payable now" (the state and NSAP pensions) and "future pension from age 60 — you pay ₹X/month".
- Render `premium_inr` on the result screen and on the sheet for every eligible scheme.
- Word the Hindi line so it cannot be read as money arriving this year.
- Add a test that renders the result for an 18–40-year-old PM-SYM match and asserts the word "60" and the contribution appear in the total line.

### C2. Proven impact (25% of the score) is zero, and the instrument cannot separate a pilot from testing

> **Re-verification: CONFIRMED, one claim softened.** No channel, cohort or role filter exists in `report.py` or `links.py`. The role is written only to `feedback` (`events.py:446`), whose schema has no session column (`schema.sql:109-117`). On a copy of `sathi.db`, `report.numbers()` gives `screened: 7`, all of it test traffic: `[('telegram', 6), ('whatsapp', 1)]`. The claim that a terminal run reaches production is softened below.

- `README.md:237-238`
  ```
  produce real ones has not run. Nobody has been screened yet except the
  maintainer testing his own bot.
  ```
- `sathi/metrics/report.py:48-52` counts every session on every channel, with no channel or cohort filter:
  ```python
  screened = _scalar(
      conn,
      f"SELECT COUNT(DISTINCT session_id) FROM events"
      f" WHERE event_type='eligibility_evaluated'{where}", p,
  )
  ```
  That includes `cli` sessions: the report's own self-check builds `cli` sessions and counts them (`report.py:461-482`). `main.py:96` defaults `--db` to `DB_PATH`, so a terminal run lands in the production log **only if** `DB_PATH` is exported in that shell. Systemd's `EnvironmentFile` does not apply to an interactive session. *(Softened in round 3; round 1 stated it unconditionally.)*
- `sathi/conversation/flow.py:995-1000`: the only tester/self/helping label goes to the `feedback` table, which by design has no session id:
  ```python
  self.log.record_feedback(self._rating, self._suggestion, self.channel, role,
                           person=self.person)
  ```
  So tester sessions cannot be removed from `screened`, `surfaced` or the ₹ totals. `docs/PROGRESS.md:55` claims the opposite: "so developer testing can be excluded from pilot evidence".
- `sathi/pack/links.py:206-209` publishes that unfiltered `screened` count to the public landing page through `/stats.json`.
- The web channel is anonymous with no rate limit (see M6), so screenings can also be scripted.
- The deploy gate is 11 Oct, 16 days from this audit. CLAUDE.md still lists "Partner outreach" as blocked, with no named partner.

**Fix:**
- Tag every session with a coarse cohort. The router already captures a whitelisted `/start csc` slug in `Router._source`. Write that slug (not an id) as an events column, the same way `channel` is.
- Make `report.py` default to excluding `channel='cli'` and non-pilot cohorts, and print the filter in the methodology footer.
- Freeze a pilot start date and always report with `--since`.
- None of this matters until a named CSC partner puts real workers through before 11 Oct. That is the actual critical path.

### C3. The required AgentFoundry confirmation is still unresolved

> **Re-verification: CONFIRMED, as far as the repo can show.** No later doc records an answer. The most recent statements are `CLAUDE.md:111` ("still unresolved, still the top project risk") and `HANDOFF_2026-09-14.md:62`: `hello@codeforindia.org` hard-bounced, `partners@` and GitHub Discussion #13 unanswered. The organisers' actual current position cannot be verified from the repo.

- `docs/submission/SUBMISSION_DRAFT.md:27`
  ```
  1. **`Built using AgentFoundry (AF), the official IDE` is a REQUIRED checkbox.**
  ```
- `docs/submission/SUBMISSION_DRAFT.md:197`
  ```
  been established. **Do not check the required AF confirmation yet.**
  ```

The repo's own docs say the form cannot be filed without this box, and that ticking it today would be false. This is not a code problem, but it can zero the entry regardless of code quality.

**Fix:** get a written organiser answer this week. If AF work is required, do and record it as in `docs/submission/AGENTFOUNDRY_MIGRATION.md` before building anything else.

---

## Major

### M1. No button route asks occupation, so the only AI in an "Agentic-AI" entry never runs for a worker who taps buttons

> **Re-verification: CONFIRMED, scope corrected.** A regex search for `field = "occupation"` in `data/schemes/` finds nothing. A branching walk (up to 6 buttons per screen, both typed ages) of `pick:all` and each signed scheme alone never reached `OCCUPATION` or `OCCUPATION_FREE`. The only other entry is `_advance_core` with `_legacy_full` set (`flow.py:481`). That happens when a worker **types a state name** at the all-or-choose screen instead of tapping, which is possible on Telegram and WhatsApp (the web shows no text box there) and is what `DEMO_SCRIPT.md` does. The title and consequence 1 were reworded; round 1 said "never asked on any live route".

- `sathi/conversation/flow.py:333-335`: core questions come only from fields the selected schemes use:
  ```python
  wanted = ((set(_CORE_FIELD_STATES) - {"is_unorganised_worker"}) if self._legacy_full else
            {c.field for sc in self._active_schemes().values()
             for c in sc.criteria + sc.exclusions})
  ```
- No scheme file uses `occupation`. Per `grep '^field *=' data/schemes/*.toml`, the fields in use are age, is_bpl, has_bank_account, is_income_tax_payer, state, … and never occupation.
- **Reproduced** by walking `pick:all` and each of the 10 signed schemes alone: `occupation asked: False` on all 11 routes.

Consequences:
1. `llm.propose_occupation` (`flow.py:567`) is only reachable through the legacy route at `flow.py:479-483`. That route exists for callbacks in flight during a deploy, and it is entered when a worker types a state name at the all-or-choose screen. No button leads to it, so with `LLM_API_KEY` set, a worker who only taps buttons triggers no model call.
2. The recap shows every worker `• work: you did not say`, `• land: you did not say` and `• household size: you did not say` for questions they were never asked (reproduced).
3. The event log's `occupation` column is NULL for new sessions, so the dashboard's "Work they do" table is empty. README:289 and IMPACT.md:50 still list occupation as a logged dimension.

**Fix:**
- Decide what the model does. If nothing, stop calling this an agent and say so. If something, wire it into a path real users reach.
- Only print recap lines for fields actually asked (`self._answered_fields`).
- Either ask occupation explicitly as a metrics-only question or drop it from the docs.

### M2. Voice notes and LLM "rephrasing" are documented as working but do not exist

> **Re-verification: CONFIRMED.** `synthesise` has no caller. `main.py:22` imports `audio` only for `is_available()` at `:45`. The only `Reply(audio=…)` in `sathi/` is inside `whatsapp.py`'s `_self_check` (lines 931-933). `llm.py` defines `_within_budget`, `is_available`, `_ask`, `propose_occupation` and `_self_check`, with no rephrasing function. The only "rephrase" in the code is a comment (`engine.py:41`).

- `README.md:336`
  ```
  | `TTS_CMD` | Replies also arrive as an audio note, e.g. `espeak-ng -v hi -w {out} {text}`. |
  ```
  But `sathi/render/audio.py:30` `def synthesise(...)` is never called outside its own self-check, and nothing sets `Reply.audio` except tests (`telegram.py:882`, `whatsapp.py:931`). Setting `TTS_CMD` only changes the startup line (`main.py:45`).
- `README.md:335`
  ```
  | `LLM_API_KEY` | Free-text intake maps to a category, always confirmed by the worker; text is rephrased. Verdicts are unchanged. |
  ```
  But `sathi/render/llm.py` has one model call, `propose_occupation`. Its own self-check says `# * Classification is the only model call; eligibility stays templated.`

For a track named "Livelihood for the Uneducated", a text-only product that claims voice will be probed by judges.

**Fix:** delete both claims everywhere (README, ARCHITECTURE, CLAUDE.md "in spoken Hindi"), or build them. `SUBMISSION_DRAFT.md:116` already disclaims voice, so the README contradicts the submission.

### M3. The "1,377,810 verdicts" correctness sweep never produces ELIGIBLE for 6 of the 10 signed schemes

> **Re-verification: CONFIRMED.** The re-run over the test's own `AGES × INCOME × TRI⁶` product gives `1,377,810` verdicts. The signed schemes with zero ELIGIBLE are `['IGNDPS', 'IGNOAPS', 'IGNWPS', 'NPS_TRADERS', 'PMUY', 'UK_OLD_AGE']` (6 of 10). I checked the counter-evidence:
> - `test_the_named_boundaries_individually` (`test_rule_boundaries.py:255-313`) covers only PMSBY, PM-SYM, e-Shram and PM Vishwakarma.
> - Elsewhere, UK old-age has age-edge asserts (`test_expansion.py:30-31`), PMUY has a boolean sweep, and NPS-Traders has one hand-picked eligible case (`test_flow.py:654`).
> - **IGNOAPS, IGNWPS and IGNDPS have no eligible assertion in any test.** Only their ₹ amounts are checked (`test_expansion.py:51`).

- `README.md:371-375`
  ```
  - `tests/test_rule_boundaries.py` — asks whether the **answers** are right, not
    whether the code runs. … compared against the engine
    across every combination of the fields any rule touches — 1,377,810 verdicts,
  ```
- `tests/test_rule_boundaries.py:233-234` varies only 8 fields:
  ```python
  for age, income, bank, tax, epfo, nps, worker, government_family in itertools.product(
      AGES, INCOME, TRI, TRI, TRI, TRI, TRI, TRI
  ```
  `state`, `is_bpl`, `is_widow`, `has_disability_80pct`, `is_small_trader`, `is_woman`, `household_has_lpg`, `pmuy_declaration_met` and `uk_pension_*` stay `None`.
- **Measured** by re-running the same product and counting verdicts per scheme:
  ```
  IGNDPS      {'unknown': 76545, 'ineligible': 15309}
  IGNOAPS     {'unknown': 35721, 'ineligible': 56133}
  IGNWPS      {'unknown': 56133, 'ineligible': 35721}
  NPS_TRADERS {'unknown': 9072,  'ineligible': 82782}
  PMUY        {'unknown': 76545, 'ineligible': 15309}
  UK_OLD_AGE  {'unknown': 35721, 'ineligible': 56133}
  ```
  A wrong BPL, trader, widow or state condition in those files cannot be caught here. `test_expansion.py:311-340` sweeps the UK and PMUY booleans (3,024 checks). No oracle sweep covers the ELIGIBLE side of IGNOAPS, IGNWPS, IGNDPS or NPS-Traders.
- The "independent oracle" was written by the same party as the TOML files (CLAUDE.md:18, "Claude writes the code"). It checks two encodings against each other. It is not an external check.

**Fix:** add `state`, `is_bpl`, `is_widow`, `has_disability_80pct` and `is_small_trader` to the product (or run a second product for them), and assert that every signed scheme reaches ELIGIBLE at least once. Correct the README sentence.

### M4. Four signed scheme files still say "NO HUMAN SIGN-OFF IS CLAIMED", and two cite an aggregator the project forbids

> **Re-verification: CONFIRMED, narrowed.** Line 1 of `ignoaps`, `igndps`, `ignwps` and `nps_traders.toml` reads `# Source-researched draft, 12 September 2026. NO HUMAN SIGN-OFF IS CLAIMED.`, while `verified_by` names `Avinash Negi, checked 2026-09-14/15`. All `source_url`s were re-listed:
> - IGNOAPS (lines 42, 54) and IGNWPS (46, 58, 70) cite `myscheme.gov.in`.
> - IGNDPS cites a government PDF on `cdnbbsr.s3waas.gov.in`, and NPS-Traders cites `maandhan.in`, which are primary sources.
>
> The aggregator half of the title now says "two"; round 1 implied all four.

- `data/schemes/ignoaps.toml:1-6`
  ```toml
  # Source-researched draft, 12 September 2026. NO HUMAN SIGN-OFF IS CLAIMED.
  # ! nsap.nic.in refused every connection on 12 September 2026, so the values
  # ! below were read from the myScheme entry … That is an aggregator, …
  # ! Before signing: open nsap.nic.in/circular.do?method=faq
  ```
  But `ignoaps.toml:21` has `verified_by = "Avinash Negi, checked 2026-09-15"`.
- The same first line appears in `igndps.toml:1`, `ignwps.toml:1` and `nps_traders.toml:1`, all in `SIGNED_OFF` (`tests/test_schemes.py:296`).
- Criteria still cite myScheme: `ignoaps.toml:42` `"https://www.myscheme.gov.in/schemes/nsap-ignoaps"` and `ignwps.toml:46`.
- `CONTRIBUTING.md:11` requires sources "not the site root, not a news article, not an aggregator".
- `docs/audit-evidence/*.pdf` shows primary PDFs were collected, but the files do not cite them per value.

A judge who opens any of these files sees a signature directly contradicting line 1.

**Fix:** update each header to what was actually checked (date, PDF name in `docs/audit-evidence/`) and replace the myScheme `source_url`s with the primary document. If the primary source was not read, unsign.

### M5. The deploy "gate" runs after the new code is already in place

> **Re-verification: CONFIRMED.** Between the staging copy and the swap there is no `check.py` execution; the other matches in the script are filenames in the `rsync`/`tar` lists. There is no symlink flip or rollback. `Restart=always` is at `sathi.service:47`, `sathi-whatsapp.service:46` and `sathi-web.service:23`.

- `deploy/install-on-vm.sh:62`
  ```bash
  rsync -a --delete /tmp/sathi-stage/{sathi,data,tests,check.py,pyproject.toml} /opt/sathi/
  ```
- `deploy/install-on-vm.sh:74-76`
  ```bash
  # ! The same check.py that gates the Docker build gates the deploy. A VM that
  # ! cannot pass its own tests must not talk to a worker.
  cd /opt/sathi && python3 check.py
  ```

If `check.py` fails, `set -e` stops the script, but `/opt/sathi` already holds the failing code. All three units run `Restart=always` (`deploy/sathi.service:47`), so the next crash or reboot serves it.

**Fix:** run `cd /tmp/sathi-stage && python3 check.py` before the rsync into `/opt/sathi`, or rsync into a versioned directory and flip a symlink only on success.

### M6. The public web channel lacks the input hardening the WhatsApp webhook has

> **Re-verification: CONFIRMED, one fix corrected.** Fresh loopback run:
> - `[1,2]` → `RemoteDisconnected`, and the server raised `AttributeError`.
> - A worker session at `consent` was gone after 500 anonymous `/start` POSTs (`sessions: 500`). The worker's next tap returned 200 on **a new session**; their earlier answers were silently discarded.
> - Negative Content-Length direct → no response in 3 s. Through Caddy → 400 (round 2).
> - `local_web.py:63` has no `catch`/`r.ok`; the only grep hit for "catch" is a Python comment at `:257`.
>
> Fix corrected: `caddy list-modules` on 2.6.2 and 2.11.4 shows **no `rate_limit` module**, so "add a Caddy `rate_limit`" needs a custom build.

All reproduced against `handler_class()` on loopback:

- **A non-object JSON body crashes the handler.** `sathi/local_web.py:194` does `answer = data.get("answer", "")`, but only `(ValueError, json.JSONDecodeError)` is caught (`:197`). A body of `[1,2]` raises `AttributeError`. Direct, the client gets `RemoteDisconnected`. Through Caddy 2.6.2 and 2.11.4 with the deployed site block, the client gets `502` (reproduced). It should be a 400.
- **A negative Content-Length reads until the client closes, but only on loopback.** `local_web.py:192-193`:
  ```python
  size = int(self.headers.get("Content-Length", "0"))
  data = json.loads(self.rfile.read(min(size, 10_000)))
  ```
  `Content-Length: -1` gives `rfile.read(-1)`, and sent directly there was no response after 3 s. **Through Caddy 2.6.2 and 2.11.4, the same request gets `HTTP/1.1 400 Bad Request` and never reaches the app** (reproduced). So this is not exploitable through the documented deployment, but it is still the only HTTP surface here that lacks the `whatsapp.py` guards. No socket timeout is set either, while `links.py:235` and `whatsapp.py:696-697` both set `settimeout(5)`.
- **Anyone can evict every live worker's session.** `local_web.py:104-105`:
  ```python
  while len(self.sessions) >= self.MAX_SESSIONS:
      self.sessions.pop(next(iter(self.sessions)))
  ```
  501 cookieless `{"answer":"/start"}` POSTs left 500 sessions, and the oldest real conversation was silently gone. With `--db` (production, `deploy/sathi-web.service:22`), each POST also writes a `session_start` row. The page itself POSTs `/start` on every load (`local_web.py:64`).
- **The UI freezes on any server error.** `local_web.py:63` does `show(await r.json());` with no `try`/`catch` and no `r.ok` check.

**Fix:**
- Copy the `whatsapp.py` `do_POST` guards (single non-negative length, max size, timeout).
- Require `isinstance(data, dict)`.
- Wrap `app.payload` and return a JSON error reply.
- Replace FIFO eviction with idle-TTL expiry.
- Rate-limit per client. Stock Caddy has no `rate_limit` directive (checked with `caddy list-modules` on 2.6.2 and 2.11.4), so either build Caddy with the third-party `caddy-ratelimit` plugin (`xcaddy`) or add a small per-IP token bucket in `local_web`. *(Corrected in round 3.)*
- Handle `!r.ok` in the page.

### M7. The rating question crashes on input the age question was already fixed for

> **Re-verification: CONFIRMED.** `flow.py:978` still reads `if not (digits.isdigit() and 1 <= int(digits) <= 10):`, while age uses `isdecimal()` with a length cap (`:532`). Fresh run: `²`, `④` (circled digit) and 5,000 digits all raise `ValueError`. The stubbed Telegram run again logs `update failed: ValueError`, drops the session and sends the "screening stopped" text. The screening was already logged as `session_complete` (`flow.py:968-969`), so the impact count survives; the feedback is lost and the worker is told to start over.

- `sathi/conversation/flow.py:977-978`
  ```python
  digits = answer.strip()
  if not (digits.isdigit() and 1 <= int(digits) <= 10):
  ```
- `flow.py:528-529` documents this exact trap for age ("isdigit() accepts superscripts like "²", which int() then rejects") and uses `isdecimal()` there, but not here.
- **Reproduced:**
  ```
  python -c "…c=Conversation({});c.state=State.RATING;c.handle('\u00b2')"
  → ValueError: invalid literal for int() with base 10: '²'
  ```
  `'1'*5000` → `ValueError: Exceeds the limit (4300 digits)`.
- **Reproduced on Telegram** by stubbing the wire and putting a chat at the rating prompt. `TelegramBot.poll_once()` logs `[telegram] update failed: ValueError`, drops the session, and sends the worker, who has just finished a screening, `कुछ गड़बड़ होने से यह जाँच रुक गई। कृपया /start भेजें और सवालों के जवाब फिर से दें।` ("something went wrong, this check stopped; send /start and answer the questions again"). Telegram's rating prompt has only a Skip button (`flow.py:244-245`), so typing a number is the expected path.
- On the web, the rating screen has 1–10 buttons and no text box (`local_web.py:81-83`), so only a crafted POST reaches this. That request then gets a 502 through Caddy, and the page freezes (see M6).

**Fix:** `if len(digits) > 2 or not digits.isdecimal() or not (1 <= int(digits) <= 10)`, plus a test next to the age fuzz in `tests/test_input_privacy.py`.

### M8. Sensitive answers are kept longer than the README says, and one host logs pack URLs

> **Re-verification: CONFIRMED.** I searched `router.py`, `whatsapp.py`, `telegram.py` and `local_web.py` for any time-based expiry (`time.time`, `monotonic`, `expir`, `idle`, `ttl`, `last_seen`):
> - Sessions are removed only at `router.py:175` (`/cancel`), `:197` (a reply that ends the session) and `:208` (abandon), plus FIFO eviction at `local_web.py:105`.
> - Documents are removed only by FIFO at `local_web.py:134`.
> - Telegram's `time.time()` calls (`:277`, `:348`) serve `/clear` only.
>
> The Caddy re-run with `enable-web.sh:27`'s block logged `uri=/document/PACKTOKEN_abc123` with `remote_ip` and the phone User-Agent on both 2.6.2 and 2.11.4.

- `README.md:288` says `The profile lives in process memory for one session and is discarded.` But `sathi/channels/router.py:95` `if fresh or key not in self.sessions:` creates sessions that are removed only on `reply.end`, `/cancel` or `abandon` (`router.py:175, 197, 208`). There is no idle expiry.
  - A worker who stops halfway leaves exact age, widow status, disability-certificate and BPL answers in RAM until restart.
  - `self.sessions`, `_lang`, `_source`, `_sent` and `_tokens` grow without bound on a 1 GB `t4g.micro`.
- Web sheets never expire. `local_web.py:76` sets `MAX_DOCUMENTS = 100` (FIFO), and `:136` does `self.documents[token] = reply.document`. The pack contains the recap, including exact age and the sensitive yes/no answers. `pack/links.py:34` gives the Telegram equivalent `TTL_SECONDS = 3600`.
- The web host's Caddy block is plain `log`:
  - `deploy/enable-web.sh:27`: `printf '\n%s {\n    log\n    reverse_proxy 127.0.0.1:8765\n}\n'`
  - The same block appears at `RUNBOOK.md:170-173`.
  - Compare the pack host at `RUNBOOK.md:133-142`, which redacts `/p/` tokens and deletes `remote_ip` and `User-Agent`.
  - **Reproduced with that exact block** on Caddy 2.6.2 (Ubuntu 24.04's `apt` version) and 2.11.4. Every request is logged with the worker's IP, User-Agent and full URI, including the sheet's bearer URL:
    ```
    [2.6.2 log]  status=404 uri=/document/PACKTOKEN_abc123 remote_ip=::1 UA=['Mozilla/5.0 (Linux; Android 11; Redmi 9A) worker-phone'] Cookie=[]
    [2.11.4 log] status=404 uri=/document/PACKTOKEN_abc123 remote_ip=::1 client_ip=::1 UA=['Mozilla/5.0 …'] Cookie=['REDACTED']
    ```
    The session cookie is redacted on both versions; the IP, User-Agent and sheet token are not. The runbook's redacting block (`RUNBOOK.md:133-142`) passes `caddy validate` on both versions, so the fix is a copy-paste. Not verified: the Caddyfile actually live on the host.

**Fix:**
- Add an idle TTL (for example 30 min) to `Router` and `LocalWeb` sessions.
- Give web documents the same 1 h TTL as `links.py`.
- Copy the redacting `log { format filter … }` block to the `sathi.avinashnegi.com` site.

### M9. The judge-facing landing page contradicts the repo

> **Re-verification: CONFIRMED for points 1 and 2; point 3 (Docker) is a FALSE POSITIVE and is withdrawn.**
> - The table under the `Ten signed schemes` heading (`index.html:341`) has **11 rows**, including `Uttarakhand widow pension | ₹18,000 per year`. `uk_widow.toml:49` is `"unconfirmed — PENDING HUMAN VERIFICATION"`.
> - The authorship line (`:444`) conflicts with **four** public files signed `claude — AUTO-RESEARCHED`, not two: `apy.toml:39`, `pmjdy.toml:15`, `pmjay_70.toml:45` and `pm_vishwakarma.toml:25`.
> - Docker: `:358` is an unlabelled technology strip that also lists `Ubuntu + systemd`. The repo ships a `Dockerfile` that CI builds (`checks.yml:39-40`). Listing it claims nothing false.

- `livesite/index.html:341` says `Ten signed schemes. Still narrow by design.` The table under it has 11 rows, including `:347` `Uttarakhand widow pension ₹18,000 per year`. That scheme is unsigned (`uk_widow.toml` `verified_by = "unconfirmed — PENDING HUMAN VERIFICATION"`) and is not even offered in the picker (`flow.py:349` lists servable schemes only).
- `livesite/index.html:444` says `I designed, wrote and deployed Yojana Sathi on my own — the rule engine, the scheme files, the Hindi copy and the server it runs on.` Public files say otherwise: `data/schemes/apy.toml:39`, `pmjdy.toml:15`, `pmjay_70.toml:45` and `pm_vishwakarma.toml:25` all have `verified_by = "claude — AUTO-RESEARCHED, PENDING HUMAN VERIFICATION"`. The project's pitch is honesty, so a judge who finds this discounts everything else.
- ~~`livesite/index.html:358` lists `Docker` in the stack. `deploy/RUNBOOK.md:306` says `No Docker`, and production uses systemd.~~ **Withdrawn in round 3 (false positive).** The strip also lists `Ubuntu + systemd`, and a CI-built Dockerfile exists.

**Fix:**
- Drop the widow row, or mark it "not served — rate unconfirmed" with no ₹.
- Describe authorship accurately: you designed, reviewed, signed and deployed it, and an AI assistant wrote code and drafts.

---

## Minor (5)

**m1. `sathi.main` crashes on Windows when output is redirected.**
`sathi/main.py:33` does `print(f"  {code}: {len(sc.stubs)} unresearched value(s) → served as UNKNOWN")` and raises `UnicodeEncodeError` under cp1252 (reproduced above). `check.py:65-69` already knows about this (`# * Hindi and rupee signs must survive redirected Windows consoles too.`) and reconfigures its streams. `main.py` and `local_web.py` do not.
**Fix:** move the `reconfigure(encoding="utf-8")` loop into a helper and call it from `main()`.

**m2. `.env.example` omits variables production needs, including the privacy-critical one.**
It lists 10 variables. The code reads 22, including `REACH_HMAC_KEY` (`sathi/metrics/events.py:262`), `PACK_BASE_URL`, `BOT_URL`, `PACK_PORT`/`PACK_BIND`, `STATS_ORIGIN`, `LLM_BASE_URL`, `LLM_MODEL`, `WHATSAPP_BIND` and `FOLLOWUP_SALT` (which the README documents).
**Fix:** add them, commented, with the RUNBOOK's warnings.

**m3. Dead code shipped as features.**
- `sathi/channels/base.py:22` `class ChannelMessage` and `:54` `class Outbox` are unused. ARCHITECTURE.md:97 calls them "the channel boundary".
- `events.py:243` `PURPOSES = frozenset({"self", "family", "helping", "testing"})` and `set_purpose()` are never called by the app, and the vocabulary differs from the roles the flow actually records (`"self"`, `"helping"`, `"tester"`, `flow.py:991`).
- `schedule_followup()` has no caller or sender.
- `audio.synthesise()`, see M2.

**Fix:** delete them, or mark them clearly as unbuilt.

**m4. Four of the ten signed schemes have no source-drift watch, and two watched pages have changed.**
`python -m sathi.sources` printed `Re-reading 7 official page(s)` (`data/sources/*.json`: eshram, pm_sym, pmjjby, pmsby, pmuy, uk_old_age, uk_widow). There are no records for the signed IGNOAPS, IGNWPS, IGNDPS and NPS_TRADERS files, so a ministry change to those amounts would go unnoticed. The same run reported `~ ESHRAM` and `~ PM_SYM`: "every value still checks out, but the page text changed since 2026-09-09".
**Fix:** add records for the four missing schemes from the primary PDFs in `docs/audit-evidence/`, and re-read the changed e-Shram FAQ and maandhan page.
(Replaces round 1's "3.11 is never tested". `check.py` now passes on 3.11.16, so that risk is gone, although CI still only runs 3.12.)

**m5. Doc sprawl, with superseded docs presented as current.**
There are 25 files under `docs/`, and many are dated snapshots (CHECKPOINT, HANDOFF, AUDIT_PLAN, AUDIT_RESUME, CHANGE_REVIEW, …). `README.md:412-413` sends judges to `docs/history/assessment/` as "a scored breakdown of where this stands". That file opens with `> **HISTORICAL SNAPSHOT — superseded.**` and self-scores 9–9.5/10.
**Fix:** move dated snapshots to `docs/archive/`, and keep README links to current docs only.

---

## Docs vs Code

| Doc file | What it says | What the code does | Fix |
|---|---|---|---|
| README.md:307 | `git clone <repo> && cd scheme-sathi` | Repo is `yojana-sathi` (`git remote -v`), so `cd scheme-sathi` fails. | `cd yojana-sathi` |
| README.md:201-203, flow.py:11-12, ARCHITECTURE.md:142-143 | "answerable entirely by tapping buttons" / "Every question works with buttons alone" / "Every question is answerable by picking a number from a list" | Age has no buttons: `flow.py:220` `State.AGE: lambda: Reply(text=self._s("questions.age"))`. `local_web.py:79`: "Age has no buttons". | Say age is typed, or add age-band buttons. |
| README.md:270-273, 335; ARCHITECTURE.md:29, 46-47, 93; assessment/README.md:45 | LLM "rephrases text a human wrote" and is used for "conversation flow" | Only `propose_occupation`, which is unreachable on live routes (M1, M2). | Remove. |
| README.md:336; ARCHITECTURE.md:30, 94; CLAUDE.md:9 | TTS audio notes / "in spoken Hindi" | `synthesise()` is never called (M2). | Remove, or build. |
| README.md:288 | profile "is discarded" | No idle expiry (M8). | Add a TTL, or reword. |
| README.md:291-292; IMPACT.md:59-60 | "aggregates covering fewer than 5 people are suppressed" | Counts sessions, not people. Headline cards and the source/purpose tables are unsuppressed (`report.py:407` passes `False`). The page itself says "Headline totals are unsuppressed". | Reword. |
| README.md:289; IMPACT.md:50 | Log holds "state, age band, occupation, income band" | No button route asks occupation, so it is NULL for button-only sessions (M1). Income is asked only when PM-SYM is screened. | Reword, or ask it. |
| README.md:360; CLAUDE.md "State" | "21 module self-checks" | `len(check.SELF_CHECK_MODULES)` = 22 | 22 |
| README.md:371-375; ARCHITECTURE.md:157 | Sweep covers "every combination of the fields any rule touches" / "~30,000 verdicts" | 8 fields swept, and 6 signed schemes never reach ELIGIBLE (M3). 1,377,810 is the current count. | Fix the test, then the text. |
| README.md:396-397 | `data/sources/` holds "44 named claims — one per value we rely on" | 44 claims across 7 JSON files. Running it printed `Re-reading 7 official page(s)`. There is no drift watch for signed IGNOAPS, IGNWPS, IGNDPS or NPS_TRADERS (m4). | Add them, or say "7 of 10 signed schemes". |
| README.md:412-413 | assessment = "where this stands" | The file is marked HISTORICAL (m5). | Relabel or drop. |
| README.md:315; `report.py:432` | `python3 -m sathi.metrics.report --out impact.html` | `--db` defaults to `./sathi.db` and ignores `DB_PATH`, unlike `main.py:96` and `links.py:197`. On the server this prints `no event database at ./sathi.db`. | Default to `os.environ.get("DB_PATH", "./sathi.db")`. |
| ARCHITECTURE.md:184 | `Profile.is_nps_member` | Field is `nps_exclusion_applies` (`profile.py:71`). | Rename. |
| ARCHITECTURE.md:209 | bilingual test holds "our three files" | 15 scheme files | Update. |
| ARCHITECTURE.md:103; IMPACT.md:9 | "the six numbers" | IMPACT's table has 7 rows, and the dashboard renders 8 cards (`report.py:314-328`). | Update. |
| ARCHITECTURE.md:226-236 | Telegram command table | Omits `/demo` (`router.py:28`). | Add. |
| CONTRIBUTING.md:13 | contributors put "your name in `verified_by`" | Only `sathi.review` may write it (README.md:387), and `tests/test_schemes.py:310` fails on an unexpected signature. | Point to `python3 -m sathi.review`. |
| CONTRIBUTING.md:11 | no aggregator sources | Signed NSAP files cite myScheme (M4). | Fix the files. |
| SUBMISSION_DRAFT.md:10 | "**Six schemes are signed off**" | 10 are signed (line 15 of the same doc agrees). | Rewrite the section. |
| SUBMISSION_DRAFT.md:112-113 | "confirmed occupation classification reduce[s] the amount a person must type" | Not reachable by any button route; only by typing a state name at the all-or-choose screen (M1). | Remove. |
| SUBMISSION_DRAFT.md:158 | link `../HACKATHON_READINESS.md` | The file does not exist. | Remove. |
| DEMO_SCRIPT.md:22-38 | Golden path: Language 1, Consent 1, State `UK`, Age 30, Occupation 1, … | After consent the flow asks all-vs-choose (`flow.py:473-474`). Typing `UK` there triggers the legacy route (`flow.py:479-483`). The run then hits the unorganised-worker and follow-up questions, and the scripted inputs never reach "Schemes already held" (ran it). | Re-script against the picker route. |
| RUNBOOK.md:162 | browser channel "not yet routed" | README.md:67 and `livesite/index.html:419` say it is live. | Update the heading. |
| RUNBOOK.md:3 | "Three scripts." | 7 scripts in `deploy/`. | Update. |
| schema.sql:69 | the reach key "never leaves this database" | `events.py:262` reads `REACH_HMAC_KEY` from the env first, and `install-on-vm.sh:80` moves it out. | Update. |
| schema.sql:31 | `channel … 'telegram' \| 'cli' \| 'whatsapp'` | Also `'web'` (`local_web.py:106`). | Add. |
| events.py:497 | purge is "The only DELETE in the project" | `events.py:334` also runs `DELETE FROM meta WHERE key = 'reach_key'`. | Reword. |
| schemes.py:326 | `premium_inr` "is never summed, only shown" | Never shown (C1). | Render it. |
| PROGRESS.md:55 | "developer testing can be excluded from pilot evidence" | It cannot (C2). | Correct. |
| review.py:8 | "Every scheme ships unsigned, so every worker gets UNKNOWN" | 10 signed | Update. |
| tests/test_flow.py:662 | "IGNWPS is deliberately unsigned during renewed source review" | IGNWPS is in `SIGNED_OFF` (`test_schemes.py:296`). | Update the comment. |
| data/schemes/{ignoaps,igndps,ignwps,nps_traders}.toml:1 | "NO HUMAN SIGN-OFF IS CLAIMED" | Signed (M4) | Update the headers. |
| livesite/index.html:341-347, 444 | "Ten signed" (lists 11); sole authorship | See M9. The `:358` Docker item was withdrawn as a false positive in round 3. | See M9 |
| HANDOFF_2026-09-14.md:27 | `livesite/assets/intro.realesrgan.mkv` | The file does not exist. | Archive the doc (m5). |

---

## What holds up

This is not padding. These are why the score is not lower.

- **The engine gate is real and tested.** `engine.evaluate` is pure. An unsigned or `TODO` file cannot produce a verdict or ₹ (`engine.py:120-140`). The build pins the signed list (`test_schemes.py:296-315`). All 22 self-checks and 15 test files pass.
- **Privacy architecture is careful.** Consent is enforced in the only writer (`events.py:149-155`). Coarse columns are whitelisted by value (`events.py:171-181`). Session ids are random. The HMAC key has been moved out of the DB. Digit runs are scrubbed from suggestions (`events.py:426`).
- **The WhatsApp webhook is properly hardened:** constant-time signature check, single non-negative Content-Length, size cap, timeout, 503 on a full queue (`whatsapp.py:726-768`).
- **No secrets in git.** `.env` was never committed, and a pattern scan of all 113 commits found only binary-PDF false positives. There are genuinely zero runtime dependencies.
- **The runtime claims held when checked independently.** The suite passes on Python 3.11.16 and 3.12.10. The Linux `docker build` passes in CI for this exact commit. All 44 recorded source claims still match the live official pages. `sathi.review` really does refuse to sign without a terminal.

---

## Top 3 fixes, in order

1. **C1: stop telling a 25-year-old they could get ₹36,000 this year.** Split the "now" and "from age 60" totals, show `premium_inr` and the contribution on the result and the sheet, and add a test. This is a few hours of work, and it is the only finding that directly misleads a worker.
2. **C2 + C3: make the submission fileable and the impact number defensible.**
   - Get the AgentFoundry answer in writing.
   - Tag sessions with a coarse pilot cohort (the `/start csc` slug) and filter `cli` and testers out of `report.py` and `/stats.json`.
   - Get a named CSC partner's workers through before 11 Oct.
3. **Truth pass on everything a judge reads**, in about a day of edits:
   - Remove the TTS and rephrasing claims (M2).
   - Fix the four signed-file headers and aggregator citations (M4).
   - Fix the landing-page table and authorship line (M9).
   - Fix the sweep and its README sentence (M3).
   - Stop printing "you did not say" for unasked questions and decide what the LLM is for (M1).
   - Re-script `DEMO_SCRIPT.md`.

Next after those: M5 (deploy ordering), M6 + M7 (web hardening, rating crash) and M8 (TTL on sessions and web documents, Caddy log redaction).

---

## Verdict after the round-4 fixes: **6.5 / 10 — still not submission-ready**

- **Engineering: about 7.5 → about 9.** Every confirmed code defect is fixed and
  tested on 3.11 and 3.12: the rating crash, the web input handling, session
  expiry, the deploy ordering, the misleading money line, the cost display, and
  the weak correctness sweep. What keeps it off 10 is only what the tests
  cannot reach: the Hindi is unreviewed, the fixes are not yet deployed, and the
  legacy typed-state route still exists.
- **Product, for the worker: about 5 → about 7.** The screen no longer overstates
  money, and it shows what each scheme costs. It is still text-only for a
  low-literacy track, and nobody outside the maintainer has used it.
- **Submission readiness: about 3 → about 4.** Now honest and measurable, but
  still blocked by zero field evidence and the unresolved AgentFoundry
  checkbox. The last 3–4 points are the pilot, AgentFoundry and the Hindi
  review, and no code change earns them.

---

## Round-1 verdict (kept for the record): **5 / 10 — not submission-ready**

- **Round 2 did not change the score.** It confirmed the good parts (3.11, the Linux build, source claims). It also turned two SUSPECTED items into confirmed ones: the Telegram rating crash ends a finished session, and the web host's Caddy logs sheet URLs with IPs. The one thing it cleared, negative Content-Length, is blocked by Caddy.
- **Round 3 (re-verification) did not change the score either.** All 3 Critical and 9 Major issues held up against the code. Four were corrected in scope or wording:
  - C2: a terminal run reaches production only with `DB_PATH` exported.
  - M1: occupation is reachable by typing a state name, just not by any button.
  - M4: the aggregator citations are in two files, not four.
  - M6: stock Caddy has no rate limiter.

  One sub-point (M9 Docker) was a false positive and has been withdrawn.
- **Engineering alone would score about 7.5.**
  - For: a disciplined deterministic core, a green 60-second suite, zero dependencies, and real privacy thinking.
  - Against: shared-flow crash bugs, an unhardened public web channel, and a deploy gate that runs after the swap.
- **As a submission, it fails on three things code cannot fix quickly:**
  - The AF checkbox is unresolved.
  - Proven impact is literally zero 16 days before the internal deploy gate, and the instrument cannot yet tell a pilot from testing.
  - The judge-facing claims overreach the code in exactly the places a careful judge checks: voice, LLM rephrasing, "every combination" testing, "ten signed" with eleven listed, and signed files saying unsigned.
- **The harshest finding is C1.** A project whose thesis is "never mislead a worker about money" shows its target user, in Hindi, a yearly ₹ figure for a pension that starts at 60 and that the worker has to pay into.

Fix C1 and the truth pass, and resolve AF. With a real pilot cohort on top of that, this is a credible 7–8 entry.
