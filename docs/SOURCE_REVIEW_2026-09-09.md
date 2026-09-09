# Source review packet — 9 September 2026

Everything below was re-fetched from the official page on **9 September 2026**
and compared line by line against the shipped file. This is a machine
source-comparison. **It is not a human signature and does not approve any
scheme.** Nothing here ticks a box in [VERIFICATION.md](VERIFICATION.md).

Read this with [SCHEME_AUDIT.md](SCHEME_AUDIT.md) (7–8 September) and
[SCHEME_EXPANSION.md](SCHEME_EXPANSION.md) (the four new files).

**This document covers two passes on the same day.** The first used a plain
fetcher and could not read three official sources — a single-page app and two
hosts with legacy TLS. The second used a browser and got into them, which
**reversed one of the first pass's conclusions and answered two open questions**.
Where they differ the second pass wins, and the first is left visible rather than
deleted, because the reasoning is the point.

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
| ~~1~~ | ~~Uttarakhand widow pension: what is the rate?~~ | **ANSWERED in the second pass** — ₹1,500/month, stated on myScheme. See 4.1. |
| ~~2~~ | ~~Can one person draw both the old-age and the widow pension?~~ | **ANSWERED** — myScheme states on *both* scheme pages that the applicant must not already be receiving another pension. Now encoded as a criterion, not just a totals rule. See 4.2. |
| 2b | **Whose income counts for the ₹4,000 line?** | New conflict found in the second pass: the department page says the **applicant's**, myScheme says the **family's**. The question now asks the stricter family reading and the fail text says the sources differ. |
| 3 | **PM-SYM NPS scope** | Still open, but better characterised. The maandhan FAQ Q2 and Q6 both frame it as "covered under any statutory Social Security Scheme such as NPS, ESIC, EPFO" — NPS named plainly, no qualifier. A 3 Aug 2026 ministry reply says government-funded NPS. The code excludes only central-government NPS and leaves other NPS answers UNKNOWN, which is the right treatment of a conflict: it neither invents a NO nor quietly admits someone. **No change made.** |
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
| `budget.uk.gov.in/files/Budget_Speech__1.pdf` | **HTTP 404.** This was the original citation for the widow pension amount. |
| `myscheme.gov.in/schemes/uwps` and `/oap` | **Read successfully in the second pass, with a browser.** Source of the widow rate and the no-other-pension rule. |
| `uk.gov.in/.../file-04-12-2023-06-02-23.pdf` — the state guidelines page 16 that myScheme itself cites | Legacy TLS; downloaded from the Linux host using `OP_LEGACY_SERVER_CONNECT`. It is **320 MB** and almost certainly a scan. Not read. A human should check page 16. |
| `socialwelfare.uk.gov.in/files/GO_1.pdf` | HTTP 404 |
| Rate-increase GO 40/XVII-2/22-19(05) 2019-T.C, 21/04/2021 | Retrieved, but a **scanned image PDF** — no extractable text. Needs a human to open and read. |
| `ssp.uk.gov.in` | TLS handshake refused (unsafe legacy renegotiation). Reachable from an ordinary browser. |
| `myscheme.gov.in/schemes/uwps` | Browser-only single-page app; returns no content to a fetcher. |
| `web.umang.gov.in` scheme detail | Same. |

---

## 4. What was changed in the repository today

### 4.1 The widow pension amount: withdrawn, then restored from a better source

**File:** `data/schemes/uk_widow.toml`.

**First pass.** The shipped ₹1,500/month was cited to budget speech paragraph
189. That URL now returns **404**, and the department's widow page — unlike the
old-age page — states no rate at all. So the value was withdrawn to `"TODO"`,
which is what rule 3 in `CLAUDE.md` is for.

**Second pass.** The reason the earlier attempts failed was tooling, not
absence: myScheme is a single-page app that returns nothing to a fetcher.
Opened in a browser, <https://www.myscheme.gov.in/schemes/uwps> says plainly:

> "A pension of ₹1,500/- per month is provided to eligible beneficiaries."

myScheme is the Government of India scheme portal, run by Digital India
Corporation under MeitY, and it cites the state's own guidelines. **So the value
is restored as `18000`, now with a citation anyone can open**, and the file's
header records the whole story — including that myScheme's underlying citation
(state guidelines page 16) is a 320 MB scan nobody has read.

`KNOWN_STUBS` in `tests/test_schemes.py` is empty again.

### 4.2 "Not already receiving another pension" is a rule, not just arithmetic

**Files:** both pension TOMLs, `sathi/core/profile.py`, `sathi/conversation/flow.py`,
both string files.

The first pass reasoned that a 62-year-old widow satisfies both pension files,
that the state surely pays one pension, and added `exclusive_group` so the two
could never be **added together** in a ₹ total. That fixed the arithmetic on an
assumption.

The second pass found the actual rule, stated on **both** myScheme scheme pages:

> "The applicant must not be receiving any other pension." (old-age)
> "The widow must not be receiving any other pension benefits." (widow)

That is an **eligibility bar**, which is stronger and more useful than a totals
adjustment: someone already drawing a pension should be told so before they
travel, not quietly counted once. It is now a real criterion on both files,
backed by a new session-only profile field `receives_other_pension` and one
extra follow-up question in both languages.

`exclusive_group` stays as well. The criterion stops an already-pensioned person
being told yes; the group stops the totals double-counting someone who currently
draws neither and qualifies for both routes. They cover different cases.

**Note what the department's own pages do NOT say.** Neither
`socialwelfare.uk.gov.in` service page mentions this condition. It is recorded
here from the national portal and should be confirmed at the office before
sign-off — which is why both files remain unsigned.

**Also found, and unresolved:** myScheme says the ₹4,000 line is on the
**family's** monthly income; the department page says the **applicant's**. The
question now asks the stricter family reading, and the failure message says in
both languages that the sources differ and to ask at the office if you are near
the line.

### 4.3 Both totals now come from one function

`sathi/render/templates.py` and `sathi/pack/pack.py` each summed the payout and
cover figures with their own copy of the same two lines. Both now call
`engine.value_totals()`. A worker cannot be shown one number on screen and
handed a different one on paper.

### 4.4 Test-fixture consequence, and two coverage guards

Four suites sign the real scheme files so the eligible half of the conversation
is reachable. A file with a `"TODO"` is unservable for the same reason an
unsigned one is, so those fixtures now clear stubs as well as the signature.

This was caught the hard way. The first green run after 4.1 had quietly dropped
from **2,109 walked paths to 669**, and from 216 document screens to 63, because
`UK_WIDOW`'s seven documents fell out of the checklist. The suite still passed.
`tests/test_all_paths.py` now asserts a path floor, so a data change cannot
silently shrink the walk unnoticed.

The floor then fired a **second** time, for an honest reason, and that is worth
recording. The button walk keys on the screen, so every answer to a follow-up
question collapses to one key and only one set of answers is ever carried
through to the document checklist — whichever the search reaches first. Adding
the new pension question moved that branch to one where both pensions are
INELIGIBLE, so their documents legitimately vanished and the count fell to 672.

A path count was the wrong thing to assert. The real guarantee is now stated
directly, in `test_every_document_of_every_scheme_is_reachable`: it drives two
deliberately-answered eligible profiles — a 30-year-old and a 65-year-old,
because no single worker can qualify for all seven (PM-SYM stops at 40, PMJJBY
at 50, the old-age pension starts at 60) — and asserts their combined document
checklists contain every document of every scheme, in both languages. The loose
path floor stays as a coarse tripwire.

`tests/test_schemes.py` no longer asserts "no scheme file has any stub". It
asserts "no scheme file has a stub that is not on `KNOWN_STUBS`, with a written
reason" — and a second test fails if a `KNOWN_STUBS` entry stops being a stub, so
the list cannot rot. The gate was not removed.

---

## 5. What is needed from Avinash

Nothing in this document signs anything. In priority order:

1. **Confirm the no-other-pension bar at the office.** It comes from myScheme,
   not from the department's own service pages, and it now decides verdicts for
   both pensions. This is the most consequential unconfirmed thing in the repo.
2. **Settle whose income the ₹4,000 line means** — applicant or family. The two
   official sources disagree and the code currently uses the stricter reading.
3. **Confirm the widow rate** against the state guidelines page 16 or the
   21/04/2021 rate GO. Both are scans; a person has to look. myScheme's ₹1,500
   is good enough to ship as unsigned data, not to sign.
4. **Decide PM-SYM's NPS scope** (section 2, row 3). The code's current handling
   is defensible; a decision would remove an UNKNOWN.
5. Then work through [VERIFICATION.md](VERIFICATION.md) scheme by scheme. The
   confirmations in section 1 above should make PMJJBY, PMUY and the old-age
   pension quick, because the wording is quoted next to the shipped value.

Until a named human replaces `verified_by`, every scheme is served as UNKNOWN and
nobody real should be screened. That is unchanged by this document.

---

## 6. Independent re-verification, 9 September (third pass)

Requested by Avinash: re-check everything rather than trust the notes above.
Every source below was **fetched again from scratch** and each encoded value
matched against the live page text by pattern, not by memory. Nothing was
carried over from the earlier passes.

| Scheme | Checks | Result |
|---|---|---|
| PMJJBY | 14 | **14/14 matched** — entry age, ₹2 lakh, ₹436, one-account rule, auto-debit consent, 30-day lien, 1 Jun–31 May, termination at 55, no entry past 50, all four pro-rata premiums, account requirement |
| PMSBY | 8 | **8/8 matched** — 18–70, ₹2 lakh death, ₹1 lakh one eye/limb, ₹20, cover year, termination at 70 (nearer birthday), account requirement, one-account rule |
| PMUY | 6 | **6/6 matched** — adult woman from poor household, deprivation declaration, declaration is the criterion, no existing household LPG, free stove + first refill, deposit-free |
| e-Shram | 4 | **3/3 matched** (16+, no income criteria, not an income-tax payee). The fourth check was deliberately inverted: the string "16–59" is **confirmed absent** from the current FAQ, which is what closed that ambiguity |
| PM-SYM | 5 | **5/5 matched** — entry 18–40, "₹15000 or less", exclusion wording "any statutory Social Security Scheme such as NPS, ESIC, EPFO", income-tax exclusion. **The contradictory "less than Rs 15,000" phrasing is confirmed still present on the same page** — the ambiguity is real and is in the source, not in our reading of it |
| UK old-age | 6 | **5/5 matched** — 60+, ≤₹4,000 from all sources or BPL, Gram Sabha selection, **₹1,500/month present on the department's own page**, ssp portal. Sixth check inverted: the page says nothing about other pensions |
| UK widow | 6 | **4/4 eligibility matched** — 18+, ≤₹4,000 or BPL, Gram Sabha, death certificate. Two inverted checks confirmed again: **no rupee amount appears anywhere on that page**, and it says nothing about other pensions |

An error in the second pass was found and corrected by this one: the earlier
run reported the old-age page as not stating ₹1,500. It does. The pattern had
been written for `Rs` and the page uses the `₹` character — a fault in the
check, not in the data. The value was never wrong and nothing shipped from it.

**Re-confirmed in the browser**, because these two facts carry the most weight
and appear on no departmental page:

> "A pension of ₹1,500/- per month is provided to eligible beneficiaries."
> "The widow must not be receiving any other pension benefits."
> — <https://www.myscheme.gov.in/schemes/uwps>

> "A pension of ₹1,500/- per month is provided to eligible beneficiaries."
> "The applicant must not be receiving any other pension."
> — <https://www.myscheme.gov.in/schemes/oap>

Both myScheme pages also say **family** monthly income where both departmental
pages say the applicant's. The conflict recorded in section 2 row 2b is real
and unchanged.

### What this pass does and does not establish

It establishes that the shipped files are a faithful transcription of the
official pages as they read today. Three machine passes now agree, and the one
disagreement between them was a bug in a check rather than a wrong value.

It does **not** substitute for the signature. Everything above was still done
by a machine reading a page, which is the exact failure mode `verified_by`
exists to catch — and this same session had already got one value wrong on the
first pass. A person still has to look. What has changed is how long that
takes: the values and their sources are now on one screen, per scheme, via
`python3 -m sathi.review`.
