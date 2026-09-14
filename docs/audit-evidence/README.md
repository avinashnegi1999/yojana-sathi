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
