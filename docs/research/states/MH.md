# Maharashtra — schemes, from official pages.

Research notes, **not signed**. Read on **27 September 2026**.

Sources: Social Justice & Special Assistance Department (sjsa.maharashtra.gov.in); Maharashtra Building and Other Construction Workers Welfare Board (mahabocw.in).

<br>

## Pensions — Social Justice & Special Assistance Department.

| # | Scheme | ₹ a month | Who qualifies | Source |
|---|---|---|---|---|
| 1 | Sanjay Gandhi Niradhar Anudan Yojana | **1,500** | Destitute men and women 18–65; destitute widows; unmarried women over 35 — and **BPL list or family income ≤ ₹21,000 a year** | [page](https://sjsa.maharashtra.gov.in/en/scheme/sanjay-gandhi-niradhar-anudan-yojana/) |
| 2 | Shravanbal Seva Rajya Nivruttivetan Yojana (state old-age pension) | **1,500** | 65+; **BPL list or annual income < ₹21,000** | [page](https://sjsa.maharashtra.gov.in/en/scheme/shravan-bal-rajya-nivruttivetan-yojana/) |

- Row 1: "– Destitute men and women aged 18 to 65 years – Destitute widows – Unmarried women over 35 years of age · To be eligible for this scheme, the beneficiary's name must be on the Below Poverty Line (BPL) list or the family's annual income must be up to ₹21,000." · "Under the Sanjay Gandhi Niradhar Anudan Yojana, eligible beneficiaries receive financial assistance of ₹1500 per month."
- Row 2: "Eligible elderly individuals aged 65 and above, whose names are on the Below Poverty Line (BPL) list or whose annual income is less than ₹21,000, receive financial assistance of ₹1500 per month under the Shravanbal Seva State Pension Scheme."
- Pages last updated **25 April 2025**. Apply at the Collector's / Tehsildar's office (Sanjay Gandhi Yojana branch) or Talathi office (district pages).
- ? How these combine with the national pensions (IGNOAPS etc.) in Maharashtra is not on these pages.

<br>

## Construction Workers Welfare Board (MAHABOCW).

Source: <https://mahabocw.in/welfare-schemes/> — 21 benefits with forms, in four groups. Registered workers only.

| Group | Benefit | ₹ |
|---|---|---|
| Social | First marriage reimbursement | **30,000** |
| Social | PMJJBY, PMSBY enrolment | premiums (board) |
| Social | Recognition of prior learning training | — |
| Education (first two children) | Class 1–7 / 8–10 | **2,500 / 5,000** a year (75% attendance) |
| Education | 10th or 12th with 50%+ | **10,000** |
| Education | Class 11–12 | **10,000** a year |
| Education | Graduate (also the worker's wife) | **20,000** a year |
| Education | Medical / engineering degree | **1,00,000 / 60,000** a year |
| Education | Diploma / post-graduate diploma | **20,000 / 25,000** a year |
| Education | MS-CIT fee refund | fee |
| Health | Family planning after one girl child | ? |
| Health | 75% or permanent disability | **2,00,000** |
| Health | De-addiction treatment | — |
| Financial | **Death at work** | **5,00,000** to legal heir |
| Financial | Natural death | **2,00,000** to legal heir |
| Financial | Atal housing (urban / rural) | **2,00,000** each |
| Financial | Funeral (age 50–60) | **10,000** |
| Financial | Widow / widower assistance | ? |
| Financial | Home-loan interest | up to **2,00,000** (on loans up to ₹6 lakh) |

- Quotes: "पहिल्या विवाहाच्या खर्चाच्या प्रतिपूर्तीसाठी रु. ३०,०००/-" · "कामगाराचा कामावर असताना मृत्यु झाल्यास – रु.५,००,०००/- (कायदेशीर वारसास)" · "कामगाराचा नैसर्गिक मृत्यू झाल्यास – रु.२,००,०००/- (कायदेशीर वारसास)" · "कामगाराचा मृत्यू झाल्यास अंत्यविधीकरिता- रु. १०,०००/- (वय ५० ते ६०)"
- ! Board registration needed for all.

<br>

## Count so far.

| Group | Found |
|---|---|
| Pensions | 2 |
| Construction board | 21 |
| **Total** | **23** |

**Encodable with one new question each:** rows 1–2 need "family income ≤ ₹21,000 a year" — the app's income bands would need a band edge at ₹21,000 a year (₹1,750 a month), or BPL (`is_bpl` exists). Row 2 is BPL **or** income, so BPL alone under-covers it; row 1 also needs "destitute".
