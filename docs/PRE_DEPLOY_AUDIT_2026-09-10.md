# Pre-deploy audit — the four signed schemes

Signed: PMJJBY, PMSBY, PMUY, UK_OLD_AGE


## 1. Edge behaviour on every threshold that decides a verdict


**PMJJBY — age**

| value | verdict |
|---|---|
| 17 | ineligible |
| 18 | eligible |
| 50 | eligible |
| 51 | ineligible |
| 55 | ineligible |
| 70 | ineligible |

**PMSBY — age**

| value | verdict |
|---|---|
| 17 | ineligible |
| 18 | eligible |
| 60 | eligible |
| 69 | unknown |
| 70 | ineligible |
| 71 | ineligible |

**PMUY — age**

| value | verdict |
|---|---|
| 17 | ineligible |
| 18 | eligible |
| 19 | eligible |
| 60 | eligible |

**UK_OLD_AGE — age**

| value | verdict |
|---|---|
| 58 | ineligible |
| 59 | ineligible |
| 60 | eligible |
| 61 | eligible |
| 85 | eligible |

**Every yes/no answer, including "don't know"**

| scheme | field | no | don't know | yes |
|---|---|---|---|---|
| PMJJBY | has_bank_account | ineligible | unknown | eligible |
| PMSBY | has_bank_account | ineligible | unknown | eligible |
| PMUY | is_woman | ineligible | unknown | eligible |
| PMUY | household_has_lpg | eligible | unknown | ineligible |
| PMUY | pmuy_declaration_met | ineligible | unknown | eligible |
| UK_OLD_AGE | uk_pension_income_or_bpl | ineligible | unknown | eligible |
| UK_OLD_AGE | uk_pension_selected | ineligible | unknown | eligible |
| UK_OLD_AGE | receives_other_pension | eligible | eligible | eligible |


## 2. What a real person is now told


---

### Construction worker, 30, Uttarakhand, has a bank account, no LPG


**English**

```
I found 3 scheme(s) for you.
The one with the largest benefit is at the top.

1. Pradhan Mantri Jeevan Jyoti Bima Yojana 🆕 (you do not have this yet)
   What you get: Life insurance: ₹2 lakh on death from any cause, subject to policy terms. Standard renewal premium ₹436/year. Non-accidental death is excluded for the first 30 days on joining/rejoining. Only one account per person; consent and premium payment are required. This cover is in addition to any other life insurance you already hold.
   Why you qualify: Your reported age meets the entry-age condition. You reported an account; the branch must confirm it is suitable for enrolment.
   Where to go: your bank branch

2. Pradhan Mantri Suraksha Bima Yojana 🆕 (you do not have this yet)
   What you get: Accident insurance. ₹2 lakh for accidental death or the permanent disabilities specified by the scheme. ₹1 lakh for permanent, complete loss of sight in one eye or use of one hand or foot. Any other partial disability pays nothing, and hospital bills are not reimbursed — this is not health cover. Death by suicide is not covered. It is in addition to any other insurance you already hold. Premium ₹20 yearly, debited with your consent from your bank or post office account.
   Why you qualify: You are between 18 and 70, which this scheme requires. You have a bank account, which is what the cover attaches to.
   Where to go: your bank branch

3. Pradhan Mantri Ujjwala Yojana 🆕 (you do not have this yet)
   What you get: Deposit-free LPG connection, first refill and stove for eligible poor households. This is in-kind support, not annual cash or unlimited free refills. Distributor verification and prescribed documents are required.
   Why you qualify: Your reported age meets the entry-age condition. You reported that the applicant is a woman.
   Where to go: on the online portal

You can get accident insurance of up to ₹4,00,000 — that amount is paid only if an accident happens.

This is what you may be entitled to — the money has not been paid yet. You have to apply for it.

There are 3 scheme(s) I cannot be sure about.
I will not guess — a wrong answer costs you a day's wages and the fare.

For all of them: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it.

At the centre, ask about each one by name — “Am I eligible for this?”
• e-Shram registration
• Pradhan Mantri Shram Yogi Maandhan
• Uttarakhand widow pension

These schemes will not be available to you right now:
• Uttarakhand old-age pension — Your reported age is outside the entry-age range.
```

**Hindi**

```
आपके लिए 3 योजना(एँ) मिलीं।
सबसे ऊपर वह है जिसमें सबसे ज़्यादा फ़ायदा है।

1. प्रधानमंत्री जीवन ज्योति बीमा योजना 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: जीवन बीमा: पॉलिसी की शर्तों के अनुसार किसी भी कारण से मृत्यु पर ₹2 लाख। सामान्य नवीनीकरण प्रीमियम ₹436 प्रति वर्ष। जुड़ने या दोबारा जुड़ने के पहले 30 दिनों में गैर-दुर्घटना मृत्यु पर दावा नहीं मिलता। एक व्यक्ति का केवल एक खाता; सहमति और प्रीमियम भुगतान ज़रूरी हैं। यह बीमा आपकी किसी भी दूसरी जीवन बीमा पॉलिसी के अतिरिक्त है।
   क्यों मिलेगा: आपकी बताई उम्र प्रवेश की आयु-शर्त पूरी करती है।। आपने खाता बताया है; शाखा से पुष्टि कराएँ कि उससे नामांकन हो सकता है।
   कहाँ जाना है: अपने बैंक की शाखा

2. प्रधानमंत्री सुरक्षा बीमा योजना 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: दुर्घटना बीमा। दुर्घटना में मृत्यु या योजना में बताई गई स्थायी विकलांगता पर ₹2 लाख। एक आँख की रोशनी या एक हाथ या पैर का इस्तेमाल पूरी तरह और हमेशा के लिए खोने पर ₹1 लाख। इसके अलावा किसी आंशिक विकलांगता पर कुछ नहीं मिलता, और अस्पताल का खर्च वापस नहीं मिलता — यह स्वास्थ्य बीमा नहीं है। आत्महत्या से मृत्यु पर दावा नहीं मिलता। यह आपके किसी भी दूसरे बीमा के अतिरिक्त है। सालाना ₹20 आपकी सहमति से बैंक या डाकघर खाते से कटते हैं।
   क्यों मिलेगा: आपकी उम्र 18 से 70 साल के बीच है, जो इस योजना के लिए ज़रूरी है। आपका बैंक खाता है, इसी से यह बीमा जुड़ता है
   कहाँ जाना है: अपने बैंक की शाखा

3. प्रधानमंत्री उज्ज्वला योजना 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: पात्र गरीब परिवारों के लिए बिना जमा राशि का एलपीजी कनेक्शन, पहला रिफिल और चूल्हा। यह वस्तु रूप में सहायता है, सालाना नकद या असीमित मुफ़्त रिफिल नहीं। वितरक का सत्यापन और निर्धारित दस्तावेज़ ज़रूरी हैं।
   क्यों मिलेगा: आपकी बताई उम्र प्रवेश की आयु-शर्त पूरी करती है।। आपने महिला आवेदक होना बताया है।
   कहाँ जाना है: ऑनलाइन पोर्टल पर

आपको 4,00,000 रुपये तक का दुर्घटना बीमा मिल सकता है — यह रकम तभी मिलती है जब दुर्घटना हो।

यह वह रकम है जिसके आप हक़दार हो सकते हैं — यह पैसा अभी मिला नहीं है। मिलने के लिए आवेदन करना होगा।

3 योजना(एँ) ऐसी हैं जिनके बारे में मैं पक्का नहीं कह सकता।
मैं अंदाज़ा नहीं लगाऊँगा — गलत जानकारी पर आपका दिन और किराया बर्बाद होगा।

तीनों के लिए एक ही बात: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा।

केंद्र पर हर एक का नाम लेकर पूछें — “क्या मैं इसके लिए पात्र हूँ?”
• ई-श्रम पंजीकरण
• प्रधानमंत्री श्रम योगी मानधन
• उत्तराखंड विधवा पेंशन

इस समय ये योजनाएँ आपको नहीं मिलेंगी:
• उत्तराखंड वृद्धावस्था पेंशन — आपकी बताई उम्र प्रवेश की आयु-सीमा में नहीं है।
```

---

### Woman, 65, Uttarakhand, on the pension route, income under the line


**English**

```
I found 3 scheme(s) for you.
The one with the largest benefit is at the top.

1. Pradhan Mantri Suraksha Bima Yojana 🆕 (you do not have this yet)
   What you get: Accident insurance. ₹2 lakh for accidental death or the permanent disabilities specified by the scheme. ₹1 lakh for permanent, complete loss of sight in one eye or use of one hand or foot. Any other partial disability pays nothing, and hospital bills are not reimbursed — this is not health cover. Death by suicide is not covered. It is in addition to any other insurance you already hold. Premium ₹20 yearly, debited with your consent from your bank or post office account.
   Why you qualify: You are between 18 and 70, which this scheme requires. You have a bank account, which is what the cover attaches to.
   Where to go: your bank branch

2. Uttarakhand old-age pension 🆕 (you do not have this yet)
   What you get: ₹1,500 monthly pension after approval. If you already draw another pension, ask the office whether it affects this application — the national scheme portal says it does, the department's own page does not mention it. Apply through ssp.uk.gov.in or assisted services. Eligibility and documents are checked by the department. Do not add multiple pension routes together as guaranteed payments.
   Why you qualify: You reported living in Uttarakhand; residence documents are checked during application. Your reported age meets the entry-age condition.
   Where to go: on the online portal

3. Pradhan Mantri Ujjwala Yojana 🆕 (you do not have this yet)
   What you get: Deposit-free LPG connection, first refill and stove for eligible poor households. This is in-kind support, not annual cash or unlimited free refills. Distributor verification and prescribed documents are required.
   Why you qualify: Your reported age meets the entry-age condition. You reported that the applicant is a woman.
   Where to go: on the online portal

These could be worth about ₹18,000 to you in a year.

On top of that there is accident insurance of up to ₹2,00,000 — that amount is paid only if an accident happens.

This is what you may be entitled to — the money has not been paid yet. You have to apply for it.

There are 3 scheme(s) I cannot be sure about.
I will not guess — a wrong answer costs you a day's wages and the fare.

For all of them: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it.

At the centre, ask about each one by name — “Am I eligible for this?”
• e-Shram registration
• Pradhan Mantri Shram Yogi Maandhan
• Uttarakhand widow pension

These schemes will not be available to you right now:
• Pradhan Mantri Jeevan Jyoti Bima Yojana — Your reported age is outside the entry-age range.
```

**Hindi**

```
आपके लिए 3 योजना(एँ) मिलीं।
सबसे ऊपर वह है जिसमें सबसे ज़्यादा फ़ायदा है।

1. प्रधानमंत्री सुरक्षा बीमा योजना 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: दुर्घटना बीमा। दुर्घटना में मृत्यु या योजना में बताई गई स्थायी विकलांगता पर ₹2 लाख। एक आँख की रोशनी या एक हाथ या पैर का इस्तेमाल पूरी तरह और हमेशा के लिए खोने पर ₹1 लाख। इसके अलावा किसी आंशिक विकलांगता पर कुछ नहीं मिलता, और अस्पताल का खर्च वापस नहीं मिलता — यह स्वास्थ्य बीमा नहीं है। आत्महत्या से मृत्यु पर दावा नहीं मिलता। यह आपके किसी भी दूसरे बीमा के अतिरिक्त है। सालाना ₹20 आपकी सहमति से बैंक या डाकघर खाते से कटते हैं।
   क्यों मिलेगा: आपकी उम्र 18 से 70 साल के बीच है, जो इस योजना के लिए ज़रूरी है। आपका बैंक खाता है, इसी से यह बीमा जुड़ता है
   कहाँ जाना है: अपने बैंक की शाखा

2. उत्तराखंड वृद्धावस्था पेंशन 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: स्वीकृति के बाद ₹1,500 मासिक पेंशन। यदि आपको पहले से कोई और पेंशन मिल रही है तो कार्यालय में पूछें कि इस आवेदन पर उसका असर है या नहीं — राष्ट्रीय पोर्टल कहता है कि असर है, विभाग के अपने पृष्ठ पर इसका ज़िक्र नहीं है। ssp.uk.gov.in या सहायता केंद्र से आवेदन करें। विभाग पात्रता और दस्तावेज़ जाँचता है। अलग-अलग पेंशन विकल्पों को जोड़कर निश्चित भुगतान न मानें।
   क्यों मिलेगा: आपने उत्तराखंड में रहना बताया है; आवेदन में निवास के दस्तावेज़ जाँचे जाएँगे।। आपकी बताई उम्र प्रवेश की आयु-शर्त पूरी करती है।
   कहाँ जाना है: ऑनलाइन पोर्टल पर

3. प्रधानमंत्री उज्ज्वला योजना 🆕 (यह आपके पास अभी नहीं है)
   क्या मिलेगा: पात्र गरीब परिवारों के लिए बिना जमा राशि का एलपीजी कनेक्शन, पहला रिफिल और चूल्हा। यह वस्तु रूप में सहायता है, सालाना नकद या असीमित मुफ़्त रिफिल नहीं। वितरक का सत्यापन और निर्धारित दस्तावेज़ ज़रूरी हैं।
   क्यों मिलेगा: आपकी बताई उम्र प्रवेश की आयु-शर्त पूरी करती है।। आपने महिला आवेदक होना बताया है।
   कहाँ जाना है: ऑनलाइन पोर्टल पर

इनसे आपको साल भर में लगभग 18,000 रुपये मिल सकते हैं।

इसके अलावा 2,00,000 रुपये तक का दुर्घटना बीमा भी है — यह रकम तभी मिलती है जब दुर्घटना हो।

यह वह रकम है जिसके आप हक़दार हो सकते हैं — यह पैसा अभी मिला नहीं है। मिलने के लिए आवेदन करना होगा।

3 योजना(एँ) ऐसी हैं जिनके बारे में मैं पक्का नहीं कह सकता।
मैं अंदाज़ा नहीं लगाऊँगा — गलत जानकारी पर आपका दिन और किराया बर्बाद होगा।

तीनों के लिए एक ही बात: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा।

केंद्र पर हर एक का नाम लेकर पूछें — “क्या मैं इसके लिए पात्र हूँ?”
• ई-श्रम पंजीकरण
• प्रधानमंत्री श्रम योगी मानधन
• उत्तराखंड विधवा पेंशन

इस समय ये योजनाएँ आपको नहीं मिलेंगी:
• प्रधानमंत्री जीवन ज्योति बीमा योजना — आपकी बताई उम्र प्रवेश की आयु-सीमा में नहीं है।
```

---

### Man, 45, no bank account, household already has LPG


**English**

```
You did not fully qualify for any scheme right now. That is not the end of it.

Closest: Pradhan Mantri Jeevan Jyoti Bima Yojana — An eligible account is needed before enrolment; ask the branch about opening one.

Still, talk to your nearest centre once. States run their own schemes too, and those are not in my list.

There are 3 scheme(s) I cannot be sure about.
I will not guess — a wrong answer costs you a day's wages and the fare.

For all of them: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it.

At the centre, ask about each one by name — “Am I eligible for this?”
• e-Shram registration
• Pradhan Mantri Shram Yogi Maandhan
• Uttarakhand widow pension

These schemes will not be available to you right now:
• Pradhan Mantri Jeevan Jyoti Bima Yojana — An eligible account is needed before enrolment; ask the branch about opening one.
• Pradhan Mantri Suraksha Bima Yojana — You need a bank or post office account for this. A Jan Dhan account opens free at any bank branch, and the cover attaches to it.
• Pradhan Mantri Ujjwala Yojana — The connection must be issued in an adult woman's name.
• Uttarakhand old-age pension — Your reported age is outside the entry-age range.
```

**Hindi**

```
अभी किसी योजना में आप पूरे नहीं उतरे। यह बात यहीं ख़त्म नहीं होती।

सबसे नज़दीक: प्रधानमंत्री जीवन ज्योति बीमा योजना — नामांकन से पहले उपयुक्त खाता चाहिए; खाता खोलने के लिए शाखा में पूछें।

फिर भी अपने नज़दीकी केंद्र पर एक बार बात करें। वहाँ राज्य की अलग योजनाएँ भी होती हैं जो मेरे पास दर्ज नहीं हैं।

3 योजना(एँ) ऐसी हैं जिनके बारे में मैं पक्का नहीं कह सकता।
मैं अंदाज़ा नहीं लगाऊँगा — गलत जानकारी पर आपका दिन और किराया बर्बाद होगा।

तीनों के लिए एक ही बात: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा।

केंद्र पर हर एक का नाम लेकर पूछें — “क्या मैं इसके लिए पात्र हूँ?”
• ई-श्रम पंजीकरण
• प्रधानमंत्री श्रम योगी मानधन
• उत्तराखंड विधवा पेंशन

इस समय ये योजनाएँ आपको नहीं मिलेंगी:
• प्रधानमंत्री जीवन ज्योति बीमा योजना — नामांकन से पहले उपयुक्त खाता चाहिए; खाता खोलने के लिए शाखा में पूछें।
• प्रधानमंत्री सुरक्षा बीमा योजना — इसके लिए बैंक या डाकघर में खाता चाहिए। जन धन खाता किसी भी बैंक शाखा में मुफ़्त खुल जाता है, फिर यह बीमा उसी से जुड़ जाएगा।
• प्रधानमंत्री उज्ज्वला योजना — कनेक्शन वयस्क महिला के नाम पर होना चाहिए।
• उत्तराखंड वृद्धावस्था पेंशन — आपकी बताई उम्र प्रवेश की आयु-सीमा में नहीं है।
```

---

### Says don't know to almost everything


**English**

```
You did not fully qualify for any scheme right now. That is not the end of it.

Closest: Uttarakhand old-age pension — Your reported age is outside the entry-age range.

Still, talk to your nearest centre once. States run their own schemes too, and those are not in my list.

There are 6 scheme(s) I cannot be sure about.
I will not guess — a wrong answer costs you a day's wages and the fare.

• e-Shram registration — what I could not check: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it
   Ask this at the centre: “Am I eligible for e-Shram registration?”

• Pradhan Mantri Jeevan Jyoti Bima Yojana — what I could not check: you did not tell me: bank account
   Ask this at the centre: “Am I eligible for Pradhan Mantri Jeevan Jyoti Bima Yojana?”

• Pradhan Mantri Suraksha Bima Yojana — what I could not check: you did not tell me: bank account
   Ask this at the centre: “Am I eligible for Pradhan Mantri Suraksha Bima Yojana?”

• Pradhan Mantri Ujjwala Yojana — what I could not check: you did not tell me: woman applicant, household LPG connection, Ujjwala deprivation declaration
   Ask this at the centre: “Am I eligible for Pradhan Mantri Ujjwala Yojana?”

• Pradhan Mantri Shram Yogi Maandhan — what I could not check: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it
   Ask this at the centre: “Am I eligible for Pradhan Mantri Shram Yogi Maandhan?”

• Uttarakhand widow pension — what I could not check: the rules are written down, but a person has not confirmed them yet — until they do I will not put a number on it
   Ask this at the centre: “Am I eligible for Uttarakhand widow pension?”

These schemes will not be available to you right now:
• Uttarakhand old-age pension — Your reported age is outside the entry-age range.
```

**Hindi**

```
अभी किसी योजना में आप पूरे नहीं उतरे। यह बात यहीं ख़त्म नहीं होती।

सबसे नज़दीक: उत्तराखंड वृद्धावस्था पेंशन — आपकी बताई उम्र प्रवेश की आयु-सीमा में नहीं है।

फिर भी अपने नज़दीकी केंद्र पर एक बार बात करें। वहाँ राज्य की अलग योजनाएँ भी होती हैं जो मेरे पास दर्ज नहीं हैं।

6 योजना(एँ) ऐसी हैं जिनके बारे में मैं पक्का नहीं कह सकता।
मैं अंदाज़ा नहीं लगाऊँगा — गलत जानकारी पर आपका दिन और किराया बर्बाद होगा।

• ई-श्रम पंजीकरण — जो जानकारी नहीं मिली: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा
   केंद्र पर यह पूछें: “क्या मैं ई-श्रम पंजीकरण के लिए पात्र हूँ?”

• प्रधानमंत्री जीवन ज्योति बीमा योजना — जो जानकारी नहीं मिली: आपसे यह जानकारी नहीं मिली: बैंक खाता
   केंद्र पर यह पूछें: “क्या मैं प्रधानमंत्री जीवन ज्योति बीमा योजना के लिए पात्र हूँ?”

• प्रधानमंत्री सुरक्षा बीमा योजना — जो जानकारी नहीं मिली: आपसे यह जानकारी नहीं मिली: बैंक खाता
   केंद्र पर यह पूछें: “क्या मैं प्रधानमंत्री सुरक्षा बीमा योजना के लिए पात्र हूँ?”

• प्रधानमंत्री उज्ज्वला योजना — जो जानकारी नहीं मिली: आपसे यह जानकारी नहीं मिली: महिला आवेदक, परिवार में एलपीजी कनेक्शन, उज्ज्वला वंचना घोषणा
   केंद्र पर यह पूछें: “क्या मैं प्रधानमंत्री उज्ज्वला योजना के लिए पात्र हूँ?”

• प्रधानमंत्री श्रम योगी मानधन — जो जानकारी नहीं मिली: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा
   केंद्र पर यह पूछें: “क्या मैं प्रधानमंत्री श्रम योगी मानधन के लिए पात्र हूँ?”

• उत्तराखंड विधवा पेंशन — जो जानकारी नहीं मिली: इस योजना के नियम लिखे हुए हैं, पर किसी व्यक्ति ने अभी उनकी पुष्टि नहीं की — जब तक वह नहीं होती, मैं पक्की बात नहीं कहूँगा
   केंद्र पर यह पूछें: “क्या मैं उत्तराखंड विधवा पेंशन के लिए पात्र हूँ?”

इस समय ये योजनाएँ आपको नहीं मिलेंगी:
• उत्तराखंड वृद्धावस्था पेंशन — आपकी बताई उम्र प्रवेश की आयु-सीमा में नहीं है।
```
