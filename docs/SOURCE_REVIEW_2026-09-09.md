# Source review packet — 9 September 2026

Everything below was re-fetched from the official page on **9 September 2026**
and compared line by line against the shipped file. This is a machine
source-comparison. **It is not a human signature and does not approve any
scheme.** Nothing here ticks a box in [VERIFICATION.md](VERIFICATION.md).

Read this with [SCHEME_AUDIT.md](SCHEME_AUDIT.md) (7–8 September) and
[SCHEME_EXPANSION.md](SCHEME_EXPANSION.md) (the four new files).

**What changed in the repository as a result of this pass:** three things, all
in section 4. Two are corrections to shipped data. Nothing else was touched.

---

## 1. Confirmed against a live official page — no change needed

Each row was read off the page named, today. "Confirmed" means the shipped
value is the value on that page, not that a human has approved the file.

### PMJJBY — `data/schemes/pmjjby.toml`
Source: <https://financialservices.gov.in/pmjjby> (DFS FAQ)

| Shipped | Official wording | |
|---|---|---|
| Entry age 18–50 | "in the age group of 18 to 50 years are entitled to join" | ✅ |
| ₹2,00,000 cover | "Rs.2 lakh is payable on a subscriber's death due to any cause" | ✅ |
| ₹436/year | "The premium payable is Rs.436/- per annum per subscriber" | ✅ |
| One account only | "the person is eligible to join the scheme through one bank / Post office account only" | ✅ |
| Auto-debit consent | "deducted … through 'auto debit' facility … as per the consent given by the subscriber" | ✅ |
| 30-day lien, non-accidental death | "insurance cover shall not be available for death (other than due to accident) occurring during the first 30 days from the date of enrolment (lien period)" | ✅ |
| Cover year 1 Jun – 31 May | "The cover shall be for one-year period stretching from 1st June to 31st May" | ✅ |
| Termination at 55 (nearest birthday) | "On attaining age 55 years (age near birth day) … entry, however, will not be possible beyond the age of 50 years" | ✅ |
| First-time premium ₹436 / ₹342 / ₹228 / ₹114 | Matches the four pro-rata quarters verbatim | ✅ |

The file is an accurate transcription of that page. It remains unsigned.

### Uttarakhand old-age pension — `data/schemes/uk_old_age.toml`
Source: <https://socialwelfare.uk.gov.in/service/old-age-pension/>

| Shipped | Official wording | |
|---|---|---|
| Age ≥ 60 | "The age of the applicant should be 60 years or more" | ✅ |
| Income ≤ ₹4,000 all sources **or** BPL | "monthly income of the applicant should not exceed Rs. 4000/- from all sources or the applicant should be a BPL card holder" | ✅ |
| Gram Sabha selection required | "The applicant should have been selected in an open meeting of the Gram Sabha" | ✅ |
| ₹1,500/month (₹18,000/yr) | "A pension of ₹1,500/- per month is provided to eligible beneficiaries" | ✅ |
| Six documents | Family register/ration card, income certificate or BPL, selection proposal, certified photo, CBS passbook, Aadhaar | ✅ |
| Apply online (ssp.uk.gov.in) | "apply online through the Department's pension portal (https://ssp.uk.gov.in), the Umang mobile app, or the Apni Sarkar portal" | ✅ |

**New fact from this page, not previously recorded:** the scheme description
says the pension goes to senior citizens "(both husband and wife)". That is a
spouse question, and is *not* the old-age/widow overlap in section 4.2.

### PMUY — `data/schemes/pmuy.toml`
Source: <https://www.pmuy.gov.in/faq.html>

| Shipped | Official wording | |
|---|---|---|
| Adult woman applicant | "Adult woman from poor household" (Q1) | ✅ |
| Deprivation declaration, not income | "The deprivation declaration submitted by the applicant is the basic criteria" (Q2) | ✅ |
| No existing household LPG | "the household must not have an existing LPG connection registered in the name of any family member listed in the family composition document" (Q1) | ✅ |
| Deposit-free connection, free stove, free first refill, in-kind | Q3 and Q5(b) list exactly these; no cash entitlement is mentioned | ✅ |
| Six documents | Q6 list: KYC form + photo, applicant Aadhaar, adult members' Aadhaar, address proof, bank details, declaration | ✅ |

### PMSBY — `data/schemes/pmsby.toml`
Source: <https://financialservices.gov.in/pmsby>

Age 18–70, ₹20/year, ₹2 lakh death, and — the item the 7 September audit flagged
as needing careful wording — the ₹1 lakh figure is specifically
"Total and irrecoverable loss of sight of one eye or loss of use of one hand or
foot", which is what the shipped Hindi and English summaries now say. **This
audit row can be closed.** Termination "On attaining age 70 years (age nearer
birth day)" matches the encoded `before_nearest_birthday` handling.

### e-Shram — `data/schemes/eshram.toml`
Source: <https://eshram.gov.in/faqs>

The audit recorded the age rule as AMBIGUOUS (Q11 "16 or above" versus another
page's "16–59"). The **current** FAQ Q11 reads: *"A person aged 16 years or above
who is engaged in unorganised work may register on eShram, subject to the
applicable eligibility conditions."* There is no upper bound on that page today.
The shipped rule (≥16, no upper bound) matches the current source. Q10 confirms
no income criterion but excludes income-tax payees, as shipped.
**Two audit rows can move from AMBIGUOUS to MATCH-as-of-today**, with the caveat
that "subject to the applicable eligibility conditions" is doing unexamined work.

### PM-SYM — `data/schemes/pm_sym.toml`
Source: <https://www.labour.gov.in/en/pm-sym> and the ministry's scheme page

Audit item A1 (is ₹15,000 in or out?): the ministry's own description reads
*"whose monthly income is Rs 15,000 per month **or less**"* and *"for entry age
of 18 to 40 years with monthly income of Rs.15,000 **or less**"*. The shipped
inclusive ceiling matches. **A1 can be closed on the ministry page**, noting the
scheme FAQ's contradictory "less than" wording still exists.

---

## 2. Still unresolved — keep UNKNOWN, do not sign

These need a human, a document, or a phone call. Nothing was invented to fill
them and no default was substituted.

| # | Question | Why the code cannot settle it |
|---|---|---|
| 1 | **Uttarakhand widow pension: what is the rate?** | The department's widow page states no amount. See 4.1. |
| 2 | **Can one person draw both the old-age and the widow pension?** | Neither page says. Handled conservatively in code (4.2), but the *rule* is still unknown. |
| 3 | **PM-SYM NPS scope** | The ministry page says "NPS" plainly; a 3 Aug 2026 reply qualifies it as government-funded NPS. Excluding too broadly wrongly turns a worker away. |
| 4 | **PM-SYM worker status** | A non-worker can satisfy the numeric rules. The occupation answer is collected but not evaluated. |
| 5 | **PMSBY at exactly 70** | "18 to 70 years are entitled to join" versus "terminates on attaining age 70 (nearer birthday)". The source genuinely conflicts. |
| 6 | **PMSBY via e-Shram at 18–59** | Only ever seen in a commented-out block on the e-Shram FAQ. Not encoded. Worth one CSC question. |
| 7 | **e-Shram "applicable eligibility conditions"** | Q11's qualifier is undefined on the page. Farmers/landholders remain unresolved (audit row). |
| 8 | **PMJJBY renewal path** | The file screens **new entry** only. Someone aged 51–55 renewing an existing policy is a different case the bot does not model. |
| 9 | **PMUY current enrolment availability** | Q6 lists documents; whether new connections are open in a given district is a distributor question. |
| 10 | **Uttarakhand local selection procedure** | Encoded as a question and explained as a step to complete, never as a permanent refusal. Current rural/urban procedure unconfirmed. |

---

## 3. Sources that could not be retrieved

Recorded so nobody repeats the attempt and concludes something is missing.

| Source | Result on 2026-09-09 |
|---|---|
| `budget.uk.gov.in/files/Budget_Speech__1.pdf` | **HTTP 404.** This was the citation for the widow pension amount. |
| `socialwelfare.uk.gov.in/files/GO_1.pdf` | HTTP 404 |
| Rate-increase GO 40/XVII-2/22-19(05) 2019-T.C, 21/04/2021 | Retrieved, but a **scanned image PDF** — no extractable text. Needs a human to open and read. |
| `ssp.uk.gov.in` | TLS handshake refused (unsafe legacy renegotiation). Reachable from an ordinary browser. |
| `myscheme.gov.in/schemes/uwps` | Browser-only single-page app; returns no content to a fetcher. |
| `web.umang.gov.in` scheme detail | Same. |

---

## 4. What was changed in the repository today

### 4.1 The widow pension amount was withdrawn to `"TODO"`

**File:** `data/schemes/uk_widow.toml`.
**Was:** `annual_value_inr = 18000`, with both summaries promising "₹1,500
monthly pension", cited to budget speech paragraph 189.
**Now:** `annual_value_inr = "TODO"`, and neither summary quotes a figure.

**Why.** The citation URL is now a 404, the department's widow page states no
rate, the governing rate GO is a scan, and every other official route is
browser-only. A ₹ figure whose source nobody can open is exactly what
`"TODO"` exists for — rule 3 in `CLAUDE.md`. The old-age page *does* state
₹1,500 on its own, which is why that file was left alone.

This is a **withdrawal, not a discovery that the number is wrong.** ₹1,500 may
well be correct. To restore it: open the 21/04/2021 GO from
<https://socialwelfare.uk.gov.in/document-category/government-orders-pension/>,
read the widow rate, put the GO number in the file's header comment, and delete
the `UK_WIDOW` line from `KNOWN_STUBS` in `tests/test_schemes.py`.

Practical effect today: none for a worker — the scheme was already served as
UNKNOWN because it is unsigned. The effect is on *you*: the startup report and
`/schemes` now say the file is unfinished, instead of showing a researched-looking
number.

### 4.2 The two Uttarakhand pensions can no longer be added together

**Files:** `uk_old_age.toml`, `uk_widow.toml` (new `exclusive_group =
"uk_state_pension"` in `[benefit]`), `sathi/core/schemes.py`,
`sathi/rules/engine.py`.

A 62-year-old widow satisfies **both** pension files. Before this change, the
result screen and the printed pack would each have added ₹18,000 + ₹18,000 and
told her ₹36,000 a year. The state pays one pension.

`engine.total_value()` now collapses each exclusive group to its largest member,
counted once. Schemes with no group are unaffected, so nothing else changed.

This is the same class of bug as the insurance cover that used to be added to a
pension, and it is now covered by
`tests/test_expansion.py::test_the_two_state_pensions_are_never_counted_as_two_payments`,
which drives a real 65-year-old widow profile through the engine and asserts the
worker-facing screen never contains "36,000" in either language.

**The grouping is a safe default, not a researched rule.** It assumes at most one
pension. If the department in fact pays both, the group must be removed — that is
open question 2 in section 2.

### 4.3 Both totals now come from one function

`sathi/render/templates.py` and `sathi/pack/pack.py` each summed the payout and
cover figures with their own copy of the same two lines. Both now call
`engine.value_totals()`. A worker cannot be shown one number on screen and
handed a different one on paper.

### 4.4 Test-fixture consequence, and a coverage floor

Four suites sign the real scheme files so the eligible half of the conversation
is reachable. A file with a `"TODO"` is unservable for the same reason an
unsigned one is, so those fixtures now clear stubs as well as the signature.

This was caught the hard way. The first green run after 4.1 had quietly dropped
from **2,109 walked paths to 669**, and from 216 document screens to 63, because
`UK_WIDOW`'s seven documents fell out of the checklist. The suite still passed.
`tests/test_all_paths.py` now asserts a floor of 2,000 paths per language, so a
data change cannot silently shrink the walk again.

`tests/test_schemes.py` no longer asserts "no scheme file has any stub". It
asserts "no scheme file has a stub that is not on `KNOWN_STUBS`, with a written
reason" — and a second test fails if a `KNOWN_STUBS` entry stops being a stub, so
the list cannot rot. The gate was not removed.

---

## 5. What is needed from Avinash

Nothing in this document signs anything. In priority order:

1. **Open the 21/04/2021 rate GO and read the widow pension rate.** It is a
   scanned PDF; a person has to look at it. This is the single blocking fact for
   `uk_widow.toml`.
2. **Ask whether one person can hold both state pensions** — Gram Panchayat, the
   district social welfare office, or the SSP helpline. Answer decides whether
   `exclusive_group` stays.
3. **Decide PM-SYM's NPS scope** (section 2, row 3). Currently the broader
   exclusion; a wrong exclusion turns away someone eligible.
4. Then work through [VERIFICATION.md](VERIFICATION.md) scheme by scheme. The
   confirmations in section 1 above should make PMJJBY, PMUY and the old-age
   pension quick, because the wording is quoted next to the shipped value.

Until a named human replaces `verified_by`, every scheme is served as UNKNOWN and
nobody real should be screened. That is unchanged by this document.
