# Scheme Sathi — progress log

Short, factual local/deployment record. Update at the end of a working day or
when Avinash asks to save progress. Do not include secrets, user data, or chat
identifiers.

## 2026-09-14

- Read the handoff and audited scheme evidence locally. Added source copies and
  SHA-256 records under `docs/audit-evidence/`.
- Human-signed locally: IGNOAPS, IGNWPS, IGNDPS, and NPS-Traders. Total: 11
  signed schemes; 4 drafts remain safely `UNKNOWN` (APY, PM Vishwakarma,
  PM-JAY 70+, PMJDY).
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

## Next

- Manually test the live selected-scheme route in Telegram.
- Do not push to GitHub unless Avinash explicitly asks.
