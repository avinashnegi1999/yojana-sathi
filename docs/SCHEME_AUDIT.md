# Scheme source audit — 7 September 2026

Repository evidence: the three production TOML files, loader, rule engine and
boundary tests. Historical context was recovered from `docs/VERIFICATION.md`
and the Scheme Sathi memory; current sources take precedence over those notes.
This is a source comparison, **not human verification**. All three signatures
remain `unconfirmed — PENDING HUMAN VERIFICATION`; production verdicts remain
UNKNOWN, including otherwise definite failures. No reviewer has signed this audit.

MATCH means the identified source supports the field, not that the complete
scheme is approved. AMBIGUOUS and NEEDS HUMAN REVIEW must be resolved before
signing the affected file. Network failure does not establish that a source moved.

## Official evidence checked

| ID | Official source | Date / access evidence |
|---|---|---|
| E1 | [e-Shram FAQ](https://eshram.gov.in/faqs) | Retrieved 7 Sep 2026; page footer updated 7 Sep 2026; individual clauses have no effective dates |
| E2 | [NIC e-Shram description](https://www.nic.gov.in/project/%E0%A4%88-%E0%A4%B6%E0%A5%8D%E0%A4%B0%E0%A4%AE/) | Official search result checked 7 Sep 2026; 16–59 description, no established amendment date |
| P1 | [DFS PMSBY FAQ](https://www.financialservices.gov.in/pmsby) | Official indexed text checked 7 Sep 2026; page states last updated 5 Jan 2026; direct fetch failed |
| P2 | [Jan Suraksha PMSBY FAQ](https://jansuraksha.gov.in/Files/PMSBY/ENGLISH/FAQ.pdf) | Official indexed PDF text checked 7 Sep 2026; document effective date not independently established |
| P3 | [PIB PMSBY explanatory note](https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=154426&lang=1&reg=1) | Official indexed text checked 7 Sep 2026; includes termination at 70, nearest birthday |
| M1 | [PIB PM-SYM explanation](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2108082&lang=2&reg=48) | 2025 release; official text checked 7 Sep 2026; [ministry PDF mirror](https://labour.gov.in/sites/default/files/pib2108082.pdf) retrieved |
| M2 | [Lok Sabha answer AU148](https://sansad.in/getFile/loksabhaquestions/annex/185/AU148_kMKeD0.pdf?source=pqals) | Official indexed text checked 7 Sep 2026; NPS qualification differs from generic FAQ wording |

Original PMSBY [rules link](https://jansuraksha.gov.in/Files/PMSBY/English/Rules.pdf)
and PM-SYM [FAQ link](https://maandhan.in/show_content.php?lang=1&level=1&ls_id=79&lid=63&page=74)
timed out during this audit, including a retry. Existing links are retained;
the mirrors/secondary official sources above support review but do not prove
every original clause is still current. Save dated copies during human review.

## PMSBY — Pradhan Mantri Suraksha Bima Yojana

File: `data/schemes/pmsby.toml`; authority: Department of Financial Services,
Ministry of Finance. Recorded research date: 2026-08-31; human approval pending.

| Field | Repo value | Official source / clause | Status | Human action |
|---|---|---|---|---|
| Age | Inclusive 18–70 | P1 eligibility; P3 termination at 70 using nearest birthday | AMBIGUOUS | Resolve entry versus termination and integer-age precision; do not approve an automatic YES at 70 |
| Account | Bank/post office account required | P1 eligibility | MATCH | Confirm participating account type with enrolment form |
| Income / tax / occupation | No such exclusion encoded | P1 eligibility, P2 FAQ | MATCH | Check complete current rules for omissions |
| Value | ₹2,00,000, `insurance_cover` | P2 benefits table | MATCH | Conditional death/qualifying permanent disability cover; never annual income |
| Partial disability | ₹1,00,000 in summaries | P2 specific permanent-loss definitions | NEEDS HUMAN REVIEW | Generic “partial” wording must not imply all injuries qualify |
| Premium | ₹20 yearly | P1 premium | MATCH | Confirm current rate and debit consent |
| Renewal | 1 June–31 May, auto-debit | P1 enrolment | MATCH | Explain sufficient balance does not override termination conditions |
| Documents | Aadhaar, passbook, enrolment/auto-debit form | P2 administration; original rules unavailable | NEEDS HUMAN REVIEW | Distinguish KYC alternatives from mandatory Aadhaar; confirm passbook is a practical checklist item |
| Apply | `bank_branch` | P1 participating bank/post office | MATCH | Explain existing post office account route too |
| Cover restrictions | Not evaluated | P1 one account only; P3 termination | NEEDS HUMAN REVIEW | Existing cover, account closure, balance and consent remain enrolment checks; repository comment incorrectly says all appear in summary |

## PM-SYM — Pradhan Mantri Shram Yogi Maandhan

File: `data/schemes/pm_sym.toml`; authority: Ministry of Labour & Employment.
Recorded research date: 2026-08-31; human approval pending.

| Field | Repo value | Official source / clause | Status | Human action |
|---|---|---|---|---|
| Entry age | Inclusive 18–40 | M1 eligibility | MATCH | Confirm current rule |
| Income | `no_income` through `10001_15000` | M1 ≤₹15,000; original FAQ reportedly contains conflicting wording | AMBIGUOUS | New official evidence supports inclusive ceiling; record authoritative resolution before approval |
| Value | ₹36,000 `annual_payout` | M1 ₹3,000 monthly from 60; repository multiplies by 12 | MATCH | Label as future pension, conditional on scheme terms/contributions, not present annual receipts |
| Contribution | ₹55–₹200 monthly, by entry age; equal government match | M1 contribution table | MATCH | Check every endpoint; no contribution calculator exists |
| Spouse pension | 50% in summaries | M1 features | MATCH | Confirm circumstances and spouse-only scope |
| Exclusions | EPFO/ESIC, NPS, income tax | M1 exclusions; M2 says government-funded NPS | AMBIGUOUS | Clarify voluntary/private NPS versus government-funded NPS |
| Other pension | No question/rule | M1 also excludes other government pension benefits | NEEDS HUMAN REVIEW | Resolve authoritative scope, then add minimal question/rule if applicable |
| Worker status | Occupation collected, not evaluated | M1 unorganised-sector employment | NEEDS HUMAN REVIEW | A student or non-worker can satisfy current numerical rules after hypothetical sign-off; membership absence alone does not prove worker status |
| Account / documents | Aadhaar, passbook, self-certification and consent form; bank answer not evaluated | M1 documents/enrolment; original FAQ unavailable | NEEDS HUMAN REVIEW | Confirm mandatory account/mobile requirements and whether screening is for potential eligibility before obtaining documents |
| Apply / payments | CSC; monthly contributions until 60 | M1 enrolment; original FAQ | MATCH / NEEDS HUMAN REVIEW | First subscription cash is supported; reopen original contribution-duration clause |

## e-Shram registration

File: `data/schemes/eshram.toml`; authority: Ministry of Labour & Employment.
Recorded research date: 2026-08-31; human approval pending. Summary corrected
7 Sep 2026 without changing the signature or pretending a new human review.

| Field | Repo value | Official source / clause | Status | Human action |
|---|---|---|---|---|
| Age | ≥16, no upper bound | E1 Q11 versus E2 16–59 | AMBIGUOUS | Confirm new registration at 60+, separately from retaining an existing UAN |
| Income / tax | No income ceiling; tax payer excluded | E1 Q10 | MATCH | Confirm current wording |
| Membership | EPFO/ESIC excluded; NPS not excluded | E1 Q3 | MATCH | Preserve scheme-specific membership distinction |
| Worker status | No occupation rule | E1 Q3, Q27 | NEEDS HUMAN REVIEW | Resolve non-workers, “other” occupations and farmers with land before approval |
| Value / category | ₹0, `gateway` | E1 Q13/Q42 | MATCH | Registration is not proof of benefit approval |
| Premium / renewal | Free; card does not expire | E1 Q15–17 | MATCH | Explain profile updates |
| Documents | Aadhaar, linked mobile; biometric fallback | E1 Q12 | MATCH | No identifiers should be entered into this bot |
| Apply | e-Shram centre | E1 Q14/Q12: portal or assisted CSC/SSK | MATCH | Demonstrate local assisted route |
| Automatic PMSBY / first premium | Previously promised in both summaries; removed | E1 current Q13/Q42 does not substantiate that promise | MISMATCH — CORRECTED | Do not reinstate historic insurance language without current terms |

## Safety conclusions and test limits

- No age, income, benefit threshold or reviewer signature was changed by this
  audit. Existing ambiguity stays behind the whole-scheme UNKNOWN gate.
- **Signing the current files alone is insufficient.** Settle the incomplete
  conditions above and encode any necessary questions before sign-off. Do not
  infer employment from income, NPS from EPFO, or registration from insurance.
- The 30,618-case boundary sweep checks the encoded interpretation, not legal
  correctness. It currently omits occupation, other pensions, DOB precision and
  enrolment consent. Its older “official rules” wording overstates this evidence.
- Regression checks now reject nonfinite/reversed/boolean numeric thresholds,
  prevent invalid numeric inputs becoming a NO, keep unsigned value access at
  zero, and exclude cover/one-time grants from `total_value` annual payout totals.
- The 8 September engineering follow-up also rejects mismatched comparison
  types (including Python's `True == 1`) and keeps integer comparisons exact,
  avoiding float rounding and overflow. This did not change scheme thresholds.
- A definite valid exclusion may produce INELIGIBLE with another unanswered
  criterion; that is ordinary three-valued conjunction, not missing-data coercion.

## Expansion priorities — recommendations only

Stabilise and human-approve the existing three first. Ranking considers worker
relevance, reach, practical value, source clarity and implementation cost;
it is engineering judgment, not evidence that these schemes were implemented.

| Rank | Candidate | Relevance / coverage / value | Clarity / complexity / official source |
|---|---|---|---|
| 1 | PMJDY account guidance | Broad unbanked-worker reach; unlocks payments and existing application routes | Relatively clear, low complexity; [DFS scheme description](https://www.pmjdy.gov.in/scheme). Treat account access as a gateway, not an invented cash benefit |
| 2 | PM Vishwakarma | High livelihood relevance for supported artisans; narrower occupational reach | Detailed trade and household checks, medium/high complexity; [official PIB note and linked guidelines](https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=155216&id=155216&lang=2&reg=48) |
| 3 | PM-JAY referral | High potential health-cost protection for covered workers/families | Registry-backed verification needed, high complexity; [NHA beneficiary guidance](https://nha.gov.in/img/resources/Adhikar-Patra.pdf). Offer official lookup referral; never infer registry eligibility from coarse income |

No expansion files or dependencies were added.
