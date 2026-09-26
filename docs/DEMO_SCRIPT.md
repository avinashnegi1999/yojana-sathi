# Demo script.

An honest walkthrough in two to three minutes. Real signed scheme data, fictional answers.

> Keep **"OFFLINE ENGINEERING PREVIEW — NOT A REAL WORKER"** on screen throughout. This is a script, not a recorded demo or proof that anything is live.

<br>

## Run it.

```bash
python3 -m sathi.main --preview telegram --no-db
python3 -m sathi.main --preview whatsapp --no-db
```

No token, nothing sent. `--no-db` keeps these sessions out of the impact numbers. The preview prints the buttons a channel would send — it is not a test of how a phone renders them.

<br>

## The golden path.

Type the number of the button. Only age is typed as a value. Re-run against the current flow on **26 September 2026**, in both languages — the same numbers work in each.

| Prompt | Type | Meaning |
|---|---|---|
| Language | `2` | English (`1` for Hindi) |
| Consent | `1` | Agree, for this fictional demo |
| All or choose | `1` | All signed schemes |
| State | `1` | Uttarakhand |
| Age | `30` | Typed — the only question without buttons |
| Income | `2` | Up to ₹5,000 a month |
| Bank account | `1` | Yes |
| Income tax | `2` | No |
| PF / ESIC | `2` | No |
| NPS | `1` | No NPS account |
| Unorganised work | `1` | Yes |
| Are you a woman? | `2` | No — skips the widow and Ujjwala questions |
| BPL household | `2` | No |
| Shop / trade | `2` | No |
| Schemes already held | `9` | None |
| Papers you have | `1`, `4`, `8` | Aadhaar, bank passbook, Next |
| Sheet | `1` | Yes |
| Rating | `8` | Typed |
| Suggestion | `1` | Skip |
| Who is this for? | `4` | Skip |
| Exit | blank line | End |

**Expect:**

- A recap of only the questions that were asked.
- **Four matches:** PMJJBY, PMSBY, PM-SYM, e-Shram.
- **"You pay"** on each scheme that costs money: ₹436 a year, ₹20 a year, and for PM-SYM a line pointing to the centre (English) or ₹55–₹200 a month (Hindi).
- A pension total that says each pension starts at its own age.
- The schemes that don't fit, by name. Their reasons are on the sheet.

<br>

## Show `UNKNOWN` on purpose.

Answer **Don't know** (`3`) to income tax. e-Shram and PM-SYM come back as "can't be sure", with the missing fact named: *income tax*.

**Don't type a state name** at the "all or choose" screen. It opens an old full route that screens the unsigned drafts as `UNKNOWN` and asks occupation, land and household size — which no button route does.

<br>

## Narration.

| Segment | Show | Say |
|---|---|---|
| Problem · 20 s | The README's problem figures | "India's unorganised sector had an estimated 43.99 crore workers in 2019–20. That is the population context, not our user count." |
| The worker · 45 s | The Hindi golden path, repetitive steps sped up openly | "Hindi or English, consent, short questions. Buttons work without a language model. EPFO/ESIC and NPS are asked separately because schemes treat them differently. The recap shows what was recorded." |
| Safety · 30 s | A "don't know" giving `UNKNOWN`, then `verified_by` in `data/schemes/` | "Compute first, narrate second. The rules decide, never the model. A missing answer stays unknown instead of becoming a guess. Until a named person signs a scheme, the engine won't say yes at all." |
| Sources · 30 s | One official link from a scheme file, `data/sources/official-text/`, `python3 -m sathi.sources` | "Every value traces to an official page, and the page is in the repository. This command re-reads the live pages and tells us the day a ministry changes a number. The sheet helps an application; it is not an approved one." |
| Channels and privacy · 25 s | The English WhatsApp preview, the architecture diagram | "Both channels run the same conversation and rules. Preview sends nothing and records nothing. Live metrics use coarse bands and random session ids — the platforms still see accounts and messages. This is not an anonymity claim." |
| Honest close · 15 s | The remaining human gates | "Passing checks and a deployment are not impact. What's left: human scheme and Hindi review, a voluntary worker pilot, an accessible recorded demo, and AgentFoundry eligibility." |

The 43.99 crore figure is a dated government estimate — the [Ministry of Labour's reply to Parliament, 24 July 2023](https://www.pib.gov.in/PressReleasePage.aspx?PRID=1942079). Never call it a census, or people proven unable to claim.

<br>

## Show the checklist without faking status.

Run `python3 tests/test_flow.py` and show two checks:

- `test_full_session_with_no_llm_key_reaches_a_pack`
- `test_unverified_scheme_never_produces_a_verdict_or_rupees`

Their `VERIFIED` / `STUBBED` fixtures are synthetic. Label the first **SYNTHETIC TEST SCHEME — NOT GOVERNMENT DATA**. It runs the real conversation, the missing-papers explanation and the sheet in a temporary folder. It does not prove any real value was checked by a person.

- Preview's document marker stands in for an upload. It is not a PDF, or proof a file rendered on a phone.
- Show file contents only if the code produced them, and label the data source.
- **Never** edit a real `verified_by`, swap test files into `data/schemes/`, or switch off the signature gate for filming.

<br>

## Before recording.

- [ ] Run `python3 check.py` on the commit being filmed. Keep the output.
- [ ] Rehearse with `--no-db`. Confirm "don't know" still shows `UNKNOWN`.
- [ ] Prepare the English preview at the same point, so the language switch is short. Say so if clips are cut together.
- [ ] Open the official source before filming. Hide personal tabs.
- [ ] Keep tokens, environment, chat handles, phone numbers, databases and real worker details off screen.
- [ ] Present any past AWS or Meta test-number evidence as past. Don't imply a new check happened.
- [ ] Put a video or live link in the submission only once it exists and has been tested.
