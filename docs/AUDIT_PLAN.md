# Submission readiness audit — 7 September 2026

Purpose: make the existing bilingual screening service safe to demonstrate and
prepare honest submission evidence without changing its deterministic design.

This implements the maintainer's 20-phase audit request. Small fixes stay in
the existing modules; there are no new dependencies, scheme signatures, live
messages, deployment changes or remote pushes.

## Baseline

- Clean `main`, commit `719363a`.
- Python 3.14.4: `python3 check.py` passes 18 module self-checks and 8 test
  scripts (73 individually reported test functions). The path walker reports
  486 paths per language, 258 completed synthetic screenings in total; the
  rule oracle checks 30,618 verdicts.
- `python3 -m unittest discover`: zero tests, exit 5 on Python 3.14. This is
  not the project's runner and provides no validation.
- `docker build -t yojana-sathi-audit .`: passes, including the full suite
  under Python 3.12. Docker warns that its legacy builder is deprecated.
- Injected transport-error messages in the test output are expected checks,
  not baseline failures. Full local logs: `/tmp/sathi-audit-2026-09-07/`.

## Work order and validation

- [x] Read repository instructions, tracked tree, current code, tests, recent
  history and historical context before selecting changes. History recovered
  from `~/.codex/memory/` (Scheme Sathi, WhatsApp, prior review, Code for India,
  and predecessor Saans), plus `docs/BUILD_LOG.md`; current code wins conflicts.
- [ ] Rules/sources: inspect every criterion, exclusion and benefit against
  authoritative sources; reproduce loader/operator defects with regression
  tests; retain UNKNOWN and human sign-off. Deliver `SCHEME_AUDIT.md` and a
  targeted update to `VERIFICATION.md`.
- [ ] Channels/core/privacy: reproduce malformed-input, session retention,
  duplicate delivery, unsafe logging and metrics defects. Patch shared code
  once; test both adapters offline, including failure paths and preview.
- [ ] Deployment/CI: verify build, persistent SQLite, non-root filesystem
  permissions, systemd syntax and documented TLS boundaries. Keep deployment
  manual; inspect tracked files and history for secrets without printing values.
- [ ] Submission: independently research current official rules and actual
  submission form; record conflicts and the AgentFoundry eligibility gate.
- [ ] Evidence: prepare human Hindi review, pilot, golden demo, submission
  draft, methodology and readiness report; correct current documentation while
  preserving dated build history.
- [ ] For each logical fix: observe regression failure, implement minimum fix,
  run relevant checks, inspect staged diff and secret scan, commit locally.
- [ ] Final: full `check.py`, container build/runtime checks, offline previews,
  rendered HTML check, documentation/link consistency, clean git status and
  separate technical/submission scores with remaining human gates.

The audit is split into independent scheme/rule, WhatsApp, and official-rules
reviews while the primary engineer reviews Telegram, shared flow, metrics and
deployment. Findings are integrated and checked together before handoff.
