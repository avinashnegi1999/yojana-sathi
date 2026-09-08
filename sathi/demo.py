"""Fixed fictional profiles for judges. No personal input, signatures or metrics.

# ! This command demonstrates the encoded rules, not a person's entitlement.
# ! The normal evaluate() entry point still enforces human verification.
"""
from dataclasses import replace

from sathi.channels.base import Reply
from sathi.core.profile import Profile
from sathi.core.schemes import Scheme
from sathi.rules.engine import _evaluate_rules, Verdict


def examples():
    """No user-derived values are accepted by this demonstration."""
    worker = Profile(state='UK', age=30, income_band='upto_5000',
                     is_unorganised_worker=True, has_bank_account=True,
                     is_income_tax_payer=False, is_epfo_or_esic_member=False,
                     nps_exclusion_applies=False)
    pension = Profile(state='UK', age=65, uk_pension_income_or_bpl=True,
                      uk_pension_selected=True)
    return (
        ('PMJJBY', worker, 'Age 30; individual account; applying for new cover.',
         'उम्र 30; व्यक्तिगत खाता; नए बीमा के लिए आवेदन।'),
        ('PM_SYM', worker, 'Age 30; unorganised worker; income within the ceiling; no listed exclusions.',
         'उम्र 30; असंगठित श्रमिक; आय सीमा के भीतर; बताई गई रोक लागू नहीं।'),
        ('PMSBY', worker, 'Age 30; individual bank account.', 'उम्र 30; व्यक्तिगत बैंक खाता।'),
        ('ESHRAM', worker, 'Age 30; unorganised worker; no EPFO/ESIC or income-tax exclusion.',
         'उम्र 30; असंगठित श्रमिक; ईपीएफओ/ईएसआईसी या आयकर की रोक लागू नहीं।'),
        ('UK_OLD_AGE', pension, 'Age 65; Uttarakhand; income/BPL condition met; local selection completed.',
         'उम्र 65; उत्तराखंड; आय/बीपीएल शर्त पूरी; स्थानीय चयन पूरा।'),
        ('UK_WIDOW', replace(pension, age=35, is_widow=True),
         'Separate example: widow aged 35; Uttarakhand; income/BPL condition met; local selection completed.',
         'अलग उदाहरण: विधवा, उम्र 35; उत्तराखंड; आय/बीपीएल शर्त पूरी; स्थानीय चयन पूरा।'),
        ('PMUY', Profile(age=30,is_woman=True,household_has_lpg=False,pmuy_declaration_met=True),
         'Adult woman; no household LPG; official deprivation declaration condition met.',
         'वयस्क महिला; परिवार में एलपीजी नहीं; आधिकारिक वंचना घोषणा की शर्त पूरी।'),
    )


def replies(schemes: dict[str, Scheme], lang: str = 'hi') -> list[Reply]:
    en = lang == 'en'
    header = ('DEMO — fictional examples, not your eligibility. These rule files await human review. '
              'No example is saved as user impact. Each example is separate; benefits are not added together.'
              if en else 'DEMO — काल्पनिक उदाहरण, आपकी पात्रता नहीं। नियमों की मानवीय समीक्षा बाकी है। '
              'उदाहरण उपयोगकर्ता प्रभाव में नहीं गिने जाते। हर उदाहरण अलग है; लाभ जोड़े नहीं जाते।')
    out = [Reply(text=header)]
    for code, profile, english, hindi in examples():
        if code not in schemes:
            continue
        scheme = schemes[code]
        if scheme.stubs:
            outcome = 'Rules incomplete' if en else 'नियम अधूरे हैं'
        else:
            result = _evaluate_rules(profile, scheme, 0, scheme.benefit['value_basis'])
            outcome = ({Verdict.ELIGIBLE:'Example matches the encoded conditions',
                        Verdict.INELIGIBLE:'Example does not meet the encoded conditions',
                        Verdict.UNKNOWN:'Example needs more information'} if en else
                       {Verdict.ELIGIBLE:'उदाहरण कोड की शर्तें पूरी करता है',
                        Verdict.INELIGIBLE:'उदाहरण कोड की शर्तें पूरी नहीं करता',
                        Verdict.UNKNOWN:'उदाहरण में जानकारी बाकी है'})[result.verdict]
        label = 'Human review pending; not an approval.' if en else 'मानवीय समीक्षा बाकी; यह स्वीकृति नहीं है।'
        text = f'DEMO · {code}\n{scheme.name(lang)}\n{english if en else hindi}\n\n{outcome}\n{label}\n\n{scheme.summary(lang)}\n\n{scheme.official_url}'
        out.append(Reply(text=text))
    return out
