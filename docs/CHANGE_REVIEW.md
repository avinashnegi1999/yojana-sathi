# Change review notes — readiness audit, 7–8 September 2026

For the next reviewer. Baseline: `719363a`. Changes are local until the owner
chooses to publish them. This file is updated as fixes are integrated; it is not
a claim of independent security certification or human scheme verification.

## Confirmed fixes

| Area / files | Before → after | Regression evidence |
|---|---|---|
| Intake: `sathi/conversation/flow.py` | Arbitrary `state:` payloads entered the profile and event log → only listed state codes accepted | `tests/test_input_privacy.py::test_prefixed_state_is_validated_before_logging` |
| Event privacy: `sathi/metrics/events.py` | Column whitelist accepted arbitrary string values → coarse dimensions also require known enum values; pre-consent event types cannot carry profile data | Two privacy tests in `test_input_privacy.py`; existing `test_privacy.py` |
| Numeric/document intake: `flow.py` | Family input stripped punctuation; huge ages raised; negative document indexes selected the last document → strict bounded decimal syntax and nonnegative indexes | Three input regressions in `test_input_privacy.py` |
| Rules/loader: `sathi/core/schemes.py`, `sathi/rules/operators.py` | Nonfinite/reversed/boolean numeric criteria accepted → malformed criteria rejected; unsigned monetary accessor returns zero | Added checks in `tests/test_schemes.py`, `tests/test_rules.py` |
| Annual totals: `sathi/rules/engine.py` | Helper could add insurance/one-time values to annual payouts → helper sums annual payouts only | `tests/test_rules.py`; worker/dashboard callers reviewed separately |
| e-Shram: `data/schemes/eshram.toml` | Summary promised automatic insurance/free first premium without current supporting FAQ evidence → unsupported promise removed in both languages | `docs/SCHEME_AUDIT.md`; all signatures remain pending |
| WhatsApp: `sathi/channels/whatsapp.py` | Unbounded request/queue handling and malformed signed payload failures → size/shape limits and backpressure; one failed recipient no longer drops siblings | `tests/test_whatsapp_safety.py`, `tests/test_whatsapp_webhook.py` |
| WhatsApp rendering/preview | Long text could be truncated and context-free old taps accepted → complete text chunks and active-question context required | `test_whatsapp_safety.py`; offline preview |

All six new intake/privacy regressions were observed failing on the prior code,
then passing after the minimal patches. WhatsApp and rule reviews supplied
their regression evidence; the integrated `python3 check.py` passed again on
resume. Final command/count/commit evidence is recorded below when complete.

## Documents and evidence

- `AUDIT_PLAN.md`: baseline, scope and validation order.
- `SCHEME_AUDIT.md` / `VERIFICATION.md`: official comparisons, unresolved
  interpretation/coverage issues, unsigned human worksheet.
- `HACKATHON_REQUIREMENTS.md` / `AGENTFOUNDRY_MIGRATION.md`: current official
  requirements, actual form fields, source conflicts, legitimate manual steps.
- Final readiness, pilot, demo, Hindi review and submission materials are being
  prepared. Do not infer completion from this working checklist.

## Review boundaries

- No production signature changed; no scheme became servable.
- No live worker interactions, deployment, remote push, organizer contact or
  external approval was performed by this audit.
- Baseline secret scan checked 155 reachable historical blobs against common
  token/key patterns and current local secret values, printing no values.
  No matches found. This is a scoped scan, not proof no secret can exist.
- Recheck accepted webhook loss on abrupt restart, failed-send recovery,
  metrics labels/suppression, session retention and deployment permissions.
- Official scheme ambiguities and missing worker-status conditions must be
  resolved before human sign-off; signing files alone is insufficient.

## Final verification and commits

Pending final integration. See `HACKATHON_READINESS.md` once generated; this
section will list the actual local commit IDs and verification results.
