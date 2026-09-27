# Sikkim — schemes, from official pages.

Research notes, **not signed**. Read on **27 September 2026**.

Source: Women & Child Welfare Department pension portal — <https://pensionscheme.sikkim.gov.in/>

<br>

## General criteria (all schemes).

1. SSC / COI / residential certificate.
2. **BPL household** holding an Antyodaya Anna Yojana or Priority Household ration card (rule 6, Sikkim Food Security Rules, 2014; Notification No. 4/SJE & WD, 1.2.2017).
3. Aadhaar card.
4. Bank account under PM Jan Dhan Yojana.

<br>

## Pensions — amounts include central and state share.

| # | Scheme | ₹ a month | Specific criteria |
|---|---|---|---|
| 1 | IGNOAPS (Sikkim) | **1,500** (60–69) · **2,000** (70–79) · **2,500** (80+) | 60+ |
| 2 | IGNWPS (Sikkim) | **2,000** | Widow **21+**; husband's death certificate; non-marriage certificate |
| 3 | IGNDPS (Sikkim) | **2,000** | 18+; disability **above 80%** |
| 4 | National Family Benefit Scheme | **30,000** once | Death of the household's breadwinner; a woman home-maker counts as a breadwinner |
| 5 | Sikkim Unmarried Women Pension (100% state) | **2,000** | Unmarried woman **45+**; unmarried certificate |
| 6 | Chief Minister's State Disability Pension (100% state) | **1,500** | **Any age**; disability **40%+**; not covered by IGNDPS |
| 7 | Sikkim Grant to Transgender | 12,000 a month (0–6 years); free education to graduation; ₹500 a month if unemployed after qualifying | Medical certificate |

> "i. Rs. 1500/- pm to the old aged person between the age group 0f 60 years - 69years. ii. Rs. 2000/- pm to the old aged person between the age group of 70 years+ and above. iii. Rs. 2500/- pm to the old aged persons having attained the age of 80 years and above ."
>
> "Indira Gandhi National Widow Pension Scheme (IGNWPS) Rs. 2000/- per month. The above amount consists of Central and State Share."
>
> "Chief Minister's State Disability Pension Scheme Rs. 1500/- per month. 100% State Innovative Scheme"

- Life certificate required yearly (portal notice: last date 28-Feb-2026 for 2026).

<br>

## Count so far.

| Group | Found (official) |
|---|---|
| Pensions and grants | 7 |
| Construction board | ? (myScheme lists 6 Sikkim construction-worker schemes) |

**Encodable today:** rows 1–3 need age, BPL (`is_bpl` exists), widow (exists), 80% disability (`has_disability_80pct` exists) — Sikkim amounts by age band. The strongest set found in any state so far. Row 6 needs a 40% disability question.
