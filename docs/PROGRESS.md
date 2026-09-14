# Scheme Sathi — progress log

Short, factual local/deployment record. Update at the end of a working day or
when Avinash asks to save progress. Do not include secrets, user data, or chat
identifiers.

## 2026-09-14

- Read the handoff and audited scheme evidence locally. Added source copies and
  SHA-256 records under `docs/audit-evidence/`.
- Human-signed locally: NPS-Traders and seven earlier files. Total: 10
  signed schemes; 5 files remain safely `UNKNOWN` (APY, PM Vishwakarma,
  PM-JAY 70+, PMJDY, UK widow pension).
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

## Next

- Resolve the Uttarakhand widow-pension ₹1,500 primary source before re-signing it.
