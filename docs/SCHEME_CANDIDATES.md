# Scheme expansion — researched candidates

**Status: research only, 11 September 2026. Nothing here is signed, and nothing
here is in the bot.** A candidate becomes a scheme when a file exists with a
source URL on every value and Avinash's name in `verified_by`. This document is
the queue, not the product.

Seven schemes are live: PMJJBY, PMSBY, PM-SYM, e-Shram, PMUY, UK_OLD_AGE,
UK_WIDOW.

---

## What this pass changed my mind about

Three findings matter more than the list itself, because each one says
something about the data model rather than about a scheme.

### 1. Not every scheme is screenable, and saying so is the useful answer

**PM-JAY** is the largest health scheme in the country — ₹5 lakh per family per
year. It is also, for our purposes, **not a rule**. Eligibility is *membership
of the SECC-2011 deprivation list*, plus whatever database a state has since
been permitted to substitute. No sequence of questions establishes it. A worker
either appears on a list or does not, and only the beneficiary portal knows.

Asking "are you on the SECC list?" would be worse than useless: almost nobody
knows, so almost everyone answers "don't know", and we would have spent a
question to produce UNKNOWN.

The honest shape is the one e-Shram already uses — a **gateway**: no ₹ value of
its own, surfaced as "go and check whether your family is listed, here is the
portal and here is what to carry." That is real help and it is not a verdict.

**The exception is worth a separate file.** The 2024 Cabinet expansion covers
**everyone aged 70 and above, irrespective of income**. That *is* computable
from one question we already ask. A 70-year-old is entitled and can be told so.

So PM-JAY is two entries, not one: a gateway, and a real rule for 70+.

### 2. The central pensions collide with the state pensions already in the repo

**NSAP** — IGNOAPS (old age), IGNWPS (widow), IGNDPS (disability) — is the
central scheme that the Uttarakhand pensions sit on top of. States do not pay
*instead* of the centre; they **top up** the central share.

Two consequences, and the second is a defect waiting to happen:

- The central amounts (₹200/month under 80, ₹500/month at 80+, ₹300/month for
  widows) are a **central share, not what a worker receives.** Publishing ₹200
  as a benefit would understate the real payment badly, which is the same class
  of error as overstating it.
- Encoding IGNOAPS beside UK_OLD_AGE without an `exclusive_group` would count
  the same rupee twice — exactly the bug already fixed once in the engine and
  once in the dashboard. **Third occurrence, if we are careless.**

These need a phone call before anything is signed, not more reading. The
question is: *for an Uttarakhand applicant, is the ₹1,500 the state figure
inclusive of the central share, or additional to it?*

### 3. The widow-pension age bands do not meet

IGNWPS covers widows **40–59**. UK_WIDOW, as encoded, and the state pension
generally, pick up at 60 via the old-age route. A 35-year-old widow qualifies
for neither. That gap is real, it is the government's, and the right behaviour
is to say so plainly rather than let the bot return a bare "no".

---

## Priority queue

Ordered by *users helped per hour of your signing time*, which is the only
currency that matters now.

### Tier 1 — draft next, national, computable from questions we already ask

| Scheme | Why it ranks here | Primary source |
|---|---|---|
| **APY** (Atal Pension Yojana) | Structurally a twin of PM-SYM: age 18–40, savings/post-office account, not an income-tax payer. Guaranteed ₹1,000–₹5,000/month from 60. Every condition is already a question the bot asks. | `jansuraksha.gov.in/Files/APY/ENGLISH/APY.pdf` · `pfrda.org.in/schemes/atal-pension-yojana-apy` |
| **PM-JAY (70+)** | One question, ₹5 lakh family cover, explicitly income-blind. The single highest value-per-question entry available. | `nha.gov.in/PM-JAY` · Cabinet decision PIB `PRID=2053883` |
| **NSAP / IGNOAPS** | The floor under every state old-age pension. Needs the top-up call first and an `exclusive_group` with UK_OLD_AGE. | `nsap.nic.in/Guidelines/nsap_guidelines_oct2014.pdf` |
| **NSAP / IGNWPS** | Covers widows 40–59, the band the state scheme leaves open. | `nsap.nic.in/Guidelines/guidelines on IGNWPS 30sep09.pdf` |

### Tier 2 — national, needs one new intake question each

| Scheme | New question needed | Primary source |
|---|---|---|
| **NPS-Traders** | "Do you run a small shop or trade, with turnover under the limit?" Otherwise identical in shape to PM-SYM. | `maandhan.in` |
| **IGNDPS** | Disability status — a question we deliberately do not ask today. Adding it needs care: it is sensitive, and the scheme requires *severe or multiple* disability, which a self-report cannot establish. | `nsap.nic.in/Guidelines/dps.pdf` |
| **PM Vishwakarma** | Trade membership, from a fixed list of 18 traditional trades. Also has a five-year exclusion for anyone who took PMEGP / MUDRA / PM SVANidhi credit — an exclusion we would have to ask about honestly. | `pmvishwakarma.gov.in` · trade list at `/Home/TradeNames` |

### Tier 3 — gateways, no ₹ value of their own

| Scheme | Model as | Note |
|---|---|---|
| **PM-JAY (general)** | `value_basis = "gateway"` | SECC list membership. Send them to check; never guess. |
| **NFSA ration card** | `value_basis = "gateway"` | State-administered lists, same shape. |
| **PMJDY** | `value_basis = "gateway"` | A bank account is a *prerequisite* for PMJJBY, PMSBY and APY, so this is arguably the most useful gateway in the set. |

### Deliberately not queued

- **PM-KISAN** — land-owning farmers. Our user is a labourer, frequently
  landless. Low hit rate per question spent, and we already ask about land.
- **Sukanya Samriddhi, PPF, insurance products** — savings instruments, not
  entitlements. Different promise, different failure mode.
- **PMAY (housing)** — enormous, state-administered waitlists, and "eligible"
  means "may join a queue of years". The bot's ₹ framing would mislead badly.
- **BOCW boards** — genuinely high value for construction workers, but each of
  28 states runs its own board with its own rules. That is 28 research efforts,
  not one.

---

## The rule that governs all of this

`CLAUDE.md` rule 8: **accuracy over coverage. Three schemes correct beats twenty
approximate.**

Twenty drafted-but-unsigned files do not make the bot more useful — they make it
return UNKNOWN in twenty new places. Coverage grows when you sign, not when a
file appears. So the sequence is: draft with citations → you read the source →
`python3 -m sathi.review` → the scheme goes live.

At roughly 30–60 minutes of careful reading per scheme, Tier 1 is about three
hours of your time and would take the bot from seven schemes to eleven,
including the largest health scheme in the country for everyone over 70.

## Open questions that need a phone call, not a search

1. **Top-up or inclusive?** Is Uttarakhand's ₹1,500/month inclusive of the NSAP
   central share, or paid in addition to it? Decides whether IGNOAPS is a
   separate entitlement or the same rupee counted twice.
2. **IGNWPS in practice.** The guideline says 40–59 and BPL. Which BPL list does
   a district use in 2026 — the 2002 list the guidelines name, or a current
   substitute?
3. **PM-JAY 70+ enrolment.** Does a 70-year-old need a fresh Ayushman card, or
   does an existing family card cover them?

---

# State pensions for the six pilot states — research, 12 September 2026

`data/states.toml` marks six states `common = true`, which is where the pilot
runs and the only place state schemes are worth the research: **Uttarakhand,
Uttar Pradesh, Delhi, Haryana, Himachal Pradesh, Bihar.** Uttarakhand's two are
already live.

## What a state pension costs to add, which is more than a file

Every national scheme drafted tonight (APY, PMJAY_70) reuses questions the
intake already asks, so the file is the whole change. **State pensions do not.**
Each state sets its own income ceiling in rupees per year, and the intake holds
a monthly *band*, not a figure — `upto_5000` cannot establish "₹46,080 a year or
less". Uttarakhand solved this with a dedicated `uk_pension_income_or_bpl`
field, asked only of Uttarakhand residents.

So each state costs: a profile field, an intake question, state-gated skip
logic so nobody is asked about a pension in a state they do not live in, and
test coverage for both. That is code, not data, and it is the reason this is
queued rather than drafted at the same time as the national files.

**One generic `is_bpl` question would unlock several at once** — IGNOAPS,
IGNWPS, and any state pension that tests BPL status rather than a rupee figure.
That is the cheapest next step, and it should be designed once rather than five
times.

## Uttar Pradesh — researched, ready to draft

From the Department of Social Welfare's own page (not an aggregator), read
12 September 2026:

| Value | As stated |
|---|---|
| Pension | **₹1,000 per month**, paid quarterly |
| Age | **60 or above** |
| Income ceiling, rural | **₹46,080 per year** |
| Income ceiling, urban | **₹56,460 per year** |
| Apply | online, `sspy-up.gov.in` — application to disbursement |

Source: `samajkalyan.up.gov.in/en/article/old-age-pension-scheme`
(page last updated 4 September 2025).

**The rural/urban split is the problem, and it is not a small one.** The intake
has no rural/urban field and adding one is a real question with a real error
rate — many workers migrate seasonally and would answer differently in March
and October. Two defensible designs:

1. Test against the **rural** ceiling of ₹46,080, the stricter number, and say
   in the fail text that the urban limit is higher so someone near the line
   should still go and ask. This is the pattern `uk_old_age.toml` already uses
   where the department and myScheme disagree — resolve toward telling her to
   ask, never toward refusing her.
2. Ask rural or urban. More accurate in principle, one more question for
   everybody, and wrong whenever the answer is seasonal.

Option 1, on the same reasoning as the existing file: a wrong NO is a missed
entitlement, and the cost of being told "ask at the office" is far lower than
the cost of being told "no".

## The other four — blocked on sources, not on effort

| State | Status |
|---|---|
| **Delhi, Haryana, Himachal Pradesh, Bihar** | Not researched. Needs the same department-page pass as UP. |
| **Uttar Pradesh (widow)** | `sspy-up.gov.in` refused connections repeatedly, and myScheme's own detail tabs render no text to read. Not obtainable tonight by any route that would produce a citable figure. |

**Do not fill these from an aggregator.** This project has already been burned
once: `uk_widow.toml` rests on a myScheme page whose own "Official Website" link
points at a different scheme entirely, and that single weak citation is the
reason one of seven files carries a disclosure the other six do not.

Where the department's own page cannot be read, the honest output is a `"TODO"`
and an UNKNOWN verdict, not a plausible number.
