# Scheme audit evidence

This directory holds the exact public documents used for Avinash's manual
scheme sign-off. It is evidence, not a substitute for the `source_url` in a
scheme file, which remains the primary public citation.

## IGNOAPS — PIB release, 11 February 2026

- File: `ignoaps-pib-2026-02-11.pdf`
- Official source: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2226202&reg=3&lang=2
- SHA-256: `4F8FE601AFE7951305B0C662FA56228B1DC17BA8238D7083E3443B7A6241827A`
- Checked claims: BPL eligibility; ₹200/month for ages 60–79; ₹500/month from age 80.

The source file is a local copy of the public PIB release. Re-download it from
the official URL and compare the SHA-256 before relying on it if its provenance
is in doubt.

## IGNWPS — PIB Department of Rural Development Year Ender 2025

- File: `ignwps-pib-2025-year-ender.pdf`
- Official source: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2210378&lang=1&reg=1
- SHA-256: `469D99BAD7186A4E6CC546E318AC5EBFE628BDCE70E4929EE537FCA57C190D7A`
- Checked claims: BPL widow; ₹300/month for ages 40–79; ₹500/month from age 80.

## IGNDPS — Government of India Lok Sabha reply, May 2026

- File: `igndps-goi-2026-05.pdf`
- Official source: https://cdnbbsr.s3waas.gov.in/s3e58aea67b01fa747687f038dfde066f6/uploads/2026/05/20260526963824969.pdf
- SHA-256: `F3874E3842AC425DD84CDD8E0F11395D6278E4FEF695172135097377256D0159`
- Checked claims: BPL household; age 18+; severe or multiple disability at 80%+; ₹300/month for ages 18–79; ₹500/month from age 80.
- Open point: this document does not mention dwarfism, although the draft summary says dwarfs qualify. Do not treat that statement as verified from this PDF.

## NPS-Traders — Maandhan FAQ, captured 14 September 2026

- File: `nps-traders-maandhan-faq-2026-09-14.txt`
- Official source: https://maandhan.in/show_content.php?lang=1&level=1&ls_id=78&lid=64&page=74
- SHA-256: `6E71136D9AF4272EA2D32C06AE86D22F7502540D0A33E98DE786AAC0225441ED`
- Checked claims: eligible occupation and ₹1.5 crore turnover ceiling; entry ages 18–40; income-tax, government-funded NPS, EPFO, ESIC and PM-SYM exclusions; ₹3,000/month from age 60; spouse pension after pension begins; CSC enrollment; age-based contribution and auto-debit.
- Open point: this captured FAQ refers to a separate contribution table but does not contain it, so `premium_inr` remains `"TODO"`.

## NPS-Traders — Labour Ministry contribution chart

- File: `nps-traders-labour-contribution-chart.pdf`
- Official source: https://www.labour.gov.in/static/uploads/2025/06/45622468af6003658367ea762959d151.pdf
- SHA-256: `5762197509A10B1F926E49F2D80C0E05A46AF1523D9FC1E71DD8FA024430AF0F`
- Checked claims: entry-age table (18–40); worker contribution ₹55–₹200/month; equal Central Government contribution; total ₹110–₹400/month.
- Resolution: this evidence fills `benefit.premium_inr`; the FAQ capture's contribution-chart open point is closed.

## PM Vishwakarma — MSME PIB release, 18 December 2023

- File: `pm-vishwakarma-pib-benefits-2023-12-18.pdf`
- Official source: https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1987716
- SHA-256: `923AC2CB42F14A54AA9E48EDF064895498578448AFEC1995CCDF7543627222C2`
- Checked claims: all 18 listed trades; recognition certificate and ID; training and ₹500/day stipend; toolkit e-voucher up to ₹15,000; credit and marketing support.
- Open point: this release does not state the draft's age-18, one-member-per-family or prior-loan eligibility conditions. Do not sign from this document alone.

## PM Vishwakarma — MSME PIB eligibility release, 21 December 2023

- File: `pm-vishwakarma-pib-eligibility-2023-12-21.pdf`
- Official source: https://www.pib.gov.in/PressReleaseIframePage.aspx?PRID=1989108
- SHA-256: `81236E97C7998BBB6EC6FF937A66D9C73858993968AE8ABF39B43114CE541A7F`
- Checked claims: 18 family-based traditional trades in the unorganised, self-employed sector; age 18+; active engagement in the trade; the five-year PMEGP/MUDRA/PM SVANidhi loan condition and repaid MUDRA/SVANidhi exception; one family member; family definition.
- Resolution: the intake and rule now collect and enforce the government-service-in-family condition. This evidence alone still does not verify every application-paperwork claim in the draft.

## PM-JAY — Cabinet coverage for senior citizens aged 70+, 11 September 2024

- File: `pmjay-70-pib-cabinet-2024-09-11.pdf`
- Official source: https://www.pib.gov.in/Pressreleaseshare.aspx?PRID=2053883
- SHA-256: `CEEE40545C5CB795D0A7597631CF8809BBDF70298CD8A6B4D317FE74F630270B`
- Checked claims: every person aged 70+ qualifies irrespective of income or socioeconomic status; a distinct card is issued; ₹5 lakh annual hospital cover; an extra individual ₹5 lakh top-up for a 70+ member already covered through PM-JAY; private insurance and ESI do not bar eligibility; CGHS, ECHS and Ayushman CAPF members choose between their existing scheme and PM-JAY.
- Open point: the release does not verify the draft's application documents, CSC application route, card-expiry statement or listed-hospital wording. Do not sign the whole scheme from this PDF alone.

## Tamil Nadu pensions (TN_IGNDPS) — Revenue Administration page, 27 September 2026

- File: `tn-cra-social-security-schemes-2026-09-27.pdf` (browser print of the page, English translation, printed 27 Sep 2026)
- Official source: https://cra.tn.gov.in/about_schemes_t.php
- SHA-256: `EF1E559A44EAAFA75CBB7919D4B6997AC0C591D656DFBF70990ABF804870F812`
- Checked claims for TN_IGNDPS: disability 80% or more, below poverty line, age 18+; ₹300 central + ₹1,200 state a month; apply online at tnesevai.tn.gov.in, resolved within 30 days.
- Also on the page (for later drafts): the TN old-age and widow pensions require the person to be **destitute** as well as BPL; state pension rules and amounts; free-house exclusion from property value.
- Open points: the "Total" column is cut off at the print edge (the two shares are visible); the page lists **no documents**, so `documents` stays `"TODO"`.

## Sikkim pensions (SK_IGNOAPS, SK_IGNWPS, SK_IGNDPS) — pension registration portal, 27 September 2026

- File: `sk-pension-schemes-2026-09-27.pdf` (browser print of the portal home page, 3 pages, printed 27 Sep 2026)
- Official source: https://pensionscheme.sikkim.gov.in/
- SHA-256: `31D1487A41BF36210CA4617AC427CF902FEC538467FE65753197DE0D77282A95`
- Checked claims for SK_IGNOAPS: SSC/COI/residential certificate; BPL household with an Antyodaya or Priority Household ration card; Aadhaar; Jan Dhan bank account; age 60+; ₹1,500 a month at 60–69, ₹2,000 at 70+, ₹2,500 at 80+.
- Checked claims for SK_IGNWPS: widow, age 21+ (not NSAP's 40), husband's death certificate, non-marriage certificate; ₹2,000 a month, "Central and State Share"; no age band.
- Checked claims for SK_IGNDPS: age 18+; certificate from the medical authority "certifying more than 80% disabilities" and an identity card; ₹2,000 a month, "Central and State Share"; no age band.
- Also on the page (not drafted): NFBS ₹30,000 once, unmarried women ₹2,000 (45+), CM state disability ₹1,500 (40%+, not on IGNDPS).
- Open points: the 70 and 80 rows overlap ("70 years+ and above"), read as 70–79; the old-age row, unlike the other two, does not say it includes the state share.

## Mizoram old-age pension (MZ_IGNOAPS) — Directorate of Social Welfare page, 27 September 2026

- File: `mz-old-age-pension-2026-09-27.pdf` (browser print of the page, 4 pages, text on pages 1–2; page updated 23 Jul 2026)
- Official source: https://socialwelfare.mizoram.gov.in/page/old-age-pension-old-age-home
- SHA-256: `46DE436E196990A813CCAEC357B8ACB4654F8E1E097A31CE6D782535AB73FECE`
- Checked claims for MZ_IGNOAPS: Mizoram pays ₹1,000 a month per beneficiary from 1 April 2024; eligible age 60; ₹200 central + ₹1,000 state = ₹1,200 a month at 60–79; ₹500 + ₹1,000 = ₹1,500 from 80.
- Open points: the page does not state the BPL condition (taken from the national IGNOAPS rule, PIB PRID=2226202); it lists **no documents and no way to apply**, so both stay `"TODO"`; "above 80 years" and "80 years and above" both appear — read as from 80.

## Madhya Pradesh Kalyani pension (MP_KALYANI) — District Dhar scheme page, 27 September 2026

- File: `mp-kalyani-dhar-2026-09-27.pdf` (browser print of the page, 3 pages; site last updated 16 Sep 2026)
- Official source: https://dhar.nic.in/en/scheme/chief-minister-kalyani-pension-scheme/ (NIC-hosted district site — not the state department)
- SHA-256: `E21FC73BDD8CB5192E4D9F02F4D2108035A386129DEF9E73A3EB36554BFADD16`
- Checked claims for MP_KALYANI: started 1 April 2018; widow aged 18–79; not an income-tax payer; not a government employee/officer; no family pension; BPL not required; no other pension; ₹600 a month from the state; 13 documents including Samagra ID and native-of-MP proof; apply at District Panchayat (rural) or Municipality (urban), or via Public Service Guarantee.
- Open points: a district page, so a state order is the stronger source; "not a government employee" is not encoded (no self-only field); where to apply was `"TODO"` until the `local_office` location was added the same day (panchayat, block or municipal office).

## Uttarakhand widow pension (UK_WIDOW) — GO 40 of 21 April 2022, and the department's Hindi overview, 27 September 2026

- File: `uk-go40-pension-rates-2022-04-21.pdf` (scanned government order, 2 pages)
- Official source: https://cdnbbsr.s3waas.gov.in/s357bafb2c2dfeefba931bb03a835b1fa9/uploads/2025/02/202502041827311603.pdf (Social Welfare Department's S3WaaS upload)
- SHA-256: `53FEE6D6F489A47ECD9C9815F068CE6B916AB60CCE2D03C11464D52D0CC33F1A`
- Checked claims: Order 40/XVII-2/22-19(05)2019TC, Social Welfare Section-2, dated 21 April 2022; old-age, destitute widow maintenance grant and disability pension rates raised by ₹100 to ₹1,500 a month; immediate effect; raised rates include the central share.
- File: `uk-pension-overview-hi-2026-09-27.html` (saved HTML of the department's Hindi "पेंशन योजनाएं" page)
- Official source: https://socialwelfare.uk.gov.in/hi/पेंशन-योजनाएं/
- SHA-256: `44F7A6445A437DCF535E9890B2FA6678735BAB8061109697FE18E6CBA3A44B41`
- Checked claims: widow pension ₹1,500 a month; family income ≤ ₹4,000 a month or BPL; not receiving any other pension benefit; age 18+; Gram Sabha open-meeting selection; documents (income certificate or BPL card, family register or ration card, husband's death certificate, selection proposal, attested photo, passbook, Aadhaar).
- Resolves both open questions from the 2026-09-10 sign-off: (a) the rate, (b) the other-pension bar. Open point: confirm no order after April 2022 changed the rate.

## Punjab old-age pension (PB_OLD_AGE_WOMEN, PB_OLD_AGE_MEN) — Social Security department page, 27 September 2026

- File: `pb-pensions-2026-09-27.pdf` (browser print of the page, 3 pages; page last updated 14-09-2026)
- Official source: https://sswcd.punjab.gov.in/en/social-security/pensionsfinancial-assistance
- SHA-256: `B327A88668DAC7A1167BF4B133788B57A8A9AA81CDEB55CC2CE78A0DDE212C8B`
- Checked claims: women 58+, men 65+; total annual income ≤ ₹60,000 including business, rent and interest; land ≤ 2.5 acres Nehri/Chahi or 5 acres Barani / waterlogged (husband and wife together); self-declaration: no government or private job, not self-employed, no commercial property, house ≤ 200 sq m in towns, not an income-tax, VAT or professional-tax payer; one proof of age (Aadhaar, voter card, voter list, matriculation or birth certificate); forms at DSSO, CDPO, Sewa Kendra, SDM, Anganwadi, Panchayat, BDPO; CDPO verifies within a month; DSSO sanctions; paid through banks; ₹1,500 a month from 1 July 2021 under all four schemes.
- Also on the page (not drafted): widows / destitute women under 58 and unmarried women over 30; dependent children under 21; disabled persons (≥ 50%, mental disability at any level) — all ₹1,500, same income limit. NSAP central rates, "applicable for BPL families and ... SECC 2011".
- Open points: the app's income question asks earnings, not total income; the commercial-property, house-size, VAT and professional-tax items are not asked (they are on the declaration she signs).

## PMJDY — Jan Dhan "Scheme Details" page, 27 September 2026

- File: `pmjdy-scheme-details-2026-09-27.pdf` (browser print of the page, 2 pages)
- Official source: https://pmjdy.gov.in/scheme (Mission Office, Department of Financial Services)
- SHA-256: `D917CE3FF21B8CD9FA0326D93CB30870959D779B9D01405B38A63FE8D135F4F4`
- Checked claims: a basic savings bank deposit (BSBD) account "can be opened in any bank branch or Business Correspondent (Bank Mitra) outlet, by persons not having any other account"; no minimum balance; interest earned; RuPay debit card; accident cover ₹1 lakh, ₹2 lakh for accounts opened after 28.8.2018, with the RuPay card; overdraft up to ₹10,000 for eligible holders; account eligible for DBT, PMJJBY, PMSBY, APY and MUDRA.
- Open points (resolved the same day, below): this page does not list the documents needed, the small-account route for someone without Aadhaar, or the dormant-account advice in the draft's renewal line.
- File: `pmjdy-account-opening-form-en.pdf` (downloaded directly from the site, 1 page)
- Official source: https://pmjdy.gov.in/files/forms/account-opening/English.pdf
- SHA-256: `1867A9E69136410F4FF007421A05681BA2548730730C4C4AE572C979B239E0C4`
- Checked claims: the form asks for an "Aadhaar/ EID No." and a photograph "To be captured through system or obtain latest photograph not older than six month"; overdraft of ₹5,000 after six months, one member per household (older than the scheme page's ₹10,000).
- File: `pmjdy-brochure-2014-en.pdf` (downloaded directly from the site, 40 pages; the 2014 mission document)
- Official source: https://pmjdy.gov.in/files/E-Documents/PMJDY_BROCHURE_ENG.pdf
- SHA-256: `43C19D71D4566B02B96DC10F1FF23CA3C0185C18A5D0E1CACDA31ACFC4DA0A84`
- Checked claims: none used. It is written for banks and states no worker document list, small-account route or dormant-account rule.
- Resolution: the draft's documents now follow the form (Aadhaar number or EID, photograph). The small-account sentence and the dormant-account line were removed as unsourced.

## PM-JAY 70+ (PMJAY_70) — registration, documents and hospitals, PIB, 27 September 2026

nha.gov.in/PM-JAY renders an empty page (checked in a browser, 27 Sep 2026), so these PIB sources replace it for the paperwork.

- File: `pmjay-70-pib-registration-2024-12-09.html` (saved HTML of the release)
- Official source: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2082288
- SHA-256: `652710FB00B6959191F25D7924C5599652C6CE5B03F14656B4E61DCF702ADFAC`
- Checked claims: register at the nearest empanelled hospital, or self-register on the Ayushman app or www.beneficiary.nha.gov.in; toll-free 14555, missed call 1800110770; ₹5 lakh cover irrespective of income; extra top-up of up to ₹5 lakh for a 70+ member of a family already on PM-JAY; CGHS, ECHS and CAPF members choose; private insurance and ESI do not bar; pre-existing diseases covered from day one.
- File: `pmjay-70-pib-backgrounder-2025-06-17.pdf` (PIB backgrounder "Affordable and Accessible Healthcare for All", 17 June 2025)
- Official source: https://static.pib.gov.in/WriteReadData/specificdocs/documents/2025/jun/doc2025617571401.pdf
- SHA-256: `7383E68917A2F08570A20CB162D8901879A411FDE9C84E5386BE03599A0430F6`
- Checked claims: "Requiring only Aadhaar for registration".
- File: `pmjay-70-pib-hospitals-2025-07-29.html` (saved HTML of the release)
- Official source: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2149693
- SHA-256: `B31A00C00583390DB16D6C8D52E17CE59264C7B3C77558694BE3FD240AF6EACB`
- Checked claims: free treatment up to ₹5 lakh per year; portability to any of 31,466 empanelled hospitals regardless of place of residence.
- Resolution: documents now "Aadhaar card" only; apply location "online" (app / portal), with the hospital route in the summary. Removed as unsourced: CSC as the place to apply, ration card and mobile number, "the card does not expire".
- Open point: whether a 70+ member of a family already on PM-JAY needs a new card (see the file header).

## PM Vishwakarma — Guidelines for Implementation, and portal pages, 27 September 2026

- File: `pm-vishwakarma-guidelines-v30.pdf` (official "PM Vishwakarma — Guidelines for Implementation", v30.0, 64 pages)
- Official source: pmvishwakarma.gov.in (downloaded by Avinash from the portal)
- SHA-256: `F356E6CDC3CE3C9BA32562730577BA9E8FB7FCD5D55438D257AC51E77D7D0928`
- Checked claims: para 4 eligibility (hands-and-tools artisan in a listed family-based trade, unorganised, self-employed; 18+ on the registration date; no PMEGP, PM SVANidhi or MUDRA loan in the past 5 years, counted from sanction, except fully repaid MUDRA and SVANidhi; one member per family — husband, wife, unmarried children; a person in government service and their family are not eligible); para 5.1.4 documents (Aadhaar, mobile number, bank details, ration card; without a ration card, Aadhaar numbers of all family members; CSC helps open a bank account); para 5.1.5 no fee; para 5.1.6 CSC or online self-registration with Aadhaar biometric authentication; para 3.2.3 stipend ₹500 a day; para 6.3 toolkit up to ₹15,000 as e-RUPI / e-vouchers; interest 5% to the beneficiary.
- Files: `pm-vishwakarma-portal-eligibility-2026-09-27.pdf`, `pm-vishwakarma-portal-trades-2026-09-27.pdf`, `pm-vishwakarma-portal-objectives-2026-09-27.pdf` (browser prints of pmvishwakarma.gov.in, 5 pages each)
- SHA-256: `ADC6BA58E157ABB08F84D1A72A40CD41FFE809472F2FAA0B2D3310CED0034E9D`, `2BDED2073198E488371C92FCA55AA814A987154637139D2F95633425EB56E35F`, `A3A0EF76BCFD798E8C13DB5CA19C4E60950F476F110BF29D192C6C96E6BAFE39`
- Checked claims: the portal's eligibility and trade list agree with the guidelines.
- Resolution: the loan question said "still unpaid" for all three schemes, which let someone with a repaid PMEGP loan through. It now asks about any PMEGP loan in 5 years, or an unrepaid MUDRA / SVANidhi loan. The toolkit summary now says e-vouchers. A pasted FAQ text was not used as evidence: it is a paraphrase, not the portal's own wording.

## APY — "Details of the Scheme" with the contribution table (Annex-1), 27 September 2026

- File: `apy-details-jansuraksha.pdf` (official scheme document, 4 pages)
- Official source: https://jansuraksha.gov.in/Files/APY/ENGLISH/APY.pdf (Department of Financial Services)
- SHA-256: `3B7291F47C9E17DC3378745E0FB45100B3119DEB699D9CF5CFC353B6390EF939`
- Checked claims: Annex-1 monthly contribution for the ₹1,000/month pension tier by entry age — 18: ₹42, 19: 46, 20: 50, 21: 54, 22: 59, 23: 64, 24: 70, 25: 76, 26: 82, 27: 90, 28: 97, 29: 106, 30: 116, 31: 126, 32: 138, 33: 151, 34: 165, 35: 181, 36: 198, 37: 218, 38: 240, 39: 264, 40: 291; tiers ₹1,000–₹5,000; return of corpus to the nominee ₹1.7–₹8.5 lakh; section 5.2: an account opened on or after 1 October 2022 is closed if the subscriber is found to have been an income-tax payer on or before the application date.
- File: `apy-pfrda-faq-2026-09-27.html` (saved HTML of the PFRDA FAQ)
- Official source: https://pfrda.org.in/w/faqs/atal-pension-yojana
- SHA-256: `2C5A5BFA43D387452B59CF50B6B499A536E08AE0720F0099BEDFEEC1D18186BB`
- Checked claims: the FAQ says the contribution depends on entry age, frequency and pension slab, "provided as Annexure" — the annexure is not linked from the page, hence the DFS document above.
- Resolution: `premium_inr` filled as Hindi prose for the ₹1,000 tier (₹42–₹291 a month by entry age), following PM-SYM; the summary now warns that a past income-tax payer cannot join.


## Tamil Nadu pensions — Chennai district "OAP Eligibility" page, 27 September 2026

- File: `tn-chennai-oap-eligibility-2026-09-27.pdf` (headless-browser print of the page)
- Official source: https://chennai.nic.in/oap-eligibility/ (Chennai district, NIC-hosted)
- SHA-256: `536713FAC7046B302BF43EBA2AC86DE0D985EC82E0DE12102289139B94099FED`
- Checked claims for IGNDPS: documents — photo, smart card or ration card, Aadhaar, voter ID, BPL number, bank passbook, UDID card, disability passbook. Similar lists for IGNOAPS, IGNWPS, DWPS, DDWPS, UWPS, CMUPT and DAPS.
- Open points (why TN_IGNDPS stays parked): this district page adds "Destitute" and "Annual income should not above 3 lakhs" to IGNDPS, which the state CRA page does not state; a non-official site claims ₹1,800 a month for 80%+ disability, against CRA's ₹1,500 — unconfirmed. Resolve both from a state order before using this list.
