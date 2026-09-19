# Scheme Sathi — progress log

Short, factual local/deployment record. Update at the end of a working day or
when Avinash asks to save progress. Do not include secrets, user data, or chat
identifiers.

## 2026-09-14

- Read the handoff and audited scheme evidence locally. Added source copies and
  SHA-256 records under `docs/audit-evidence/`.
- By the end of 14 September: 11 schemes were signed; 4 drafts remained
  safely `UNKNOWN` (APY, PM Vishwakarma, PM-JAY 70+, PMJDY). Superseded on
  15 September, below: UK widow was unsigned again, leaving 10 signed.
- Removed UP Old Age Pension completely: scheme file, intake field, tests, and
  current candidate references. Uttarakhand schemes are unchanged.
- Added PM Vishwakarma's government-service-in-family question and source-backed
  rule. It remains unsigned because other eligibility/application details need
  more review.
- Fixed NPS-Traders' PM-SYM membership exclusion: set-valued `known_schemes`
  now evaluates correctly instead of returning `UNKNOWN`.
- Reworked the exhaustive conversation test walker to retain isolated snapshots
  rather than replay equivalent paths. It now completes: 6,672 paths per
  language, including Telegram and WhatsApp rendering checks.
- Full local `check.py` passed before the selected-scheme work.
- Deployed the tested local bot code to AWS only; GitHub was not changed. AWS
  ran `check.py` successfully and Telegram service `sathi.service` is active.
- Live Telegram test exposed Telegram's 4,096-character message limit on long
  results. Added safe text splitting, keeping buttons on the final chunk.
  Re-tested locally and on AWS; the fixed Telegram service is active.

## Selected-scheme mode (deployed, 2026-09-14)

- Implemented after consent: **all verified schemes** or **choose schemes**.
  The picker exposes signed schemes only, keeps selections across pages, and
  evaluates only the chosen signed schemes.
- The intake now derives its core questions from the selected schemes instead
  of collecting irrelevant answers. The existing all-schemes route remains
  compatible with live conversations already holding a state-button tap.
- Dependency routing is dynamic: a male answer skips the widow question; an
  existing LPG/PNG connection skips the later PMUY deprivation declaration;
  `Don't know` never silently skips a possible scheme.
- The already-held-schemes screen now appears only when one of the selected
  schemes has a `known_schemes` exclusion that can change its result.
- Added selected-mode regression tests, including the reduced PMSBY route and
  both dependency skips. Full local `check.py` passed after this work.
- Deployed this feature to AWS after the server's full `check.py` passed. The
  `sathi.service` restart was verified active and polling 15 schemes. GitHub
  was not changed.
- Synced the master README with the 11 deployed signed schemes, selected-scheme
  route, current exhaustive-path coverage, and AWS deployment state.
- Repaired stale flow and Telegram self-check expectations after the picker
  launch; the full local `check.py` is green again.
- Added an optional anonymous end question: self-checking, helping someone,
  developer/reviewer testing, or skip. Its aggregate is stored without a
  session/channel identifier, so developer testing can be excluded from pilot
  evidence without creating a worker identity record.
- Added a pilot-role classification at the end of the flow and refreshed the
  live-site system diagrams to show the current intake, privacy, and verdict
  paths.
- Updated the Telegram adapter self-check for the new optional classification;
  the working tree has not been pushed to GitHub.

## 2026-09-15

- Corrected the Uttarakhand widow-pension exclusion from the department's Hindi
  pension overview: another pension now blocks that widow route. The rule has
  its own question and regression test.
- Fixed NSAP central pension values at age 80+: IGNOAPS, IGNWPS, and IGNDPS
  now use the official ₹500/month annual band. The engine supports validated
  age-based annual values instead of showing the under-80 amount to everyone.
- Withdrew the four affected signatures (UK widow, IGNOAPS, IGNWPS, IGNDPS).
  This is deliberate: changed facts require fresh human audit; each is live as
  `UNKNOWN` rather than a possibly wrong verdict. On 15 September, Avinash
  re-audited and re-signed the three NSAP files; UK widow remains unsigned.
- Repaired the Telegram recovery self-check after the optional pilot-role step;
  local and AWS `check.py` both passed, including 1,377,810 rule verdicts.
- Moved the production reach HMAC key from SQLite into root-only
  `/etc/sathi/sathi.env`, preserving prior anonymous reach hashes. Deployment
  now preserves that key and creates one safely for a new host.
- Added a `tar` deploy fallback because this Windows Git Bash installation has
  no `rsync`. Deployed successfully to AWS; `sathi.service` is active.
- Audited a generated application sheet and fixed two worker-facing mistakes:
  combined PMJJBY + PMSBY cover is now called insurance cover, not accident
  insurance, and equivalent missing-form entries are shown once.
- Ran the full local and AWS release gate again: 1,377,810 independent-rule
  verdict checks and all conversation, pack, privacy and channel checks passed.
- The online source-drift check found no changed encoded claim. e-Shram and
  PM-SYM page wording changed since the previous capture, but every tracked
  value still checks out; PMJJBY, PMSBY, PMUY and UK old-age pages are unchanged.
- Published the repair commits to GitHub and AWS. Current production state is
  10 signed schemes; five remain `UNKNOWN`: APY, PM Vishwakarma, PM-JAY 70+,
  PMJDY and UK widow pension.
- Refreshed the live-site system diagrams and added the intro video poster and
  custom thumbnail.

## 2026-09-16

- Added a JPG social-sharing preview and updated the live-site metadata to use
  it.
- No application checks or AWS deployment were recorded today; no deployment
  status change is claimed.

## 2026-09-17

- Full-project review against the core mechanism. Two worker-facing defects
  found and fixed, both with regression tests in `tests/test_flow.py`:
  - PM-SYM and NPS-Traders were both counted in the payout total, so a small
    trader eligible for both was told "about ₹72,000 a year" while the same
    screen said the two cannot be held together. Both files now share
    `exclusive_group = "maandhan_pension"`; the total is ₹36,000.
  - Since the 14 September selected-scheme redesign, the "which of these do
    you already have?" question listed only codes named in a `known_schemes`
    exclusion (PM_SYM alone), so a worker already holding PMSBY, PMJJBY or an
    e-Shram card was never asked and every match was logged as
    `scheme_newly_surfaced`. The list is now every screened scheme.
- Follow-ups are also skipped when an exclusion is already settled on earlier
  answers (an income-tax payer is no longer asked the NPS-Traders questions).
- Docs brought back in line with the data: README said "ten signed", "all
  eleven signed" and "four drafts" in three consecutive paragraphs and listed
  the UK widow pension as signed; it, `CLAUDE.md` (frozen at 31 August),
  `AGENTS.md`, `SUBMISSION_DRAFT.md`, `PILOT_PLAN.md`, `SCHEME_CANDIDATES.md`
  and the operator count in `ARCHITECTURE.md` now match the files.
  `uk_widow.toml`'s header records its 15 September withdrawal.
- Pre-ads hardening. Fuzzed 25 interleaved hostile users (6,000 turns: empty,
  5,000-char, emoji, RTL, SQL, Devanagari digits, stale buttons, every command
  at every state) through the router against a real event log: zero
  exceptions, only whitelisted bands reach the log, dashboard renders.
- One crash found and fixed: on a selected route that never asks income
  (e-Shram, PMSBY, NPS-Traders alone), answering Yes to income tax rendered
  the confirm screen with no band and raised, dropping the session. The
  button walk missed it because its visited-key ignored the selection; it now
  keys on selection too and proves it catches the reverted bug.
- `/start linkedin` (and facebook, instagram, google, ads) now counts as a
  reach source; unlisted slugs still fall to "direct". Reach and feedback
  writers take the same lock as the event writer.
- Drove every subset of the ten signed schemes through intake (1,023 picks ×
  3 tax answers × 5 ages × 3 answer styles, 46,035 sessions). One more fault:
  "Don't know" on the EPFO/ESIC question skipped the recording step, so the
  field never counted as answered and the same question came back on every
  tap. Recorded as None now, like the NPS and tax questions. All 46,035
  sessions reach the end.
- Deployed to AWS at 23:58 UTC via `deploy/install-on-vm.sh`: server `check.py`
  passed, `sathi.service` active, 15 schemes loaded (10 signed).

## Next

- Resolve the Uttarakhand widow-pension ₹1,500 primary source before re-signing it.

## 2026-09-18

- Drafted `sathi/local_web.py`, a browser channel for the same conversation:
  one page, JSON turns, loopback only, no database unless `--db` is given.
  `deploy/sathi-web.service` runs it beside the other two units. Not
  committed or deployed that day.

## 2026-09-19

- Reviewed the browser channel. Added one lock around each turn (the server
  is threaded and a double-tap was two requests inside one Conversation),
  made the session cookie server-issued only, and aligned the docstring,
  README, ARCHITECTURE and RUNBOOK, which had disagreed on whether it was a
  local experiment or a public service. It is a loopback service for Caddy
  to front; the Caddy route is written down but not applied.
- Browser page restyled to the repo's `DESIGN.md` tokens (monochrome frame,
  lime block, pill buttons), logo added, text box shown only on typed
  questions, 1–10 rating as tappable circles on web only. Target host
  `sathi.avinashnegi.com`; DNS and the Caddy block are Avinash's steps.
