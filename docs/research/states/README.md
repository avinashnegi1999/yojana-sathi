# State schemes — research index.

One note per state and union territory, read from **official government pages** on 27 September 2026. Every value in a note keeps the exact sentence it came from, so an audit only has to find that sentence on the linked page. **Nothing here is in the app or signed.**

Totals across all 36, as listed on myScheme: [`../STATE_SCHEMES_2026-09-27.md`](../STATE_SCHEMES_2026-09-27.md).

<br>

## Where each state stands.

**Confirmed** = amount and rules read on an official page. **Partial** = some confirmed, some flagged. **Unconfirmed** = official pages unreachable or silent; only non-official figures, which must not be drafted.

| State / UT | Status | Headline (official unless flagged) | Note |
|---|---|---|---|
| Tamil Nadu | Confirmed | Pensions ₹1,200 (disability ₹1,500) incl. state top-up; accident, insurance, farm-worker board; ~36 schemes | [TN](TN.md) |
| Uttarakhand | Confirmed | Old age ₹1,500; **widow ₹1,500 by GO 40 of 21 Apr 2022**; Kisan, Teelu Rauteli, Bauna ₹1,200; construction board | [UK](UK.md) |
| Punjab | Confirmed | 4 state pensions ₹1,500 since Jul 2021, full rules (income ≤ ₹60,000) | [PB](PB.md) |
| Sikkim | Confirmed | 7 schemes: old age ₹1,500–2,500 by age, widow / disability ₹2,000, unmarried women ₹2,000 | [SK](SK.md) |
| Maharashtra | Confirmed | 2 pensions ₹1,500 (income ≤ ₹21,000); construction board 21 benefits | [MH](MH.md) |
| Delhi | Confirmed | Old age ₹2,000 (60–69) / ₹2,500 (70+), income < ₹1 lakh, 5 years' residence | [DL](DL.md) |
| Chhattisgarh | Confirmed | Mahtari Vandan ₹1,000 to married women 21+, full rules | [CG](CG.md) |
| Jharkhand | Confirmed | Maiyan Samman ₹2,500 to women 18–49, full rules; pensions not read | [JH](JH.md) |
| Goa | Confirmed | DSSS ₹2,000 / ₹2,500 / ₹3,500 by category; income limit to check | [GA](GA.md) |
| Mizoram | Confirmed | Old age ₹1,200 (60–79) / ₹1,500 (80+) | [MZ](MZ.md) |
| Chandigarh | Confirmed | Old age ₹1,000, income ≤ ₹1.5 lakh, 3 years' residence | [CH](CH.md) |
| Andhra Pradesh | Partial | NTR Bharosa ₹4,000 from Apr 2024; 10 categories; application window closed 16 Sep 2026 | [AP](AP.md) |
| Odisha | Partial | ₹3,500 for 80+ and 80%+ disability from Jan 2025; base rate open | [OD](OD.md) |
| West Bengal | Partial | NSAP at ₹1,000 (since Apr 2020); ₹1,500 from Aug 2026 reported, unconfirmed | [WB](WB.md) |
| Gujarat | Partial | Widow ₹1,250 since Apr 2019; age rule conflicts | [GJ](GJ.md) |
| Madhya Pradesh | Partial | Kalyani (widow) ₹600; 7 pensions + Sambal named | [MP](MP.md) |
| Haryana | Partial | 8 allowances, rules for 5; **amounts not on the pages** | [HR](HR.md) |
| Rajasthan | Partial | 2019 order: old age ₹750 / ₹1,000; widow ₹500–1,500 by age — likely superseded | [RJ](RJ.md) |
| Jammu & Kashmir | Partial | ISSS 4 components, ₹1,000 per a district page; April 2025 increase reported | [JK](JK.md) |
| Uttar Pradesh | Partial | Rules confirmed; **amount conflict** (portal ₹500 vs reported ₹1,000); board 10 schemes | [UP](UP.md) |
| Bihar | Partial | 6 pensions named; 2019 rules; **amount conflict** (₹400 vs reported ₹1,100) | [BR](BR.md) |
| Nagaland | Partial | Central NSAP rates only, old page | [NL](NL.md) |
| Karnataka | Unconfirmed | 4 schemes named, no amounts | [KA](KA.md) |
| Telangana | Unconfirmed | ₹2,016 vs ₹4,000 conflict | [TS](TS.md) |
| Kerala | Unconfirmed | ₹2,000 reported (Nov 2025) | [KL](KL.md) |
| Assam | Unconfirmed | Orunodoi ₹1,250 reported | [AS](AS.md) |
| Himachal Pradesh | Unconfirmed | Gender-split old age reported | [HP](HP.md) |
| Tripura | Unconfirmed | MSSP ₹2,000 reported | [TR](TR.md) |
| Manipur | Unconfirmed | Old age ₹1,500 reported | [MN](MN.md) |
| Meghalaya | Unconfirmed | Old age ₹500 reported | [ML](ML.md) |
| Arunachal Pradesh | Unconfirmed | Old age ₹1,500 / ₹2,000 reported | [AR](AR.md) |
| Puducherry | Unconfirmed | ₹2,000 reported; portal down | [PY](PY.md) |
| Andaman & Nicobar | Unconfirmed | Schemes named only | [AN](AN.md) |
| Dadra & Nagar Haveli and Daman & Diu | Unconfirmed | Schemes named only | [DN](DN.md) |
| Lakshadweep | Unconfirmed | Schemes named only | [LD](LD.md) |
| Ladakh | Unconfirmed | ISSS named (see J&K) | [LA](LA.md) |

**11 confirmed · 11 partial · 14 unconfirmed.**

<br>

## Draft first — these fit questions the app already asks.

| Scheme | State | Uses |
|---|---|---|
| IGNOAPS / IGNWPS / IGNDPS at state amounts | Tamil Nadu, Sikkim, Mizoram (old age) | age, `is_bpl`, `is_widow`, `has_disability_80pct` |
| Integrated Accident and Life Insurance | Tamil Nadu | age, `is_bpl` |
| Uttarakhand widow pension — **re-sign** with GO 40 | Uttarakhand | already in the app as `UK_WIDOW` |
| Mukhyamantri Kalyani Pension | Madhya Pradesh | widow, age, income tax, `receives_other_pension` |

<br>

## New questions that would unlock the most schemes.

Each is a product decision — the app asks nothing it does not need.

| Question | Unlocks |
|---|---|
| Income, at more band edges (₹21,000 · ₹60,000 · ₹1 lakh · ₹1.5 lakh · ₹3 lakh a year) | Maharashtra, Punjab, Delhi, Chandigarh, Haryana, Goa |
| Years living in this state (3 · 5 · 15) | Delhi, Chandigarh, Haryana, Goa |
| Marital status beyond widow (married · deserted · divorced · unmarried) | Chhattisgarh, Tamil Nadu, Punjab, Goa, Sikkim, Rajasthan |
| Ration-card type (AAY · priority household) | Jharkhand, Sikkim, J&K |
| Disability 40%+ (not only 80%+) | Tamil Nadu, Sikkim, Punjab (50%), J&K, UP |
| Registered with a welfare board (construction, farm, unorganised) | Every state's board schemes |
| Government job, MP / MLA in the family | Jharkhand, Chhattisgarh |
| Destitute / property value | Tamil Nadu, Maharashtra |

<br>

## Rules of use.

- **Amounts in "unconfirmed" or "conflict" rows must never be drafted.** Find the order first.
- **Several states changed rates recently** (AP 2024, Odisha 2025, Kerala 2025, WB 2026). Recheck each amount when drafting, not from this snapshot.
- **State top-ups sit on the national pensions.** A state's IGNOAPS total replaces the app's central-share figure for that state; it is never added to it.
