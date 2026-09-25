# Demo script — honest 2–3 minute walkthrough

Prepared **8 September 2026**. This script is not a recorded demo or proof of
live availability. It uses the shipped, human-signed scheme data and fictional
answers.
Keep **“OFFLINE ENGINEERING PREVIEW — NOT A REAL WORKER”** visible throughout.

## Golden path, tested locally

From the repository root run either:

- `python3 -m sathi.main --preview telegram --no-db`
- `python3 -m sathi.main --preview whatsapp --no-db`

No channel token or network send is needed; `--no-db` keeps these synthetic
sessions out of impact data. The renderer prints the buttons/lists that the
channel would send, but terminal preview is not a real Android rendering test.

Enter one answer per prompt. Numbers select visible buttons; only the age is
typed. Re-run against the current flow on **25 September 2026** in both
languages (the same numbers work in each; use `1` instead of `2` at the first
prompt for Hindi).

| Prompt | Input | Meaning |
|---|---|---|
| Language | `2` | English (`1` for Hindi) |
| Consent | `1` | Agree in this fictional demonstration |
| All or choose | `1` | All verified schemes |
| State | `1` | Uttarakhand |
| Age | `30` | Typed — the one question with no buttons |
| Income | `2` | Up to ₹5,000 a month |
| Bank account | `1` | Yes |
| Income tax | `2` | No |
| PF / ESIC | `2` | No |
| NPS | `1` | No NPS account |
| Unorganised work | `1` | Yes |
| Are you a woman? | `2` | No — skips the widow and Ujjwala follow-ups |
| BPL household | `2` | No |
| Shop / trade | `2` | No |
| Schemes already held | `9` | None of these |
| Papers you have | `1`, `4`, `8` | Aadhaar, bank passbook, then Next |
| Sheet offer | `1` | Yes |
| Rating | `8` | Typed |
| Suggestion | `1` | Skip |
| Who is this for? | `4` | Skip |
| Exit | blank line | End preview |

Expected: an answer recap listing only the questions asked, then four matches
(PMJJBY, PMSBY, PM-SYM, e-Shram). Each scheme that costs money shows **"You
pay"** (₹436 a year, ₹20 a year, and for PM-SYM a line that points to the centre
in English, or the ₹55–₹200 a month text in Hindi). The pension total says each
pension is paid only from its own starting age. The ineligible list gives each
authored reason.

**Do not type a state name at the "All verified schemes / Choose" screen.** It
opens the legacy full route that existed for deploy-time callbacks: it screens
the unsigned drafts as UNKNOWN and asks occupation, land and household size,
which no button route does. To show UNKNOWN deliberately, answer **Don't know**
to the income-tax question instead: e-Shram and PM-SYM come back UNKNOWN with
the missing fact named.

## Narration and shots

| Segment | Show | Suggested narration |
|---|---|---|
| Problem, about 20 seconds | README problem citation | “India's unorganised sector had an estimated 43.99 crore workers in 2019–20. Yojana Sathi is testing a simpler way to understand scheme eligibility and next steps. That national estimate is the population context, not our user count.” |
| Worker interaction, about 45 seconds | Hindi golden path; speed up repetitive intake transparently | “The worker chooses Hindi or English, gives consent, and answers short questions. Buttons work without a language model. We ask EPFO/ESIC and NPS separately because government schemes treat them differently. The recap shows what was recorded.” |
| Safety, about 30 seconds | A "don't know" answer producing UNKNOWN, then `verified_by` in `data/schemes/` | “Compute first, narrate second. Python rules decide, never the model. A missing answer stays unknown rather than becoming a guess. Every file names the human who checked it against the official page, and until it does the engine refuses to say yes at all.” |
| Sources and application help, about 30 seconds | One official link from a scheme TOML; `data/sources/official-text/`; `python3 -m sathi.sources` | “Every value traces to an official page, and the page itself is in the repository so you can audit a rule without leaving it. This command re-reads the live pages and tells us the day a ministry changes a number we have already promised. The sheet is an application aid, not an approved application.” |
| Channels and privacy, about 25 seconds | English WhatsApp preview list, architecture diagram | “Both adapters invoke the same conversation and rule engine. Preview sends nothing and records no events. Live metrics use coarse categories and random session IDs; the platforms still handle account identifiers and messages. This is not an end-to-end anonymity claim.” |
| Honest close, about 15 seconds | Readiness human gates | “Software checks and a deployment record are not worker impact. The remaining gates are human scheme and Hindi review, a voluntary worker pilot, an accessible recorded demo and AgentFoundry eligibility confirmation.” |

The problem figure is a dated government estimate, confirmed in the
[Ministry of Labour parliamentary reply, 24 July 2023](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1942079).
Do not describe it as a current census or as people proven unable to claim benefits.

## Showing the checklist without falsifying production status

Run `python3 tests/test_flow.py` and show the named
`test_full_session_with_no_llm_key_reaches_a_pack` and
`test_unverified_scheme_never_produces_a_verdict_or_rupees` checks with the
`VERIFIED` / `STUBBED` fixture definitions in that file. Label the first
**SYNTHETIC TEST SCHEME — NOT GOVERNMENT DATA**. It exercises the real
conversation, missing-document explanation and pack generation in a temporary
directory. This does not prove the source values have been human-verified.

Preview's document marker represents a stubbed upload. It is not a downloaded
PDF or evidence that an attachment rendered on a phone. The core produces HTML;
the WhatsApp adapter renders its supported text attachment. Show actual file
contents only if generated by the code, and label the data source. Do not edit
production `verified_by`, swap fixture files into `data/schemes`, or disable the
gate for filming.

## Recording checklist

- [ ] Run `python3 check.py` on the commit being filmed; retain actual output.
- [ ] Rehearse the path with `--no-db` and verify a "don't know" answer still
      produces a visible UNKNOWN.
- [ ] Prepare English preview at the same state so the language comparison is
      short; explain if recordings are cut together.
- [ ] Open the official source before filming; hide personal browser tabs.
- [ ] Keep terminal environment, tokens, chat handles, phone numbers, local
      databases and real worker information off screen.
- [ ] State any historical AWS/Meta-test-number evidence as historical; do not
      imply this local audit performed a new cloud or phone verification.
- [ ] Add a tested judge-accessible video/live URL to the submission only after
      it exists. No demo URL has been invented here.
