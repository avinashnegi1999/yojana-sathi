# Pilot plan — 20–50 consenting adult workers

Prepared **8 September 2026**. Recruitment, consent, worker testing and outcomes
have **not** been established by this audit. This is a practical protocol, not
evidence that a pilot has happened.

## Purpose and entry gates

Find whether workers can complete a screening, understand its uncertainty, and
use a source-checked next-step sheet without being misled about benefit approval.

Priorities:

1. ~~Finish [scheme verification](VERIFICATION.md)~~ — **done 9–10 September
   2026.** All seven schemes are signed off against their official pages and the
   bot returns real verdicts. This gate is cleared.

   **The remaining gate is [Hindi review](HUMAN_REVIEW_CHECKLIST.md), and it is
   not cleared.** Every Hindi string in this bot was drafted by a language model
   and has never been read by a native speaker. A worker acting on a mistranslated
   eligibility line loses a day's wages exactly as surely as she would on a wrong
   threshold, and the signature process that protects the numbers protects none
   of the words. Read the safety-critical strings aloud before the first real
   participant, not after.
2. Find one willing CSC/community organization that can explain the purpose
   without promising government endorsement. Recruit approximately 20–50 adults
   from construction, domestic work, vending, transport and other informal work.
   Include Hindi-preferring participants and people unfamiliar with chat buttons;
   record recruitment limitations rather than claiming representativeness.
3. Rehearse on a low-cost Android phone. Confirm the selected live channel works
   and its stored scheme version matches the reviewed version. Public WhatsApp
   requires its own approval/setup; Telegram or a supervised local interface is
   sufficient for an initial pilot.
4. Run voluntary screenings, fix serious failures before continuing, and ask
   participants to explain the result in their own words.
5. Invite voluntary return visits for next-step feedback; report observations
   with their limitations and denominators.

Participation must not affect employment, CSC service, access to benefits or
payment. Recruit away from employer pressure and service queues. Declining must
be as easy as accepting. Do not tie incentives to successful screening, sharing
personal data, giving positive feedback or applying for a scheme.

## Consent to read aloud

English draft:

“We are testing an independent tool that explains some government schemes. It
does not approve benefits or submit an application. Taking part is your choice;
you can stop without losing any service. Do not give us your name, Aadhaar,
account number or copies of documents. With your agreement, the tool records
anonymous session events and broad categories such as age band and occupation.
Telegram or WhatsApp still handles messages and account identifiers under its
own policies. We may note where the instructions were unclear, without recording
your words or identity. Is it okay to continue?”

Hindi draft — **requires human review before use**:

“हम एक अलग संस्था का बनाया साधन जाँच रहे हैं, जो कुछ सरकारी योजनाएँ समझाता है।
यह सरकारी सेवा नहीं है। यह लाभ मंज़ूर नहीं करता और आवेदन जमा नहीं करता। भाग लेना
आपकी इच्छा है। आप कभी भी रुक सकते हैं; इससे किसी सेवा पर असर नहीं पड़ेगा। हमें
अपना नाम, आधार नंबर, खाता नंबर या काग़ज़ों की फोटो न दें। आपकी सहमति पर इसमें
बिना पहचान वाली बातचीत की गिनती और उम्र का समूह तथा काम जैसी मोटी जानकारी
दर्ज होगी। टेलीग्राम या व्हाट्सऐप अपने नियमों के अनुसार संदेश और खाते की जानकारी
रखते हैं। हम बिना नाम लिखे यह नोट कर सकते हैं कि कौन-सी बात समझने में कठिन लगी।
क्या हम आगे बढ़ें?”

Explain that the application records minimal session-start/consent events even
when consent is declined; it does not then store profile answers. Offer a
`--no-db` supervised demonstration if the person only wants to see the tool.
The current consent flow does not offer a complete screening after declining
its logging consent. Do not claim that it does.

## Information never collected for this pilot

No names, Aadhaar/UAN numbers, phone numbers, messaging handles, exact address,
bank details, document images, recordings, personal screenshots, or raw chat
exports. Do not ask to see Aadhaar to establish age. The app asks age for rules;
the event log should retain only its band. Do not copy the transient profile
into facilitator notes. Keep `FOLLOWUP_SALT` unset for the pilot unless a
separately explained and approved follow-up design is adopted.

A participant may hold their own sheet; facilitators do not retain copies. A
sheet still includes sensitive answers even when it has no name. On shared
devices, clear the previous conversation before another person starts and
explain that channel-side deletion may be incomplete. Do not promise erasure
of Telegram/Meta records.

## Procedure and completion definition

1. Explain consent, choose language, then let the participant operate the phone.
   If requested, read the visible text neutrally; record “assisted”, not failure.
2. Ask them to use their own answers, including “don't know” where offered.
   Do not coach an answer that makes a scheme match. Let them correct mistakes
   or restart. No real application or payment is performed by the bot.
3. At the answer recap, ask whether the recorded answers are correct. At the
   result, ask: “Does this mean the government has approved money?” and “What
   would you do next?” Record only correct/unclear/incorrect understanding.
4. Offer the sheet and explain its source/verification limits. Record whether
   it was accepted, declined or could not be opened. Ask which question needs
   simpler language, using the question key rather than their personal answer.

A **completed screening session** has affirmative consent, finishes intake and
the result recap, and reaches the closing state after accepting or declining
the sheet. An all-UNKNOWN result can complete the interaction; count it
separately from an **actionable screening**, which has at least one result from
a human-verified scheme with a usable next step. Missing data is not a failed
rule evaluation. Database `eligibility_evaluated` events alone do not prove the
participant read or understood the result.

## Minimal observation sheet

Keep an access-restricted local tally outside Git. One row per observed visit:

| Language | Channel | Assisted? | First/repeat visit (self-report) | Finished? | All UNKNOWN? | Understood no approval? | Next step understood? | Sheet usable? | Error code/question key |
|---|---|---|---|---|---|---|---|---|---|
| blank | blank | blank | blank | blank | blank | blank | blank | blank | blank |

Do not include timestamps precise enough to match a person to a chat, free-text
worker quotes, session IDs or contact fields. Use aggregate counts in the
submission. Self-reported repeat visits are not reliable unique-user tracking;
the app's random sessions cannot establish unique workers.

## Measures and stop conditions

| Measure | Numerator / denominator or definition |
|---|---|
| Completion | Completed observed sessions / consenting attempts |
| Independent completion | Completed without operator assistance / consenting attempts |
| Uncertainty understood | Correct explanation that screening is not approval / completed sessions asked |
| Actionable screening | At least one reviewed scheme with a usable next step / completed sessions |
| Usable sheet | Participant can open/read it or requests a usable assisted copy / sheets accepted |
| Failures | Abandonment, repeated confusion, transport failure, wrong answer recap, privacy incident, misleading verdict; report each count separately |

Proposed usability targets, **not achieved results**: at least 80% completion
and 90% understanding that screening is not approval. These are pilot decision
thresholds, not proof of effectiveness or statistical generalizability. Any
invented benefit, gate bypass, leaked identifier or instruction likely to cause
harm stops recruitment until investigated. UNKNOWN itself is not a bug.

## Follow-up, bugs and reporting

Invite participants to return voluntarily to the same partner or start a fresh
session. Do not collect phone numbers or promise automated reminders. Ask only
whether they attempted an application, submitted it, report approval, or report
receipt. Record aggregate **self-reports** by stage; no claim is independently
confirmed unless a separately consented verification process actually exists.
Do not count non-returners as either successes or failures. Report the follow-up
response denominator, duplicate uncertainty and selection bias.

A bug report contains version/commit, language, channel, question key, a
fictional reproduction, expected/actual behavior and severity. No raw webhook,
chat screenshot or database rows. For a privacy incident, stop collection and
restrict access before writing a sanitized report.

Keep rehearsals out of the pilot database. Use `--no-db` for demos; start the
pilot with a dedicated restricted DB path and record its start date/version.
Generate a report with `python3 -m sathi.metrics.report --db /absolute/path/to/pilot.db --out /absolute/path/to/private-impact.html`.
Review aggregates before publication and suppress groups below five. Never
commit the database or event export. Keep monetary categories separate using
[IMPACT.md](IMPACT.md); report observed visits, screened sessions, applications
and outcomes as different things.

Before collecting anything, the pilot owner records who has access and a
retention period. Suggested pilot policy: delete event-level pilot data and
observation rows once checked aggregates are prepared, within 30 days of pilot
closure. This is a proposed operating policy, not a claim that software enforces
automatic deletion. No separate research or legal approval is claimed here.
