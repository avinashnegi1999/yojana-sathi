"""Seven-scheme regressions: source conditions, follow-up intake and isolated demo."""
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sathi.core.profile import Profile
from sathi.core.schemes import load_all
from sathi.rules.engine import evaluate, Verdict
from sathi.conversation.flow import Conversation, State

def test_new_scheme_boundaries():
    real = load_all(ROOT / 'data/schemes')
    assert {'PMJJBY', 'UK_OLD_AGE', 'UK_WIDOW', 'PMUY'} <= real.keys()
    # ! stubs=() as well as a signature: this test is about boundary conditions,
    # ! not about ₹ values, and UK_WIDOW's amount is a documented TODO (its
    # ! source went 404). Without clearing it the file is unservable and every
    # ! boundary below would read UNKNOWN and assert nothing.
    schemes = {k: replace(v, verified_by='test fixture only', stubs=())
               for k,v in real.items()}
    p = Profile(state='UK', age=30, has_bank_account=True, is_woman=True,
                is_widow=True, uk_pension_income_or_bpl=True,
                receives_other_pension=False,
                uk_pension_selected=True, household_has_lpg=False,
                pmuy_declaration_met=True)
    for age, expected in ((17,False),(18,True),(50,True),(51,False)):
        assert evaluate(replace(p,age=age),schemes['PMJJBY']).is_eligible is expected
    for age, expected in ((59,False),(60,True),(80,True)):
        assert evaluate(replace(p,age=age),schemes['UK_OLD_AGE']).is_eligible is expected
    assert evaluate(p,schemes['UK_WIDOW']).is_eligible
    assert evaluate(replace(p,is_widow=False),schemes['UK_WIDOW']).verdict is Verdict.INELIGIBLE
    assert evaluate(replace(p,state='UP'),schemes['UK_WIDOW']).verdict is Verdict.INELIGIBLE
    # The broad income band must never stand in for the separate income/BPL answer.
    for band in ('upto_5000','above_25000'):
        q=replace(p,income_band=band,uk_pension_income_or_bpl=None)
        assert evaluate(q,schemes['UK_WIDOW']).verdict is Verdict.UNKNOWN
    assert evaluate(replace(p,uk_pension_income_or_bpl=False),schemes['UK_WIDOW']).verdict is Verdict.INELIGIBLE
    # ! Neither pension refuses someone for already drawing one. myScheme says
    # ! it disqualifies; both departmental pages omit it entirely, and a wrong
    # ! refusal is a pension nobody claims. Both files tell her to ask at the
    # ! office instead. The answer is still collected and still shown.
    q=replace(p,age=65,receives_other_pension=True)
    for code in ('UK_OLD_AGE','UK_WIDOW'):
        assert evaluate(q,schemes[code]).is_eligible, \
            f'{code}: an existing pension must not silently refuse this route'
    assert evaluate(p,schemes['PMUY']).is_eligible
    assert evaluate(replace(p,household_has_lpg=True),schemes['PMUY']).verdict is Verdict.INELIGIBLE
    assert evaluate(replace(p,pmuy_declaration_met=None),schemes['PMUY']).verdict is Verdict.UNKNOWN
    assert schemes['PMUY'].benefit['value_basis']=='in_kind'
    assert schemes['PMUY'].benefit['annual_value_inr']==0
    # ! Unsigned schemes stay UNKNOWN on the real files. Signed ones are meant
    # ! to answer, so skip those rather than making every future sign-off fail
    # ! a boundary test that is not about sign-off at all.
    for code, sc in real.items():
        if sc.is_human_verified:
            continue
        assert evaluate(p,sc).verdict is Verdict.UNKNOWN, code

def test_the_two_state_pensions_are_never_counted_as_two_payments():
    # ! A 60-year-old widow in Uttarakhand satisfies BOTH pension files. The
    # ! state pays one pension. Before this, the result screen and the printed
    # ! pack would both have added them and promised her twice the money —
    # ! exactly the failure that adding an insurance cover to a pension caused.
    from sathi.rules.engine import value_totals, exclusive_groups
    real = load_all(ROOT / 'data/schemes')
    groups = exclusive_groups(real)
    assert groups.get('UK_OLD_AGE') and groups['UK_OLD_AGE'] == groups.get('UK_WIDOW'),         'both Uttarakhand pensions must sit in one exclusive group'

    # Give both files a real, equal value and a signature, so the totals are
    # exercised for the day they are signed off rather than only today.
    signed = {}
    for code, sc in real.items():
        benefit = dict(sc.benefit)
        if code in ('UK_OLD_AGE', 'UK_WIDOW'):
            benefit['annual_value_inr'] = 18000
        signed[code] = replace(sc, verified_by='test fixture only', stubs=(),
                               benefit=benefit)
    # ! "No other pension" is about a pension already being RECEIVED. Someone
    # ! receiving none still qualifies for both routes on paper, which is
    # ! exactly the case that used to be added up.
    p = Profile(state='UK', age=65, has_bank_account=True, is_woman=True,
                is_widow=True, uk_pension_income_or_bpl=True,
                receives_other_pension=False,
                uk_pension_selected=True, household_has_lpg=False,
                pmuy_declaration_met=True)
    results = tuple(evaluate(p, signed[c]) for c in ('UK_OLD_AGE', 'UK_WIDOW'))
    assert all(r.is_eligible for r in results), 'the overlap case must actually occur'
    payout, cover = value_totals(results, signed)
    assert payout == 18000, f'one pension, not two; got {payout}'
    assert cover == 0

    # And the worker-facing screen must show that same single figure.
    from sathi.render import templates
    for lang in ('hi', 'en'):
        block = templates.eligible_block(results, signed, frozenset(), lang)
        assert '36,000' not in block and '36000' not in block, block

def test_no_reason_is_said_to_a_worker_twice():
    """Two criteria on one field must not repeat the same sentence.

    # ! Caught in the pre-deploy audit of the signed schemes: PMSBY has an age
    # ! band and an age termination rule, both on `age`, so the result screen
    # ! read "You are between 18 and 70, which this scheme requires." twice.
    """
    from sathi.render import templates
    real = load_all(ROOT / 'data/schemes')
    signed = {c: replace(v, verified_by='test fixture only', stubs=())
              for c, v in real.items()}
    p = Profile(state='UK', age=30, occupation='construction', income_band='upto_5000',
                land_holding_band='landless', family_size=4, has_bank_account=True,
                is_income_tax_payer=False, is_epfo_or_esic_member=False,
                nps_exclusion_applies=False, is_unorganised_worker=True,
                is_woman=True, is_widow=False, household_has_lpg=False,
                pmuy_declaration_met=True, uk_pension_income_or_bpl=True,
                receives_other_pension=False, uk_pension_selected=True)
    from sathi.rules.engine import evaluate_all
    results = evaluate_all(p, signed)
    assert any(r.is_eligible for r in results), 'nothing eligible, so nothing checked'
    for lang in ('hi', 'en'):
        for r in results:
            if not r.is_eligible:
                continue
            why = templates._why(r, signed[r.scheme_code], lang, limit=10)
            parts = [x.strip() for x in why.split('।' if lang == 'hi' else '. ') if x.strip()]
            assert len(parts) == len(set(parts)), f'{r.scheme_code} [{lang}] repeats: {why}'


def test_all_unknown_never_tells_a_worker_they_failed():
    """Nothing checked is not the same as not qualifying, and must not read like it.

    # ! Found on the first real phone screening, 9 September. Every scheme is
    # ! UNKNOWN today because nobody has signed the files off, and the result
    # ! screen still opened with "You did not fully qualify for any scheme" -
    # ! a statement about the worker, caused entirely by a gap of ours. The
    # ! message now says whose gap it is.
    """
    from sathi.render import templates
    from sathi.core.content import s as _s
    # ! Build the all-unknown case explicitly instead of relying on today's
    # ! data. This test is about what the RESULT SCREEN says when nothing could
    # ! be checked; it broke the day PMJJBY was signed, which had nothing to do
    # ! with the message it exists to pin.
    schemes = {c: replace(v, verified_by='unconfirmed — PENDING HUMAN VERIFICATION')
               for c, v in load_all(ROOT / 'data/schemes').items()}
    # The profile from that screening: answers given, nothing signed off.
    p = Profile(state='UK', age=30, occupation='construction',
                income_band='upto_5000', land_holding_band='landless',
                family_size=4, has_bank_account=True, is_income_tax_payer=True,
                is_epfo_or_esic_member=False, is_unorganised_worker=False,
                is_woman=False, is_widow=False, household_has_lpg=False,
                pmuy_declaration_met=False, uk_pension_income_or_bpl=False,
                receives_other_pension=False, uk_pension_selected=False)
    from sathi.rules.engine import evaluate_all
    results = evaluate_all(p, schemes)
    assert all(r.verdict is Verdict.UNKNOWN for r in results), \
        'this test is meaningless unless every scheme really is UNKNOWN'

    for lang in ('hi', 'en'):
        msg = templates.result_message(results, schemes, frozenset(), lang)
        assert _s('result.nothing_checked_header', lang).split('\n')[0] in msg
        blame = _s('result.no_match_header', lang)
        assert blame not in msg, f'[{lang}] blamed the worker for our own gap'
        # ! The seven "ask: Am I eligible for X?" lines are one line now.
        assert msg.count(_s('result.unknown_ask_all', lang)) == 1
        for code, sc in schemes.items():
            assert sc.name(lang) in msg, f'[{lang}] {code} missing from the list'

    # ! A real INELIGIBLE must still get the honest "you did not qualify" line.
    signed = {c: replace(v, verified_by='test fixture only', stubs=())
              for c, v in schemes.items()}
    hard_no = evaluate_all(replace(p, age=5), signed)
    assert any(r.verdict is Verdict.INELIGIBLE for r in hard_no)
    msg = templates.result_message(hard_no, signed, frozenset(), 'en')
    assert _s('result.no_match_header', 'en') in msg


def test_followups_preserve_unknown_and_language():
    schemes=load_all(ROOT/'data/schemes')
    for lang in ('en','hi'):
        c=Conversation(schemes); c.lang=lang
        c.profile=Profile(state='UK',age=30,income_band='upto_5000')
        c.state=State.WORKER
        c.handle('yes')
        seen=set()
        while c.state is State.FOLLOWUP:
            field=c._followup_field()
            assert field not in seen
            seen.add(field)
            c.handle('junk')
            assert c._followup_field()==field
            c.set_language('hi' if c.lang=='en' else 'en')
            assert c._followup_field()==field
            c.handle('dont_know')
            assert getattr(c.profile,field) is None
        assert 'uk_pension_income_or_bpl' in seen
        assert 'household_has_lpg' in seen
        assert c.state is State.KNOWN_SCHEMES
        assert c.profile.income_band=='upto_5000'

def test_document_pages_reach_every_option():
    from sathi.channels.whatsapp import interactive
    c=Conversation(load_all(ROOT/'data/schemes'))
    c.state=State.DOCUMENTS
    c._required_docs=tuple(f'Document {i}' for i in range(23))
    seen=set()
    for page in range(3):
        reply=c._ask_documents()
        assert len(reply.buttons)<=10
        interactive(reply.text, reply.buttons, c.lang)
        for button in reply.buttons:
            if button.value.startswith('doc:'):
                seen.add(button.value)
                c.handle(button.value)
        if page<2:
            c.handle('docs:more')
    assert seen=={f'doc:{i}' for i in range(23)}
    assert len(c._have_docs)==23
    c.handle('docs:more')
    assert c._document_page==0
    c.handle('next')
    assert c.state is State.PACK

def test_additional_answers_are_not_persisted_and_demo_has_no_events():
    from sathi.channels.router import Router
    from sathi.metrics.events import EventLog
    from sathi.conversation.flow import EXTRA_FIELDS
    log=EventLog(':memory:')
    try:
        bot=Router(load_all(ROOT/'data/schemes'),log)
        for lang in ('hi','en'):
            bot._lang['test']=lang
            for reply in bot.dispatch('test','/demo'):
                assert len(reply.text.encode('utf-16-le'))//2<4096
                assert not reply.buttons and not reply.document
        assert not log.query('SELECT * FROM events')
        p=Profile(state='UK',age=35,**{f:True for f in EXTRA_FIELDS})
        session=log.start_session('cli');log.grant_consent(session)
        log.log(session,'profile_field_captured',profile=p)
        row=log.query('SELECT * FROM events')[-1]
        assert not set(EXTRA_FIELDS)&set(row.keys())
    finally:
        log.close()

def test_new_boolean_conditions_against_source_oracle():
    import itertools
    # stubs=() for the same reason as above: UK_WIDOW's withdrawn benefit
    # amount is a documented TODO, and this sweep is about conditions, not ₹.
    schemes={k:replace(v,verified_by='test fixture only',stubs=())
             for k,v in load_all(ROOT/'data/schemes').items()}
    def expected(conditions):
        if False in conditions:
            return Verdict.INELIGIBLE
        return Verdict.UNKNOWN if None in conditions else Verdict.ELIGIBLE
    checked=0
    for state,age,income,other,selected,widow in itertools.product(
            (None,'UK','UP'),(None,17,18,59,60,75),
            (None,False,True),(None,False,True),(None,False,True),(None,False,True)):
        p=Profile(state=state,age=age,uk_pension_income_or_bpl=income,
                  receives_other_pension=other,
                  uk_pension_selected=selected,is_widow=widow)
        for code,limit in (('UK_OLD_AGE',60),('UK_WIDOW',18)):
            conditions=[None if state is None else state=='UK',
                        None if age is None else age>=limit,income,selected]
            if code=='UK_WIDOW': conditions.append(widow)
            assert evaluate(p,schemes[code]).verdict is expected(conditions)
            checked+=1
    for age,woman,lpg,poor in itertools.product(
            (None,17,18,50),(None,False,True),(None,False,True),(None,False,True)):
        p=Profile(age=age,is_woman=woman,household_has_lpg=lpg,pmuy_declaration_met=poor)
        assert evaluate(p,schemes['PMUY']).verdict is expected(
            [None if age is None else age>=18,woman,None if lpg is None else not lpg,poor])
        checked+=1
    assert checked==3024

def test_demo_is_fictional_and_has_no_session_or_signature_mutation():
    from sathi.channels.router import Router
    real=load_all(ROOT/'data/schemes')
    before={k:v.verified_by for k,v in real.items()}
    bot=Router(real)
    replies=bot.dispatch('test','/demo')
    assert not bot.sessions
    assert len(replies)>=4
    assert all('DEMO' in r.text for r in replies)
    assert any('PMJJBY' in r.text for r in replies)
    assert {k:v.verified_by for k,v in real.items()}==before
    bot.dispatch('test','/start')
    original=bot.sessions['test']
    bot._active_keyboard['test']=123
    bot.dispatch('test','/demo')
    assert bot.sessions['test'] is original
    assert bot._active_keyboard['test']==123

if __name__=='__main__':
    for name, fn in sorted(list(globals().items())):
        if name.startswith('test_'):
            fn(); print('  ok',name)
    print('test_expansion.py OK')
