# Punjab — schemes, from official pages.

Research notes, **not signed**. Read on **27 September 2026**.

Source: Department of Social Security and Women & Child Development — <https://sswcd.punjab.gov.in/en/social-security/pensionsfinancial-assistance>

<br>

## State pensions — ₹1,500 a month, all four.

> "Rate of Pension under all schemes has been increased from Rs.750/- to Rs. 1500/- per month w.e.f 1st July, 2021."

| # | Scheme | ₹ a month | Who qualifies |
|---|---|---|---|
| 1 | Old Age Pension | **1,500** | **Women 58+, men 65+**; annual income ≤ ₹60,000 (incl. business, rent, interest); land ≤ 2.5 acres Nehri/Chahi or ≤ 5 acres Barani / waterlogged (husband and wife together) |
| 2 | Financial Assistance to Widows and Destitute Women | **1,500** | Widows / destitute women **under 58**; unmarried women **over 30**; income ≤ ₹60,000 |
| 3 | Financial Assistance to Dependent Children | **1,500** | Children **under 21** whose mother / father / both died, or parents regularly absent or incapacitated; income ≤ ₹60,000 |
| 4 | Financial Assistance to Disabled Persons | **1,500** | Blind, handicapped, deaf-mute, mentally disabled persons unable to earn; physical disability **≥ 50%** (mental disability at any level); income ≤ ₹60,000 |

- Row 1: "pension is granted to women of 58 years of age and above and to men of 65 years of age and above. Total annual Income should not be more than Rs. 60,000/- including business or rental or interest income."
- Row 2: "Financial Assistance is granted to Widows/Destitute Women of the age below 58 years and unmarried women above the age of 30 years."
- Row 4: "Handicapped persons which have less than 50% disability will not be eligible for Financial Assistance. c) Mentally disabled persons are, however, eligible irrespective of disability."
- **Self-declaration includes:** no government or private job; not self-employed; no commercial property; house ≤ 200 sq m (urban); not an income-tax, VAT or professional-tax payer.
- **Apply:** forms at the District Social Security Officer, CDPO, Sewa Kendra, SDM, Anganwadi, Panchayat / BDPO; CDPO verifies within a month; DSSO sanctions.

<br>

## National pensions — central share as stated on the page.

| # | Scheme | ₹ a month (central) | Who |
|---|---|---|---|
| 5 | IGNOAPS | 200 (60–79); 500 (80+) | 60+, BPL / SECC |
| 6 | IGNWPS | 300; 500 from 80 | Widow 40+, BPL / SECC |
| 7 | IGNDPS | 300; 500 from 80 | 18+, disability 80%; **dwarfs eligible** |
| 8 | NFBS | ? | BPL / SECC |

> "Schemes are applicable for BPL families and for those persons who cover in Socio Economic Caste Census 2011(SECC)."

? How Punjab's state pension and NSAP combine for one person is not stated.

<br>

## Count so far.

| Group | Found |
|---|---|
| State pensions | 4 |
| NSAP | 4 |
| **Total** | **8** |

**Drafted 2026-09-27:** row 1 as `PB_OLD_AGE_WOMEN` and `PB_OLD_AGE_MEN` (two new follow-ups: `has_job_or_business`, `pb_land_over_limit`; new apply location `local_office`). Evidence: `docs/audit-evidence/pb-pensions-2026-09-27.pdf`.

**Originally noted:** rows 1–4 need an income test at ₹60,000 a year (₹5,000 a month — the app's `upto_5000` band edge fits), the land limit (`land_holding_band` exists; 2.5 / 5 acre edges needed), and "not employed / self-employed". Row 1's ages differ by gender (58 women / 65 men) — the rule engine needs both age and `is_woman`.

<br>

## Still to research.

- Punjab Building and Other Construction Workers Welfare Board (myScheme lists 15 PBOCWWB schemes).
