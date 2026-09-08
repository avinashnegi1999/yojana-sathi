# Seven-scheme hackathon build — 8 September 2026

Four official-source drafts extend the original PM-SYM, PMSBY and eShram rules:

| Code | Scope | Source |
|---|---|---|
| PMJJBY | New life-insurance entry, not renewal eligibility | https://financialservices.gov.in/pmjjby |
| UK_OLD_AGE | Uttarakhand old-age pension | https://socialwelfare.uk.gov.in/service/old-age-pension/ |
| UK_WIDOW | Uttarakhand widow pension | https://socialwelfare.uk.gov.in/service/widow-pension/ |
| PMUY | Ujjwala in-kind connection support | https://www.pmuy.gov.in/faq.html |

All seven files remain pending human review. `verified_on` on new drafts records the source-comparison date, not a completed approval. A populated file does not establish that every material condition has been reconciled. Existing verification instructions still apply.

## Demonstration

Send `/demo` in Telegram or WhatsApp. The command runs fixed fictional profiles against the same rule calculation used by the engine. Each reply identifies itself as a demonstration and states that review is pending. It accepts no personal profile, creates no conversation or usage-log session, never changes scheme signatures, and shows no combined benefit total. `/language` selects Hindi or English; `/demo` preserves an existing conversation and its current keyboard.

Normal `/start` screening continues to call the gated `evaluate()` entry point. It returns UNKNOWN for unsigned scheme data. Do not route a real user's profile to the private `_evaluate_rules` function used by the demonstration.

## Intake and transport

Six new optional yes/no/unknown facts remain in memory only. None is added to event-log columns. Uttarakhand pension questions are skipped for known residents of other states. The income/BPL question is asked separately: the existing income band up to ₹5,000 cannot establish a ₹4,000 threshold. The selected state is a residence self-report, not documentary proof.

PMUY asks about the official deprivation declaration rather than inferring poverty from income or occupation. The bank/account question is an initial screen; participating institutions confirm account suitability. Documents are checklist labels only: no Aadhaar, certificate or account-number uploads are requested.

Document choices have eight items per page plus page navigation and Continue, fitting WhatsApp's ten-row limit. Absolute document IDs and selections survive paging. `/schemes` uses a separate message for each source to avoid an overlong catalogue message.

## Before signing any new file

- Reconcile pension income scope, current government orders and overlap with existing pensions. Do not sum old-age and widow pensions as independently payable to the same person. The fictional examples use separate people. Future activation needs overlap handling in result totals before both routes are signed.
- The widow pension benefit is supported by the Uttarakhand budget speech paragraph 189 (https://budget.uk.gov.in/files/Budget_Speech__1.pdf); confirm the current governing order. The current departmental old-age page independently gives its amount.
- Confirm local selection and current rural/urban approval procedures. Missing local selection is explained as a step to complete, not a permanent bar.
- PMJJBY: review one-account rule, new-entry/renewal distinction, age-55 termination, 30-day lien, seasonal first-time premium and consent. Insurance is not guaranteed cash.
- PMUY: verify the current deprivation declaration, distributor e-KYC/document process and ongoing connection availability. `in_kind` with zero annual cash means goods are described without inventing a cash valuation; it does not mean the support is worthless.
- Review both languages with the intended users. Native-language review has not been claimed.

## Verification

`python check.py` runs the suite. New checks cover scheme boundaries, 1,080 combinations of added pension/PMUY facts, bilingual follow-up questions, no demo metrics, unchanged signatures, and document pagination. The broader button walk covers empty, singleton and multiple checkbox selections, rather than enumerating every possible subset; individual page reachability is asserted separately.
