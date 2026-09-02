# Scheme value verification worksheet

Every number and rule in `data/schemes/` transcribed on 2026-08-31, with the exact
sentence it came from and a deep link. Your job is **ticking, not researching**:
open the link, find the quoted sentence, confirm it still says that, tick.

When all boxes are ticked:

1. Replace `verified_by = "unconfirmed — PENDING HUMAN VERIFICATION"` with your own
   name and the date, in all three files.
2. Delete `test_filled_files_still_admit_they_are_unverified_by_a_human` from
   `tests/test_schemes.py`.
3. `python3 check.py` must still pass.

Until then **nobody real should be screened.** A wrong threshold sends a worker on a
wasted trip to a CSC.

---

## A. The two judgement calls — do these first

These are not transcription. Both need a decision from you, and both change who the
bot admits. Neither can be settled by re-reading the page; a CSC operator or a phone
call to the helpline settles them.

### A1. PM-SYM — is ₹15,000 in or out?
**File:** `data/schemes/pm_sym.toml`, the `income_band` criterion.
**Problem:** the same FAQ page says both. Q1: *"with monthly income of Rs.15000 or
less"*. Q2: *"less than Rs 15,000"*.
**What we did:** took the generous reading — band `10001_15000` passes, so a worker
earning exactly ₹15,000 is told they qualify.
**Risk if wrong:** someone on exactly ₹15,000 walks to a CSC and is turned away.
**Settle it:** ask a CSC operator, or the PM-SYM helpline 14434, which reading they
apply in practice.

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

- [ ] Confirmed 18–70 governs → leave as is
- [ ] Confirmed 59 cap applies via the e-Shram route → needs a route-dependent rule; tell me

### A3. e-Shram — does NPS alone disqualify?
**File:** `data/schemes/eshram.toml`, the `is_statutory_scheme_member` exclusion.
**Problem:** one profile field covers EPFO + ESIC + NPS, because PM-SYM bars all
three. e-Shram's own Q3 names only ESIC and EPFO. So a worker holding NPS but
neither of the other two is currently refused e-Shram more strictly than the FAQ
requires.
**Judgement:** rare in this population, and erring strict only under-promises. Fix is
splitting the field.

- [ ] Accept as is for now (recommended — under-promising is the safe direction)
- [ ] Split the field; tell me

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
| [ ] | exclusion: EPFO / ESIC / NPS member | Q6 "any worker who is covered under any statutory Social Security Scheme such as NPS, ESIC, EPFO … is not entitled to join" |
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
| [ ] | PMSBY first-year premium borne by the Ministry, stated in the summary | Q21 "will be enrolled under PMSBY and premium for the first year will be borne by the Ministry of Labour & Employment" |
| [ ] | exclusion: income tax payer | Q10 "There are no income criteria … However, the worker should not be an income tax payee." |
| [ ] | exclusion: ESIC / EPFO member | Q3 "… not a member of ESIC or EPFO, is called an unorganised worker." — **see A3** |
| [ ] | `documents` = Aadhaar + Aadhaar-linked mobile, biometric fallback | Q12 "Aadhaar Number; Aadhaar linked Mobile number. Note: If a worker does not have Aadhaar linked mobile number, he/ she may visit nearest CSC or SSK and register through biometric authentication." |
| [ ] | card never expires, no renewal | Q16 "The e-Shram card never expires." / Q17 "there is no need to renew" |
| [ ] | **No e-Shram prerequisite was encoded** for PMSBY or PM-SYM. Confirm the FAQ nowhere makes the UAN a precondition for them | absence check |

---

## E. Sign-off

- [ ] All boxes above ticked
- [ ] `verified_by = "Avinash Negi, <date>"` in all three files
- [ ] `test_filled_files_still_admit_they_are_unverified_by_a_human` deleted
- [ ] `python3 check.py` passes
- [ ] Only now: screen a real person

If a source has changed since 2026-08-31, do not edit the value quietly — say what
moved and the `verified_on` date has to move with it.
