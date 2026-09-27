# Uttarakhand — schemes, from official pages.

Research notes, **not signed**. Read on **27 September 2026** from the Uttarakhand government's own sites. Each value keeps the exact sentence it came from.

Sources: Social Welfare Department (socialwelfare.uk.gov.in) and its Government Orders; Building and Other Construction Workers Welfare Board (ukbocw.uk.gov.in).

<br>

## ! The widow pension rate now has a primary source.

**Government Order No. 40/XVII-2/22-19(05) 2019-TC, 21 April 2022**, Principal Secretary L. Fanai, raises the old-age pension, the **destitute widow maintenance grant** and the disability pension by ₹100 to **₹1,500 a month**, effective immediately, central share included.

- PDF: <https://cdnbbsr.s3waas.gov.in/s357bafb2c2dfeefba931bb03a835b1fa9/uploads/2025/02/202502041827311603.pdf> — listed on <https://socialwelfare.uk.gov.in/document-category/government-orders-pension/> as "Regarding increase in pension rates under the Old Age, Widow and Disability Pension Scheme."
- SHA-256 of the file read: `53fee6d6f489a47ecd9c9815f068ce6b916ab60cce2d03c11464d52d0cc33f1a`

> "वृद्धावस्था, निराश्रित विधवा भरण पोषण अनुदान एवं दिव्यांग पेंशन योजनान्तर्गत पेंशन दरों में ₹100/- प्रतिमाह की दर से वृद्धि करते हुये उक्त योजनान्तर्गत ₹1500/- प्रतिमाह की दर से पेंशन प्रदान किये जाने की श्री राज्यपाल सहर्ष स्वीकृति प्रदान करते हैं।"
>
> "उक्त वृद्धावस्था पेंशन, निराश्रित विधवा भरण पोषण अनुदान तथा दिव्यांग पेंशन योजनान्तर्गत बढ़ी हुई दरों में केन्द्रांश भी सम्मिलित है।"

This is what `data/schemes/uk_widow.toml` was waiting for. Before re-signing: confirm no later order changed the rate (the order list shows none), and save the PDF under `docs/audit-evidence/`.

<br>

## Pensions — Social Welfare Department.

| # | Scheme | ₹ a month | Who qualifies | Source |
|---|---|---|---|---|
| 1 | Old Age Pension | **1,500** | 60+; income ≤ ₹4,000 a month from all sources, or BPL card; selected in a Gram Sabha open meeting | [page](https://socialwelfare.uk.gov.in/service/old-age-pension/) · GO 40 above |
| 2 | Widow Pension (destitute widow maintenance grant) | **1,500** (GO 40) | 18+; income ≤ ₹4,000 or BPL card; Gram Sabha selection; husband's death certificate | [page](https://socialwelfare.uk.gov.in/service/widow-pension/) · GO 40 above |
| 3 | Disability (Divyang) Pension | **1,500** (GO 40) | ? rules page not found on the department site | GO 40 above |
| 4 | Parityakta (abandoned / destitute women) Pension | ? not stated | Abandoned or destitute woman, or mentally ill wife / husband, 18–60, or husband missing / abandoning for 1+ year; income ≤ ₹4,000 or BPL. Destitute unmarried women 40–60 also covered (documents list) | [page](https://socialwelfare.uk.gov.in/service/destitute-pension/) |
| 5 | Teelu Rauteli Pension | **1,200** (order below) | 18–60; disabled 20–40% **while doing agricultural work**; rural; no income limit; moves to old-age pension at 60 | [page](https://socialwelfare.uk.gov.in/service/teelurautelipension/) |
| 6 | Bauna (short stature) Pension | **1,200** | Height 4 ft or less; 21+; no income limit | [page](https://socialwelfare.uk.gov.in/service/bauna-pension/) |
| 7 | Kisan (farmer) Pension | **1,200** (order below) | ? rules page not found | order below |

- **Apply online** at <https://ssp.uk.gov.in>, the Umang app, or Apuni Sarkar (<https://eservices.uk.gov.in>).
- Row 1: "A pension of ₹1,500/- per month is provided to eligible beneficiaries." · "(ii) The monthly income of the applicant should not exceed Rs. 4000/- from all sources or the applicant should be a BPL card holder. (iii) The applicant should have been selected in an open meeting of the Gram Sabha."
- Row 2: "(i) The age of the applicant should not be less than 18 years. (ii) Monthly income should not be more than Rs. 4000/- or the applicant should be a BPL card holder."
- Row 4: "(i) Such abandoned/destitute woman or mentally deranged wife/husband whose age is more than 18 years and less than 60 years or the period of husband being missing/abandoned is more than 1 year."
- Row 5: "(iii) The applicant should have become disabled while doing agricultural work. (iv) The percentage of disability should be between 20 to 40." · Rate: Directorate letter 1949/स0क0/पेंशन/2021-22, 14 Oct 2021, citing GO 336/XVII-2/20-19(05)2019 of 12.10.2021: "तीलू रौतेली एवं बौना पेंशन की वर्तमान प्रदत्त दर ₹ 1000/- प्रतिमाह में ₹ 200/- की वृद्धि" — [PDF](https://cdnbbsr.s3waas.gov.in/s357bafb2c2dfeefba931bb03a835b1fa9/uploads/2025/02/20250204618906416.pdf).
- Row 6: "A pension of ₹1,200/- per month is provided to eligible beneficiaries." · "(i) Height of the applicant should be 04 feet or less than 04 feet. (ii) Age limit of the applicant should be 21 years or more."
- Row 7: GO 1501/XVII-2/21-19(05) 2019, 22 Dec 2021: "किसान पेंशन योजनान्तर्गत वर्तमान में प्रदत्त दर ₹1000/-प्रतिमाह में ₹200/-प्रतिमाह की दर से वृद्धि कर ₹1200/-प्रतिमाह प्रदान किये जाने की श्री राज्यपाल सहर्ष स्वीकृति प्रदान करते हैं।" — [PDF](https://cdnbbsr.s3waas.gov.in/s357bafb2c2dfeefba931bb03a835b1fa9/uploads/2025/06/20250618656866568.pdf).

<br>

## Construction Workers Welfare Board (UKBOCWWB).

Source: <https://ukbocw.uk.gov.in/StaticPages/SpecialScheme-hi.aspx> (page 1 of 2 read) · list: <https://ukbocw.uk.gov.in/StaticPages/SchemeDetail-hi.aspx>

For workers registered under the BOCW Act, 1996, **and construction workers employed under MGNREGA**:
> "भवन एवं अन्य सन्निर्माण कर्मकार अधिनियम, 1996 के प्राविधानों के अन्तर्गत पंजीकृत पात्र कामगारों तथा मनरेगा में नियोजित निर्माण श्रमिकों हेतु संचालित कल्याणकारी योजनाएं।"

| # | Benefit | ₹ | Quote |
|---|---|---|---|
| 8 | Pension | **1,000 a month from 60; 1,500 from 65**; family pension 500 to the surviving spouse | "60 वर्ष की आयु पूर्ण कर चुके कामगारों को 1,000 प्रति माह की दरसे पेंशन तथा 65 वर्ष की आयु होने पर 1,500 प्रति माह की पेंशन दी जाएगी।" |
| 9 | Housing advance | up to **50,000** loan; 5 years' membership; at least 5% interest | "मकान की खरीद ⁄ निर्माण हेतु 50,000 तक अग्रिम ऋण राशि" |
| 10 | Disability pension | **1,000 a month** + up to **40,000** grant (paralysis, leprosy, accident) | "1,000 प्रतिमाह की दर से निःशक्तता पेंशन तथा 40,000 तक की अनुग्रह राशि।" |
| 11 | Death | **4,00,000** accidental death at work; **2,00,000** ordinary death | "नियोजन (कार्य के दौरान) दुर्घटना में मृत्यु होने पर 4,00,000 तथा सामान्य मृत्यु होने की दशा में मृतक कर्मकार के नामितों ⁄ आश्रितों को 2,00,000 की आर्थिक सहायता।" |
| 12 | Funeral | **10,000** | "अन्त्येष्टि संस्कार के खर्च के लिए मृतक कर्मकार के नामितों ⁄ आश्रितों को 10,000 की सहायता" |
| 13 | Health insurance | premium paid by the board | National Health Insurance scheme |
| 14 | Children's education | **1,800** (class 1–5), **2,400** (6–10), **3,000** (11–12), **10,000** (graduate / postgraduate) a year | table on the page |
| 15–24 | Child benefit, tool kit, post-marriage, maternity, bicycle, solar, umbrella, skill upgrade, sanitary napkins, toilet building | ? on page 2 | [list](https://ukbocw.uk.gov.in/StaticPages/SchemeDetail-hi.aspx) |

- Claims for death, disability and funeral within **2 months**, through the Labour Enforcement Officer or Registration Officer.
- ! Every board benefit needs **board registration** — a new question.
- ! The app's existing `UK_OLD_AGE` (₹18,000 a year) matches row 1.

<br>

## Count so far.

| Group | Found |
|---|---|
| Social Welfare pensions | 7 |
| Construction board | 17 (7 with amounts read, 10 on page 2) |
| **Total** | **24** |

Encodable today, no new question: **row 1** (already live as `UK_OLD_AGE`) and **row 2** once re-signed with GO 40. Row 5 needs "disabled 20–40% in farm work"; row 6 needs height; the board needs registration.

<br>

## Still to research.

- Disability pension and Kisan pension rules pages (not on the department site; try ssp.uk.gov.in).
- Parityakta pension amount.
- Board page 2 (10 schemes).
- Uttarakhand's other labour boards, and any state accident / life insurance scheme.
