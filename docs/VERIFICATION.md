# Scheme value verification worksheet


**Implementation update, 8 September:** read the new implementation section of
[SCHEME_AUDIT.md](SCHEME_AUDIT.md) before the historical rows below. Worker
status is now asked separately; NPS type is classified with unresolved types
remaining UNKNOWN; PMSBY's nearest-birthday termination condition is encoded.
Review these new conditions as well as the existing source values. The previous
NPS field `is_nps_member` is replaced by `nps_exclusion_applies`; a true answer
now specifically represents reported central-government contributions.
No historical checkbox is automatically approved by this implementation.

Every number and rule in `data/schemes/` transcribed on 2026-08-31, with the exact
sentence it came from and a deep link. Open the link, find the clause, compare
the file and record MATCH/MISMATCH. Read the [7 September source audit](SCHEME_AUDIT.md)
first: missing conditions and conflicting sources must be resolved before ticking.
This worksheet is not itself a human signature.

**8 September update:** see the follow-up in [SCHEME_AUDIT.md](SCHEME_AUDIT.md).
PMSBY disability/renewal wording has been tightened from a directly retrieved
DFS FAQ. A 3 August 2026 ministry reply supports the inclusive PM-SYM income
ceiling but qualifies the NPS exclusion. No human boxes have been ticked and
no scheme is approved. Review missing conditions in A4 as well as existing rows.

When all boxes are ticked:

1. Only for a completely approved file, replace
   `verified_by = "unconfirmed — PENDING HUMAN VERIFICATION"` with the actual
   reviewer's name and date; set `verified_on` to that review date.
2. Update the two production-state tests in `tests/test_schemes.py`
   (`test_filled_files_still_admit_they_are_unverified_by_a_human` and
   `test_no_shipped_scheme_is_servable_while_sign_off_is_pending`) to reflect
   precisely which files were approved. Keep the synthetic unsigned/stub gate
   tests permanently; do not delete the safety invariant to obtain a green build.
3. `python3 check.py` must still pass.

Until then **nobody real should be screened.** A wrong threshold sends a worker on a
wasted trip to a CSC.

---

## A. Source ambiguities — do these first

These affect who the bot admits. Seek current official written clarification;
record any helpline/CSC response as operational evidence, not a replacement for
the governing source. Keep the file unsigned while material ambiguity remains.

### A1. PM-SYM — is ₹15,000 in or out?
**File:** `data/schemes/pm_sym.toml`, the `income_band` criterion.
**Problem:** the same FAQ page says both. Q1: *"with monthly income of Rs.15000 or
less"*. Q2: *"less than Rs 15,000"*.
**Encoded interpretation:** band `10001_15000` passes in signed test fixtures.
Production remains UNKNOWN because the file is unsigned.
**Risk if wrong:** someone on exactly ₹15,000 walks to a CSC and is turned away.
**Settle it:** ask a CSC operator, or the PM-SYM helpline 14434, which reading they
apply in practice.

**7 September 2026 evidence:** [PIB's PM-SYM explanation](https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2108082&lang=2&reg=48)
supports an inclusive ₹15,000 ceiling. Review this against the governing terms;
the older FAQ timed out during this audit. No approval is recorded here.

**Re-checked 2026-09-03:** both readings are still live on the page, in these words —
*"15000 or less."* and *"with monthly income less than Rs 15,000/-."* The contradiction
is the source's, not a transcription slip, so only the helpline settles it.

- [ ] Confirmed ₹15,000 inclusive → leave as is
- [ ] Confirmed ₹15,000 exclusive → the band must be split; tell me and I'll do it

### A2. PMSBY — is the age cap 70, or 59 when you come via e-Shram?
**File:** `data/schemes/pmsby.toml`, the `age` criterion.
**Problem:** PMSBY's own rules say 18–70. The e-Shram FAQ says *"the person should be
between 18-59 years to be eligible for PMSBY through eSHRAM registration"* — but that
text sits in a commented-out block on their page, which is why it was not encoded.
**What we did:** used PMSBY's own rules, 18–70.
**Risk if wrong:** a 65-year-old registering through e-Shram is told they get cover
they will not get.
**Settle it:** ask a CSC operator what happens to a 65-year-old enrolling via e-Shram.

**Re-checked 2026-09-03, page re-fetched.** Q40 is *still* inside an unclosed HTML
comment ending `//-->`, so no visitor sees it — the original note holds, and this
cannot be settled by reading the page. Two separate facts got conflated and are
worth keeping apart:

- **e-Shram registration** has no upper age bound in the visible FAQ. *"A person
  aged 16 years or above … may register on eShram"*, and separately *"What action is
  required … after attaining the age of 60 years? No action is required merely
  because the worker turns 60."* The file's `age >= 16` matches what the page shows.
- **PMSBY via the e-Shram route** is what the hidden Q40 caps at 59. That is a PMSBY
  question, not an e-Shram one.

**7 September 2026 correction:** the visible e-Shram FAQ supports 16+, but
[NIC's e-Shram page](https://www.nic.gov.in/project/%E0%A4%88-%E0%A4%B6%E0%A5%8D%E0%A4%B0%E0%A4%AE/)
still describes 16–59. Keeping a UAN after 60 does not independently prove new
registration is allowed after 60. Neither result is human-verified. The obsolete
automatic-PMSBY/first-premium promise was removed from the e-Shram summaries;
linked insurance must be checked separately.

- [ ] Confirmed 18–70 governs → leave as is
- [ ] Confirmed 59 cap applies via the e-Shram route → needs a route-dependent rule; tell me
- [ ] Resolve e-Shram new-registration age separately from PMSBY
- [ ] Resolve PMSBY entry 18–70 versus cover terminating at 70 (nearest birthday),
  documented in [PIB's PMSBY note](https://www.pib.gov.in/PressNoteDetails.aspx?ModuleId=3&NoteId=154426&lang=1&reg=1)

### A3. e-Shram — does NPS alone disqualify?  ✅ SETTLED 2026-09-03 — field split
**File:** `data/schemes/eshram.toml`, now the `is_epfo_or_esic_member` exclusion.
**Problem was:** one profile field covered EPFO + ESIC + NPS, because PM-SYM bars
all three. e-Shram's own Q3 names only ESIC and EPFO, so a worker holding NPS and
neither of the other two was refused e-Shram more strictly than the FAQ requires.

**This worksheet previously recommended accepting it**, on the grounds that
erring strict only under-promises. That recommendation was wrong and has been
reversed. e-Shram is the gateway through which the other schemes are delivered,
so a wrong NO there is a missed entitlement, not a cautious default — and
"stricter than the source says" is a correctness failure whichever direction it
points.

**Resolved by splitting** into `is_epfo_or_esic_member` and `is_nps_member` —
two fields rather than three, because no scheme distinguishes EPFO from ESIC and
each extra field costs the worker another question. PM-SYM excludes on either;
e-Shram excludes on the first only. `tests/test_rule_boundaries.py` carries
`test_nps_alone_disqualifies_pm_sym_but_not_eshram`, which fails if the two are
ever conflated again.

**Nothing left to decide here** — but the two new exclusions still need their
source sentences ticked in sections C and D below.

### A4. Conditions not represented by current questions

- [ ] Confirm unorganised-worker status for PM-SYM/e-Shram. Occupation is collected
  but not used by these rules; no-work/student answers are not proof of employment.
- [ ] Resolve whether PM-SYM excludes every NPS subscription or government-funded
  NPS specifically, using the [Lok Sabha answer](https://sansad.in/getFile/loksabhaquestions/annex/185/AU148_kMKeD0.pdf?source=pqals).
- [ ] Resolve the other-government-pension exclusion in the newer PIB explanation.
- [ ] Confirm account/mobile/consent prerequisites and which are screening
  conditions versus application preparation steps.
- [ ] Have an engineer encode any missing conditions and regression cases before
  signing. Do not approve an incomplete rule set merely because each existing row matches.

---

## B. PMSBY — `data/schemes/pmsby.toml`

Source, all rows: **jansuraksha.gov.in PMSBY rules PDF (w.e.f. 1.6.2022)**
<https://jansuraksha.gov.in/Files/PMSBY/English/Rules.pdf>

| ✓ | Value in file | Quoted sentence to find |
|---|---|---|
| [ ] | age `between [18, 70]` | "aged between 18 years (completed) and 70 years (age nearer birthday)" |
| [ ] | `has_bank_account = true` | "All individual bank/ Post office account holders … will be entitled to join" |
| [ ] | `annual_value_inr = 200000`, basis `insurance_cover` | "Table of Benefits … a Death — Rs. 2 Lakh" |
| [ ] | ₹1 lakh partial figure, stated in `summary_hi` / `summary_en` | the same benefits table, partial disability row |
| [ ] | `premium_inr = 20` | "Premium: Rs. 20/- per annum per member." |
| [ ] | `renewal` = 1 June – 31 May, auto-debit | "one-year cover … 1st June to 31st May … option to join / pay by auto-debit … required to be given by 31st May of every year" |
| [ ] | `documents` = Aadhaar, bank passbook, enrolment + auto-debit form | "Enrolment form / Auto-debit authorization in the prescribed proforma…" + "Aadhar would be the primary KYC" |
| [ ] | **No income bar and no income-tax bar exist.** Confirm the PDF really contains neither — this is a deliberate absence, not an omission | search the PDF for "income" and "tax" and find nothing that bars anyone |
| [ ] | `where_to_apply = "bank_branch"` — post office also enrols but the field takes one value | judgement, not a quote; confirm you are happy sending people to the bank |

---

## C. PM-SYM — `data/schemes/pm_sym.toml`

Source, all rows: **maandhan.in FAQs (last updated 13 Feb 2023)** and the
**Contribution Chart (14 Feb 2023)**
<https://maandhan.in/show_content.php?lang=1&level=1&ls_id=79&lid=63&page=74>

| ✓ | Value in file | Quoted sentence to find |
|---|---|---|
| [ ] | age `between [18, 40]` | "voluntary and contributory Pension Scheme for Unorganized Workers for entry age of 18 to 40 years" |
| [ ] | income bands ≤ ₹15,000 pass | Q1 "with monthly income of Rs.15000 or less" — **see A1 first** |
| [ ] | `no_income` band included | judgement: zero is less than ₹15,000. Confirm you agree a worker with no income should be offered this |
| [ ] | `annual_value_inr = 36000`, basis `annual_payout` | "minimum pension is of Rs. 3000/- per month … shall start on attaining the age of 60 years" (×12) |
| [ ] | 50% family pension in the summary | the FAQ's spouse/family pension answer |
| [ ] | `premium_inr` range ₹55–₹200/month by entry age | Contribution Chart: ₹55 at 18, ₹200 at 40 |
| [ ] | Government matches 1:1, stated in the summary | "the Central Government shall give equal matching contribution" |
| [ ] | exclusion: `is_epfo_or_esic_member` | Q6 "any worker who is covered under any statutory Social Security Scheme such as NPS, ESIC, EPFO … is not entitled to join" |
| [ ] | exclusion: `is_nps_member` — a **second** block, same sentence | Q6, same sentence: NPS is the third scheme it names. Both blocks must exist; either alone disqualifies |
| [ ] | exclusion: income tax payer | Q6 "… and an income tax payee is not entitled to join the scheme" |
| [ ] | `documents` = Aadhaar, passbook, self-certified + auto-debit form | Q14 "The beneficiary has to provide Aadhar card, savings bank passbook and a Self-Certified form along with consent form for auto-debit facility." |
| [ ] | no separate age or income proof needed | Q7 "No separate proof of age or the income has to be given." |
| [ ] | `where_to_apply = "csc"`, first payment in cash | Q8 "First contribution is to be paid in cash at Common Service Centre." |
| [ ] | `renewal` = nothing to renew, pay monthly to 60 | Q15 "the beneficiary has to pay the prescribed monthly contribution till the age of 60 years" |

---

## D. e-Shram — `data/schemes/eshram.toml`

Source, all rows: **eshram.gov.in FAQ** <https://eshram.gov.in/faqs>

| ✓ | Value in file | Quoted sentence to find |
|---|---|---|
| [ ] | age `gte 16`, **no upper bound** | "A person aged 16 years or above who is engaged in unorganised work may register" + "No action is required merely because the worker turns 60" |
| [ ] | `annual_value_inr = 0`, basis `gateway` — this zero is correct, not a stub | Q13 "a centralised database of unorganised workers … to facilitate delivery of various social security benefits" — confirm the FAQ promises no payout of its own |
| [ ] | `premium_inr = 0` | Q15 "Registration on e-Shram portal is free. Workers are not required to pay any charges to any registering entity." |
| [ ] | No automatic PMSBY or free-first-premium promise | Current Q13/Q42 describes registration and access to benefits; the unsupported older summary was removed on 7 Sep 2026 |
| [ ] | exclusion: income tax payer | Q10 "There are no income criteria … However, the worker should not be an income tax payee." |
| [ ] | exclusion: `is_epfo_or_esic_member` | Q3 "… not a member of ESIC or EPFO, is called an unorganised worker." |
| [ ] | **no NPS exclusion here** — confirm Q3 and the rest of the FAQ nowhere names NPS | absence check. A3 settled 2026-09-03: NPS alone must NOT bar e-Shram. Re-adding it needs a source sentence that names NPS |
| [ ] | `documents` = Aadhaar + Aadhaar-linked mobile, biometric fallback | Q12 "Aadhaar Number; Aadhaar linked Mobile number. Note: If a worker does not have Aadhaar linked mobile number, he/ she may visit nearest CSC or SSK and register through biometric authentication." |
| [ ] | card never expires, no renewal | Q16 "The e-Shram card never expires." / Q17 "there is no need to renew" |
| [ ] | **No e-Shram prerequisite was encoded** for PMSBY or PM-SYM. Confirm the FAQ nowhere makes the UAN a precondition for them | absence check |

---

## E. Sign-off

- [ ] All boxes above ticked
- [ ] `verified_by = "Avinash Negi, <date>"` in all three files
- [ ] Both production-state tests updated for the approved files; synthetic gate tests retained
- [ ] `python3 check.py` passes
- [ ] Only now: screen a real person

If a source has changed since 2026-08-31, do not edit the value quietly — say what
moved and the `verified_on` date has to move with it.

## F. Reviewer record — copy one row per value or condition

Leave blank until a real person completes the comparison. A screenshot or saved
official PDF should contain no worker identifiers. Record the document version,
page/table or FAQ number so another reviewer can reproduce the decision.

| Scheme / field | Source URL / clause / source date | Repo value | MATCH / MISMATCH / AMBIGUOUS | Correction / unresolved question | Reviewer's name | Review date | Approved |
|---|---|---|---|---|---|---|---|
| | | | | | | | [ ] |

For each scheme: reviewer ______; date ______; reviewed file/commit ______;
all material ambiguities resolved [ ]; required rule changes tested [ ]; approve [ ].
