# Scheme Sathi (योजना साथी)

**A conversation, in Hindi or English, that tells an unorganised worker which
government schemes they are entitled to, what each is worth in ₹, and where to
walk to claim it.**

Live on Telegram: [@YojanaSathiBot](https://t.me/YojanaSathiBot)

> **Status — read before you use it on anyone.**
> The software is complete and tested end to end. All three scheme files are
> filled from official sources — the PMSBY rules PDF on `jansuraksha.gov.in`,
> the PM-SYM FAQ and contribution chart on `maandhan.in`, the e-Shram FAQ on
> `eshram.gov.in` — with a deep link on every single value.
>
> **Those values have not yet been confirmed by a second pair of eyes.**
> `verified_by` in each file says `unconfirmed — PENDING HUMAN VERIFICATION`,
> and a test keeps that admission in place until a maintainer signs off. A wrong
> threshold sends someone on a day-long trip that costs them a day's wages, so
> please do not screen a real worker before that review.

---

## The problem

India's unorganised sector is roughly **44 crore workers** — about **93% of the
total workforce** — earning around **₹6,688/month** on average. Construction
labourers, domestic workers, drivers, street vendors, farm labour, shop staff.

The welfare infrastructure exists. Over **31.38 crore** unorganised workers are
registered on e-Shram, with **14 central schemes** integrated (Nov 2025).

<!-- TODO: deep-link each figure above to its official source. Every other
     number in this project carries a citation; these should not be the
     exception just because they sit in the pitch. -->

## The gap

It is not eligibility. Workers are already entitled. The blockers are:

1. They do not know which schemes exist or apply to them.
2. Rules are scattered, in English, in bureaucratic language.
3. The paperwork is confusing, and **a failed trip to a Common Service Centre
   costs a day's wages** — so the second attempt often never happens.

A worker legally entitled to a pension or an accident cover simply never claims it.

## What it does

Asks a short set of plain questions, answerable entirely by tapping buttons.
Runs the answers through a deterministic rule engine. Says which schemes they
qualify for **and why**, in their language. Produces a document checklist and a
one-page sheet they can carry to a centre, then tells them exactly where to go.

Where it cannot be sure, it says so and hands over a question to ask a human,
instead of guessing.

## Why not just myScheme?

`myScheme.gov.in` and UMANG already publish scheme data and eligibility
matching, and this project does not try to replace them. Scheme Sathi is
**last-mile delivery on top of that work**:

> myScheme is an English web form. It assumes literacy, a browser, and a user
> who knows what "land holding in hectares" means. Scheme Sathi is a
> conversation on a ₹6,000 phone that ends in a filled checklist and an address
> to walk to.

## Impact

<!-- ! Populated from real deployment data only, by
     ! `python3 -m sathi.metrics.report`. No projections, no estimates, no
     ! "potential reach". If a number is not in the event log it does not go on
     ! this page. -->

_Not yet deployed. This section stays empty until it can be filled from the
event log._

Two ₹ figures are reported, never one. An annual pension (PM-SYM, ₹36,000/year)
and an accident cover (PMSBY, ₹2,00,000 paid only on a claim) are different
kinds of money; adding them would overstate what a worker actually receives by
roughly six times.

Methodology, and what each number does **not** claim:
[`docs/IMPACT.md`](docs/IMPACT.md).

## How eligibility is decided

**Deterministically, never by a language model.**

- Rules live in [`data/schemes/*.toml`](data/schemes/) — plain text, one file
  per scheme, readable and editable without knowing Python.
- Every threshold carries a `source_url` deep-linking the official page it came
  from, and a `verified_on` date. You can audit one rule in 30 seconds.
- An unresearched value is the literal string `"TODO"`. The loader detects it
  and the engine returns `UNKNOWN` — "we could not check this, ask at the
  centre" — rather than guessing.
- Absence is a finding too. The PMSBY draft had placeholders for an income
  threshold and an income-tax exclusion; the official rules contain neither, so
  both were **deleted rather than filled**. An unsourced exclusion turns
  eligible people away, which is the same failure as a guessed threshold.
- A language model is optional and stays outside the engine entirely. It maps
  free text to a category — always confirmed by the worker before anything is
  recorded — and rephrases text a human wrote. It never sees a threshold and
  never produces a ₹ figure or a verdict.
- With no API key the whole thing works on buttons and templated text, with
  identical results. That is a tested configuration, not a degraded one.

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Privacy

No Aadhaar number. No name. No phone number. **Those fields do not exist in the
profile**, so they cannot be stored by accident.

The profile lives in process memory for one session and is discarded. The event
log holds counts and coarse bands only — state, age band, occupation, income
band — under a random per-session id that is not derived from any messaging
account, so two sessions by the same worker are not linkable. Dashboard
aggregates covering fewer than 5 people are suppressed.

`tests/test_privacy.py` drives every event type through the log and then asserts,
column by column, that nothing else survived.

## Languages

Hindi and English, chosen by the worker before anything else. The engine is not
bilingual and never will be — verdicts are identical in both, only the words
change, and a test asserts it. Scheme rules carry both languages with the same
citation.

## Run it yourself

```bash
git clone <repo> && cd scheme-sathi

python3 check.py                     # every self-check and test, nothing to install
python3 -m sathi.main                # one screening in the terminal, buttons only
python3 -m sathi.main --telegram     # the bot (needs TELEGRAM_TOKEN)
python3 -m sathi.metrics.report --out impact.html   # the impact dashboard
```

Requires Python 3.11+ (uses stdlib `tomllib`). **There are no third-party
dependencies** — not in the app, not in the tests, not in the image.

As a container:

```bash
docker build -t scheme-sathi .
docker run -e TELEGRAM_TOKEN=... -v sathi-data:/data scheme-sathi
```

`DB_PATH` must point at a mounted volume. A free-tier container that loses its
disk on restart loses the event log, and every impact number with it.

Optional, all off by default and all tested in the off state:

| Variable | Effect when set |
|---|---|
| `LLM_API_KEY` | Free-text intake maps to a category, always confirmed by the worker; text is rephrased. Verdicts are unchanged. |
| `TTS_CMD` | Replies also arrive as an audio note, e.g. `espeak-ng -v hi -w {out} {text}`. |
| `FOLLOWUP_SALT` | Enables the 14-day follow-up, storing a salted hash of the channel id in a table that cannot be joined to the event log. |

## Bot commands

| Command | What it does |
|---|---|
| `/start` | Begin, or start over |
| `/language` | Switch हिंदी ↔ English, keeping answers already given |
| `/schemes` | Every scheme, its official source URL, and when it was checked |
| `/privacy` | What is stored, what is never asked |
| `/about` | What this is — and plainly, that it is not a government service |
| `/help` | The command list |
| `/clear` | Delete this conversation's messages |
| `/clearall` | Delete everything reachable from the last 48 hours |
| `/cancel` | Drop the profile now and end |

## Tests

```bash
python3 check.py
```

15 module self-checks and 5 test files, no framework and nothing to install.
Worth knowing about two of them:

- `tests/test_privacy.py` — the reason the privacy claim above is defensible
  rather than aspirational.
- `tests/test_all_paths.py` — presses **every button at every reachable screen**
  in both languages (948 paths, 258 completed sessions), opens every generated
  sheet, runs every path through a real event log, drives every command through
  the channel adapter, and fuzzes the typed questions. It asserts its own
  coverage counters, because a green test that never reached the thing it checks
  is worse than no test.

## Add a scheme

You do not need to write Python. Copy
[`data/schemes/_TEMPLATE.toml`](data/schemes/_TEMPLATE.toml), fill it from
official sources, and cite every value. See
[`docs/SCHEME_AUTHORING.md`](docs/SCHEME_AUTHORING.md).

**Contributions without a `source_url` and `verified_on` per value are closed.**
That is not bureaucracy: an uncited threshold is indistinguishable from a
guessed one, and a guess costs a worker a day's wages.

## Licence

Apache-2.0. See [LICENSE](LICENSE).

Built for **Code for a Billion — Bharat Agentic-AI Hackathon 2026**
(Code for India), track "Livelihood for the Uneducated".
