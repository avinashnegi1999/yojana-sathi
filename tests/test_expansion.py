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
    schemes = {k: replace(v, verified_by='test fixture only') for k,v in real.items()}
    p = Profile(state='UK', age=30, has_bank_account=True, is_woman=True,
                is_widow=True, uk_pension_income_or_bpl=True,
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
    assert evaluate(p,schemes['PMUY']).is_eligible
    assert evaluate(replace(p,household_has_lpg=True),schemes['PMUY']).verdict is Verdict.INELIGIBLE
    assert evaluate(replace(p,pmuy_declaration_met=None),schemes['PMUY']).verdict is Verdict.UNKNOWN
    assert schemes['PMUY'].benefit['value_basis']=='in_kind'
    assert schemes['PMUY'].benefit['annual_value_inr']==0
    for sc in real.values():
        assert evaluate(p,sc).verdict is Verdict.UNKNOWN

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
    schemes={k:replace(v,verified_by='test fixture only')
             for k,v in load_all(ROOT/'data/schemes').items()}
    def expected(conditions):
        if False in conditions:
            return Verdict.INELIGIBLE
        return Verdict.UNKNOWN if None in conditions else Verdict.ELIGIBLE
    checked=0
    for state,age,income,selected,widow in itertools.product(
            (None,'UK','UP'),(None,17,18,59,60,75),
            (None,False,True),(None,False,True),(None,False,True)):
        p=Profile(state=state,age=age,uk_pension_income_or_bpl=income,
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
    assert checked==1080

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
