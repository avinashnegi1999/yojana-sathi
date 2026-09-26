# Scheme Sathi — progress log

Short, factual local/deployment record. Update at the end of a working day or
when Avinash asks to save progress. Do not include secrets, user data, or chat
identifiers.

## Now — 26 September 2026

- **Live:** browser ([sathi.avinashnegi.com](https://sathi.avinashnegi.com)) and Telegram ([@YojanaSathiBot](https://t.me/YojanaSathiBot)). WhatsApp is verified on Meta's test number only.
- **Schemes:** 10 signed and served. 5 drafts answer `UNKNOWN` — APY, PM Vishwakarma, PM-JAY 70+, PMJDY, Uttarakhand widow pension.
- **Checks:** `python3 check.py` — 21 module self-checks and 15 test files, all passing.
- **Not done:** native Hindi review, and the field pilot. No impact is claimed.
- **Open, in order:** the widow-pension rate from a primary source · sign the four other drafts or leave them `UNKNOWN` · Hindi review · the AgentFoundry question · the pilot ([plan](PILOT_PLAN.md)).

The log below runs oldest first. Each entry is what was true that day.

---

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
  `sathi.avinashnegi.com`.
- **Live at https://sathi.avinashnegi.com** (00:30 UTC). A record added at
  Spaceship, code synced with `install-on-vm.sh`, unit and Caddy block
  applied with `deploy/enable-web.sh`. Two snags, both now in the script:
  commands typed from PowerShell lose their inner double quotes before ssh
  sees them, and a unit that crash-looped before the code arrived trips
  systemd's start limit and needs `reset-failed`. All three units active.

## 2026-09-20

- Reliability/privacy cleanup from an external audit of `main`, each finding
  checked against the code first. Fixed: campaign source now resets on every
  `/start` (a plain start after `/start linkedin` counted as LinkedIn);
  `feedback.person` moved to its own HMAC namespace so it no longer joins to
  `reach`; feedback prompt tells the worker not to type name/phone/address
  (both languages, Hindi unreviewed); SQLite opened in WAL mode for the three
  processes sharing one file; `install-on-vm.sh` restarts every enabled
  `sathi-*` unit, and the runbook's reach-key migration stops all of them
  first. README no longer calls myScheme "an English web form" (it has Hindi)
  and says plainly that the follow-up sender is unbuilt. Two regression tests
  added. Deferred with reasons in ARCHITECTURE.md: transactional turn delivery
  and a durable WhatsApp inbox. Deployed the same day with `install-on-vm.sh`; all three
  units restarted together. The Caddy `/p/<token>` log redaction the audit
  flagged was already live on the VM - only the runbook was stale, now fixed.
- First outside review of the browser channel: "legit good, but reading
  should be minimal and fast." Walked the live flow: every question screen is
  5-20 words; the result screen was ~700 words on one page (recap, four
  schemes at a paragraph each, six ineligible reasons) with the next button
  under all of it. Each eligible scheme on screen is now name, the first
  sentence of its signed summary, and where to go; the full summary and the
  "why you qualify" stay on the sheet, where they already were. Eligible
  block 646 -> 214 words on the test profile. Nothing rewritten, no new
  Hindi.

## 2026-09-25 — fixes from AUDIT.md (not yet deployed)

Local working tree only: nothing committed, nothing deployed. `check.py` must
pass again on the VM through `install-on-vm.sh`, which now gates the staged
copy before touching `/opt/sathi`.

- **C1 money wording.** A 25-year-old matching PM-SYM was told, in Hindi, she
  could get ₹36,000 "साल भर में". The total now says each pension is paid only
  from its own starting age, and every scheme that costs money shows what the
  worker pays (from `premium_inr`, which was loaded and never shown), on the
  screen and the sheet. New Hindi strings are marked for native review.
- **C2 pilot vs testing.** Sessions now carry the arrival-link slug
  (`?start=csc`) as `events.cohort`, written only after consent, from a fixed
  list in `sathi/metrics/events.py`. The report excludes `cli` sessions by
  default and takes `--cohort`; `/stats.json` excludes `cli` too.
  **Correction to 2026-09-14 above:** the participant-type answer is stored
  without a session id, so it never could exclude developer testing from
  pilot evidence. The cohort link does that now.
- **M3 correctness sweep.** Added a per-scheme sweep over exactly the fields
  each signed scheme uses; every signed scheme must reach ELIGIBLE. It found
  the oracle had dropped NPS-Traders' PM-SYM exclusion (now added from the
  maandhan FAQ capture). UK widow's oracle is marked stale, not copied from
  the TOML — read the department overview before re-signing it.
- **M4 headers.** The four signed files that still began "NO HUMAN SIGN-OFF IS
  CLAIMED" now name the signature and the evidence PDF. Comment lines only.
  IGNOAPS/IGNWPS still cite myScheme per value; fix at the next re-sign.
- **M5 deploy.** `check.py` runs on `/tmp/sathi-stage` before the rsync.
- **M6/M8 web + sessions.** Browser channel: bounded, validated request
  bodies, socket timeout, crash → message, 30-minute idle expiry, 1-hour
  sheets, 30 new sessions per client per 10 minutes, and page-side error
  handling. Telegram/WhatsApp sessions also expire after 30 idle minutes.
  `enable-web.sh` now writes a redacting Caddy log block; **the live host
  still has the plain `log` block** — replace it per RUNBOOK.md.
- **M7** rating accepts only 1–10 as decimal digits (`²` used to crash it).
- **M1** recap lists only questions actually asked. Docs now say the model is
  not called in normal use.
- **Sources.** Visitor counters and "Last Update" stamps on maandhan.in and
  eshram.gov.in made every fetch look changed; `normalise()` drops them.
  Added a drift record for NPS-Traders. ESHRAM and PM_SYM still show `~`
  until someone re-reads those pages and re-saves the records.
- Added `.gitattributes` so `*.sh` and `*.service` are always checked out
  with LF; `core.autocrlf=true` had made `enable-web.sh` CRLF on Windows,
  and it is copied to the Linux host as-is.
- Docs brought in line with the code: README, ARCHITECTURE, IMPACT,
  CONTRIBUTING, SUBMISSION_DRAFT, DEMO_SCRIPT (re-run end to end), RUNBOOK,
  PILOT_PLAN, `.env.example`, the landing page table and authorship line.

## 2026-09-26

- **Correction to 2026-09-25 above:** those fixes were committed and deployed
  the same day. The server env gained `PACK_BASE_URL` and `BOT_URL`, and the
  live Caddy block for the browser channel now redacts its log (checked with a
  probe request).
- Browser chat and sheet redesigned in one Apple-inspired style
  (`docs/design/apple/DESIGN.md`). The browser opens in English with a हिंदी
  switch; about sixty strings trimmed in both languages. The new Hindi is not
  native-reviewed. Scheme rules, values and signatures untouched.
- Landing page (`livesite/`) rebuilt in the same style. `intro.mp4` and
  `thumbnail.png` are off the page: both are AI-generated mock-ups, and the
  video is a 10-second clip the old page captioned "two minutes". The build
  story links to the blog post instead of a separate page.
- Committed and pushed (`77c216f`, `96319ed`, `c0c5d42`). Deployed to AWS at
  05:14 UTC with `install-on-vm.sh`: server `check.py` passed, all three units
  active, 15 schemes loaded, no restarts since.
- Docs reorganised: dated records moved word for word to `docs/history/`,
  submission notes to `docs/submission/`, every link updated. README and the
  current guides rewritten short, with every fact kept.
