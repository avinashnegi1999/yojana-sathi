# Yojana Sathi — submission draft

Prepared **8 September 2026**. Official form and rubric rechecked **9 September
2026** against codeforindia.org/hackathon and the submission issue template in
karlmehta/code-for-a-billion. Not submitted. Replace the explicit evidence
placeholders only with observed facts.

## Sign-off status, 9 September 2026

**PMJJBY, PMSBY, PMUY and the Uttarakhand old-age pension are signed off and
giving real answers.** Avinash Negi read
both Department of Financial Services FAQs in full and confirmed every encoded
value on 9 September 2026; each file names him in `verified_by`.

The other three schemes remain unsigned and answer "I could not check this yet".
Do not describe this project as screening workers against seven schemes. Four
schemes screen; three collect the answers and tell the worker what to ask at the
centre. That distinction has to survive into the demo video and the problem
statement unchanged — a judge will try it.

## What the official form actually asks for — rechecked 9 September 2026

Read this before writing any more of the draft below; two of these were not
what we assumed.

1. **`Built using AgentFoundry (AF), the official IDE` is a REQUIRED checkbox.**
   Not a preference, not a tie-breaker — the submission cannot be filed without
   ticking it. Our question about whether continued development in AF counts
   for a project that started outside it
   ([discussion #13](https://github.com/karlmehta/code-for-a-billion/discussions/13))
   is still **Unanswered, 0 comments**, 24 hours after it was asked.
   **This remains the single hard blocker, and it is not a code problem.**
2. **Scale and severity of the problem is 50% of the score.** The form says so
   in the field description: *"How many citizens face this problem, and what is
   the human suffering or economic loss it causes? Use numbers/sources where you
   can. (Judged — 50% of your score.)"* Half the marks are for the Problem
   section of this document, with sourced numbers. That is a writing and
   research task, not a build task, and it is currently the largest available
   gain.
3. **Deployment and impact data is 25%** — as previously understood — but the
   field is marked `required: false`. *"Strongest submissions have field data."*
   So the 5-weeks-of-real-usage plan still matters for the marks, but a missing
   impact section does not block filing.
4. **The track dropdown does not contain "Livelihood for the Uneducated".** The
   options are Agriculture, Health, Education, Financial Inclusion, Governance,
   Climate, Other. The website's ten impact areas *do* list "Livelihood for the
   Uneducated — skill matching, informal-sector income, micro-entrepreneurship,
   **benefits access**", which is exactly this project. **Ask the organisers
   which value to select**, or choose Other and name the impact area in the
   problem statement. Do not silently file under Financial Inclusion.
5. **A working demo URL is required** — live app or video. The Telegram bot link
   is a live app, but a judge cannot see a real screening result today because
   no scheme is signed, so the video should show `/demo` and explain the gate.
6. Public repo with a README containing setup steps — already satisfied.

Dates confirmed on the site: build window 15 August – 15 November 2026, winners
announced 5 December 2026.

## Problem

Unorganised workers need understandable explanations of scheme criteria and
application requirements. India had about **43.99 crore unorganised workers in
2019–20**, according to the Economic Survey figure cited in a Ministry of Labour
parliamentary reply. This establishes the scale of the target population, not
the number of workers with unmet eligibility needs or the project's reach.
[Official source, 24 July 2023](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1942079).

## Why this matters

Government infrastructure already reaches a large population: e-Shram reported
over **31.48 crore registrations as of 26 January 2026**, with 14 central schemes
integrated or mapped. The Ministry also describes assisted registration through
CSCs and other channels. Yojana Sathi proposes an additional conversational
route to understanding a few schemes; it does not claim government portals lack
Hindi or that registration equals receiving benefits.
[Official source, 2 February 2026](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2222263&reg=3&lang=2).

The cost and frequency of confusing applications for our pilot population have
not yet been measured. We will test whether workers understand the result and
their next step before claiming improved access or reduced wasted trips.

## Target users

Adult unorganised workers who prefer Hindi or English, including construction
workers, domestic workers, vendors, drivers and others in informal work. The
initial focus is assisted or self-directed screening with a local partner.
The intended track is **Livelihood for the Uneducated**; we do not assume every
worker is uneducated or unable to use government services.

## Solution

Yojana Sathi asks a small set of questions, reads the answers back, evaluates
source-backed Python rules, and explains what can and cannot be concluded.
Where a human-verified scheme supports a result, it can provide a document
checklist and application directions. Current scheme files remain unsigned,
so they return UNKNOWN and provide questions to ask instead of a false promise.

## Why conversational

Short questions, Hindi/English buttons, typed age/state input and confirmed
occupation classification reduce the amount a person must type. Telegram and
WhatsApp use the same conversation. These are design choices to test with real
workers; accessibility and comprehension improvements are not yet measured.
No claim of universal literacy independence or production voice assistance is
made.

## Why deterministic rules

Eligibility is consequential: a plausible invented threshold could send someone
to the wrong office or create false expectations. **Compute first, narrate
second** keeps rules, benefit categories and official sources auditable. The
language model cannot decide eligibility, invent ₹ amounts or override UNKNOWN.
Optional language assistance is separate; the button-based flow works without
an LLM key.

## Architecture

Python 3.11+ with a standard-library runtime. Channel adapters handle Telegram
polling and WhatsApp signed webhooks; both invoke the shared conversation and
three-valued rule engine. TOML holds scheme data and localized content.
Application sheets are generated in memory. Consent-gated SQLite events support
aggregate reporting. Offline channel preview exercises rendering without
sending messages. See [ARCHITECTURE.md](ARCHITECTURE.md).

## Safety

Unsigned government data is a runtime gate, not merely a README warning.
Missing information stays unknown. Human review owns final source sign-off;
the program does not auto-submit government applications. The event schema
restricts profile data to broad categories under random session IDs. Account
identifiers still exist transiently for message routing, and messaging providers
retain their own records. Packs contain sensitive answers and must be handled
privately. See [VERIFICATION.md](VERIFICATION.md) and [IMPACT.md](IMPACT.md).

## Deployment

The repository records AWS EC2 deployment and links
[@YojanaSathiBot](https://t.me/YojanaSathiBot). WhatsApp code and a historical
Meta test-number trial are documented; no public production WhatsApp number is
established. On **8 September 2026**, a read-only SSH check confirmed that
`sathi`, `sathi-whatsapp` and `caddy` were active; both application services
reported running. This establishes process status, not successful message
delivery or independent judge access. No new phone test was performed.
`python3 check.py` also passed locally at commit
`e4a10e7be39b85a0ac3c2b19bbcfff96788812f0`. Earlier offline validation is reported
in [HACKATHON_READINESS.md](../HACKATHON_READINESS.md).

Before submitting, fill: **[actual deployed commit, date checked, independent
judge-access test and sanitized evidence link]**.

## Impact

**No verified real-worker impact result is available for this draft.**

| Evidence | Fill only after it exists |
|---|---|
| Pilot recruitment and consent | [partner/approach, participant consent method, observed visit denominator] |
| Screening | [completed sessions, all-UNKNOWN subset, assisted subset, reporting period] |
| Understanding | [correct explanations that screening is not approval / completed sessions asked] |
| Applications | [attempted, submitted, approved and received, separately; self-report or verification method] |
| Outcomes | [observed change and limitations; no causal claim without a suitable study] |

Tests, previews, sessions and unique workers are different quantities. Potential
pension and contingent insurance cover are not money received and cannot be
added into a single impact amount. Follow [PILOT_PLAN.md](PILOT_PLAN.md) and
[IMPACT.md](IMPACT.md); remove empty promises before final submission.

## Repository

https://github.com/avinashnegi1999/yojana-sathi — public, Apache-2.0. CFI
organization contribution/acceptance still requires owner action and organizer
process clarification.

## Demo

**[2–3 minute video URL or independently checked live demonstration link]**

[DEMO_SCRIPT.md](DEMO_SCRIPT.md) supplies an honest path using UNKNOWN production
data and clearly labeled synthetic tests. A script is not a completed recording.

## AgentFoundry

Initial development occurred outside AgentFoundry. No verified subsequent AF
development or organizer approval of importing this existing repository has
been established. **Do not check the required AF confirmation yet.**

After written clarification and actual work, replace this paragraph with:
**[organizer guidance reference; exact task performed in AF; dates; commit IDs;
optional redacted evidence link; truthful distinction from earlier development]**.
See [AGENTFOUNDRY_MIGRATION.md](AGENTFOUNDRY_MIGRATION.md).

## Final form preparation

Team/project: **Avinash Negi — Yojana Sathi**. Member: **Avinash Negi
(@avinashnegi1999)**. Confirm these owner-supplied details before publication.
Contact: **[owner-selected public contact email]**.

Map the material above to the current form's problem, solution, scale/severity,
repo/demo and impact fields. Confirm which dropdown maps to the livelihood
track. Review registration and open-source contribution terms yourself. Follow
[HACKATHON_REQUIREMENTS.md](HACKATHON_REQUIREMENTS.md); this draft is not evidence
of submission or acceptance.
