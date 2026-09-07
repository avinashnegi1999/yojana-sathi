# Audit resume checkpoint

Updated 8 September 2026. Read this and `CHANGE_REVIEW.md` before resuming.

## Authorization and scope

Avinash requested a complete 20-phase technical/hackathon readiness audit in
this existing folder, including fixes, regressions, official-source research,
pilot/demo/submission materials and local logical commits. Continue autonomously.
Do not push, deploy, message others, expose secrets, fabricate evidence, sign
scheme files, or claim AgentFoundry eligibility. Preserve existing file wording
except targeted fixes. User additionally requested reviewer change notes and
checkpoint/pause before the available token budget runs out.

## Baseline and saved work

- Repository: `/run/media/avinash/Data/project Scheme Sathi`.
- Baseline `719363a`, clean main; Python 3.14.4, 18 self-checks + 8 test scripts
  passed; 73 reported functions; 972 path edges, 258 synthetic completions,
  30,618 rule comparisons. `unittest discover` ran zero and exited 5.
- Baseline Docker `yojana-sathi-audit` built successfully with Python 3.12;
  legacy-builder deprecation warning only.
- Commits: `4164ef4` baseline/reviewer notes; `8d8fbc1` intake/privacy validation;
  `83425d3` Telegram privacy/duplicate delivery.
- Further rule/source and WhatsApp fixes are in the working tree, not yet
  committed. Current full suite passed again after both agents' final changes.
  Review those diffs before committing.
- Logs/agent evidence live in `/tmp/sathi-audit-2026-09-07/`; copy essential
  results into the final report because `/tmp` is not durable across reboot.
- Secret scan: 155 reachable history blobs, common token patterns plus current
  local secrets, no matches; values never printed. Repeat before final commits.

## Delegated work

- `rules_schemes`: rules/loader/data/tests, `SCHEME_AUDIT.md`, `VERIFICATION.md`.
  Complete. `/tmp/sathi-audit-2026-09-07/rules-review.md` has evidence.
- `whatsapp`: adapter, preview, webhook tests, new safety tests. Complete.
  `/tmp/sathi-audit-2026-09-07/whatsapp-review.md` has evidence. Normal shutdown
  now drains accepted work; abrupt death still loses in-memory delivery state.
- `hackathon`: requirements/migration documents complete; currently preparing
  `PILOT_PLAN.md`, `DEMO_SCRIPT.md`, `SUBMISSION_DRAFT.md`,
  `HUMAN_REVIEW_CHECKLIST.md`. Check agent/file status rather than duplicating.

## Remaining implementation/review

1. Review and locally commit completed rule and WhatsApp changes with tests.
2. Metrics: `report.numbers()` still computes a misleading combined ₹ total;
   `value_split()`, templates and pack treat every non-insurance basis as annual
   payout. Remove combined total and restrict annual sums. Correct session versus
   people labels, future pension wording, generated versus delivered claims,
   small-cell disclosure claims; add regression checks. Do not fabricate impact.
3. Main preview currently opens the default event DB unless `--no-db` is passed.
   Make preview isolated by default and test it.
4. Shared Router retains abandoned sessions/language/raw routing keys forever;
   investigate bounded idle cleanup and clear/cancel lifecycle. Keep it minimal.
5. LLM `rephrase()` is unused, but its digit-set guard does not preserve facts.
   Consider deleting this unused unsafe helper; occupation classification is the
   only production LLM call. TTS helper is also not wired into intake; correct
   claims rather than inventing a voice feature. Check malformed LLM responses.
6. Deployment: Docker currently chowns `/app` to runtime user despite claiming
   read-only code. Installer overwrites remote secrets on every update, copies
   live code before testing, and only restarts Telegram. Fix minimal reproducible
   update path; no live deployment authorized here. Audit `.dockerignore`, CI,
   systemd and runbook including safe diagnostics (never `cat` real `.env`).
7. Update README/architecture/impact/assessment stale current-state claims;
   preserve dated build history with an addendum. Add final
   `HACKATHON_READINESS.md`, maintain `CHANGE_REVIEW.md` and this checkpoint.
8. Full final check.py, Docker final build and non-root/persistent-volume smoke,
   offline previews, HTML headless render verification, docs/links and secret
   checks, git status/diff/log. Commit logical batches without remote push.

## Evidence / gates that must survive

- Every production scheme remains UNKNOWN. Current source ambiguities include
  PMSBY age 70, e-Shram upper age, PM-SYM income/NPS/other-pension scope, and
  missing unorganised-worker conditions. Signing unchanged files is insufficient.
- Official hackathon explicitly requires AF; IDE can open existing folders, but
  organizer acceptance of prior outside-AF work is unverified. Final form lacks
  livelihood category and CFI organization contribution process is unresolved.
- Deadline 15 November 2026, exact time/timezone unverified. 11 October is an
  internal milestone, not a rule. No mandatory five-week pilot duration found.
- Historical EC2 deployment and owner-phone WhatsApp test-number screening are
  recorded in memory; this audit has not verified current host/credentials or
  production number approval. Temporary WhatsApp token expiry was noted for
  8 September; do not print its value or imply it was rotated.
- No real worker pilot, outcomes, native Hindi review, AF proof or demo recording
  established. Golden offline previews use pending production data honestly.

## Final response requested

Use the user's Completion Report structure: baseline, completed work, bugs,
tests, docs, separate technical/submission scores, P0 blockers, human actions,
AF/pilot status, created files/commits, actual final test results, and exactly
five ranked next actions. Link reviewer notes and a unified patch artifact.
