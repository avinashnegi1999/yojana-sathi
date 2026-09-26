# Pilot plan.

20–50 consenting adult workers. A protocol — not evidence that a pilot has happened.

> Prepared 8 September 2026. Recruitment, consent, worker testing and outcomes have **not** happened yet.

<br>

## The question.

Can workers finish a screening, understand its uncertainty, and use a source-checked sheet — without being misled into thinking a benefit is approved?

<br>

## Before the first participant.

1. ~~**Scheme verification.**~~ Done 9–10 September 2026, extended to ten schemes by 15 September. The five unsigned drafts return `UNKNOWN`. [How](history/VERIFICATION.md).
2. **Hindi review — not done.** Every Hindi string was drafted by a language model and has never been read by a native speaker. A mistranslated eligibility line costs a worker a day's wage just as surely as a wrong threshold, and the signature protects the numbers, not the words. Read the safety-critical strings aloud **before** the first participant. [Checklist](history/HUMAN_REVIEW_CHECKLIST.md).
3. **One partner.** A willing CSC or community organisation that can explain the purpose without promising government endorsement. Recruit about 20–50 adults from construction, domestic work, vending, transport and other informal work. Include Hindi speakers and people new to chat buttons. Record recruitment limits; don't claim the group is representative.
4. **Rehearse on a low-cost Android phone.** Confirm the live channel works and runs the reviewed scheme version. Telegram, the browser version, or a supervised local interface is enough for a first pilot; public WhatsApp needs its own approval.
5. **Run, fix, repeat.** Stop to fix serious failures. Ask participants to explain the result in their own words.
6. **Invite return visits** for next-step feedback. Report what was seen, with its limits and denominators.

**Participation must never affect** work, CSC service, benefits or payment. Recruit away from employers and queues. Declining must be as easy as agreeing. Never tie an incentive to a match, to sharing data, to positive feedback, or to applying.

<br>

## Consent, read aloud.

> "We are testing an independent tool that explains some government schemes. It does not approve benefits or submit an application. Taking part is your choice; you can stop without losing any service. Do not give us your name, Aadhaar, account number or copies of documents. With your agreement, the tool records anonymous session events and broad categories such as age band and occupation. Telegram or WhatsApp still handles messages and account identifiers under its own policies. We may note where the instructions were unclear, without recording your words or identity. Is it okay to continue?"

<details>
<summary><b>Hindi version — needs human review before use</b></summary>

<br>

> "हम एक अलग संस्था का बनाया साधन जाँच रहे हैं, जो कुछ सरकारी योजनाएँ समझाता है।
> यह सरकारी सेवा नहीं है। यह लाभ मंज़ूर नहीं करता और आवेदन जमा नहीं करता। भाग लेना
> आपकी इच्छा है। आप कभी भी रुक सकते हैं; इससे किसी सेवा पर असर नहीं पड़ेगा। हमें
> अपना नाम, आधार नंबर, खाता नंबर या काग़ज़ों की फोटो न दें। आपकी सहमति पर इसमें
> बिना पहचान वाली बातचीत की गिनती और उम्र का समूह तथा काम जैसी मोटी जानकारी
> दर्ज होगी। टेलीग्राम या व्हाट्सऐप अपने नियमों के अनुसार संदेश और खाते की जानकारी
> रखते हैं। हम बिना नाम लिखे यह नोट कर सकते हैं कि कौन-सी बात समझने में कठिन लगी।
> क्या हम आगे बढ़ें?"

</details>

- **Even after a "no",** the app records a minimal session-start and consent event. It stores no answers.
- **The app can't screen someone who declines logging.** Don't claim it can. If a person only wants to see the tool, offer a supervised `--no-db` demo.

<br>

## Never collected.

- **No** names, Aadhaar or UAN numbers, phone numbers, messaging handles, addresses, bank details, document images, recordings, personal screenshots or chat exports.
- **Don't ask to see Aadhaar** to check age. The app asks age for the rules; the log keeps only the band.
- **Don't copy answers** into facilitator notes.
- **Keep `FOLLOWUP_SALT` unset**, unless a follow-up design is separately explained and approved.
- **The end-of-chat "who is this for?"** (self, someone else, developer/reviewer) is anonymous self-report, not proof of occupation. Treat developer answers as testing. It is stored without a session id, so it **can't** filter screenings.

<br>

## Use the pilot link. Every time.

Hand out `t.me/YojanaSathiBot?start=csc` or `https://sathi.avinashnegi.com/?start=csc` — never the plain link. After consent, the session carries cohort `csc`:

```bash
python3 -m sathi.metrics.report --cohort csc --since <pilot start date> --out pilot.html
```

- Maintainer testing through the plain link has no cohort and never appears here.
- Terminal runs are left out of every report by default.
- A second, non-CSC partner uses `?start=pilot`, so the two are reported apart.

<br>

## Sheets and shared phones.

- The participant keeps their sheet. Facilitators keep no copies. A sheet without a name still holds sensitive answers.
- On a shared phone, clear the previous conversation before the next person. Explain that deletion on the platform's side may be incomplete — never promise Telegram or Meta will erase anything.

<br>

## During a session.

1. **Consent, language, then hand over the phone.** Read the screen neutrally if asked, and record "assisted" — not failure.
2. **Their own answers**, including "don't know". Never coach an answer that makes a scheme match. Let them correct or restart. The bot performs no real application or payment.
3. **At the recap:** are these answers right? **At the result:** "Does this mean the government has approved money?" and "What would you do next?" Record only correct / unclear / incorrect.
4. **Offer the sheet** and explain its limits. Record accepted, declined or couldn't open. Ask which question needs simpler words — note the question key, not their answer.

- **Completed session:** consent, intake, the result recap, and the closing state after accepting or declining the sheet. An all-`UNKNOWN` result can complete.
- **Actionable screening:** at least one result from a signed scheme, with a usable next step. Counted separately.
- Missing data is not a failed rule. `eligibility_evaluated` events alone don't prove anyone read or understood the result.

<br>

## Observation sheet.

A restricted local tally, outside Git. One row per observed visit.

| Language | Channel | Use (self-report) | Assisted? | First or repeat (self-report) | Finished? | All `UNKNOWN`? | Understood "not approval"? | Next step understood? | Sheet usable? | Error / question key |
|---|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | | |

No precise timestamps, free-text quotes, session ids or contact fields. Report totals only. Self-reported repeat visits don't track unique people, and neither can the app's random sessions.

<br>

## Measures.

| Measure | Definition |
|---|---|
| Completion | Completed observed sessions ÷ consenting attempts |
| Independent completion | Completed without help ÷ consenting attempts |
| Uncertainty understood | Correctly says screening isn't approval ÷ completed sessions asked |
| Actionable screening | At least one signed scheme with a usable next step ÷ completed sessions |
| Usable sheet | Opens and reads it, or asks for a usable assisted copy ÷ sheets accepted |
| Failures | Abandonment, repeated confusion, transport failure, wrong recap, privacy incident, misleading verdict — each counted separately |

**Targets, not results:** at least 80% completion and 90% understanding that screening isn't approval. These are decision thresholds, not proof of effect.

**Stop recruiting** on any invented benefit, gate bypass, leaked identifier, or instruction likely to cause harm — until it's investigated. `UNKNOWN` itself is not a bug.

<br>

## Follow-up.

- Invite a voluntary return to the same partner, or a fresh session. No phone numbers, no promised reminders.
- Ask only: did you try to apply, did you submit, do you report approval, do you report receiving it. Record totals by stage, as **self-reports** — nothing is independently confirmed.
- Count non-returners as neither success nor failure. Report the response rate, duplicate uncertainty and selection bias.

<br>

## Bugs and incidents.

- **A bug report holds:** version or commit, language, channel, question key, a fictional reproduction, expected vs actual, severity. No raw webhooks, chat screenshots or database rows.
- **A privacy incident:** stop collecting, restrict access, then write a sanitised report.

<br>

## Data.

- **Keep rehearsals out.** Use `--no-db` for demos. Start the pilot on a dedicated, restricted database and record its start date and version:

```bash
python3 -m sathi.metrics.report --db /absolute/path/to/pilot.db --out /absolute/path/to/private-impact.html
```

- **Before publishing,** review the totals and suppress groups under five. Never commit the database or an event export.
- **Keep money separate** as [`IMPACT.md`](IMPACT.md) sets out. Visits, screened sessions, applications and outcomes are different things.
- **Access and retention.** Before collecting anything, the pilot owner records who has access and for how long. Suggested: delete event-level pilot data and observation rows once checked totals exist, within 30 days of closing. A proposed policy — the software doesn't enforce it. No research or legal approval is claimed.
