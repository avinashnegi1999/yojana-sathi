# Scheme Sathi (योजना साथी)

**A conversation, in Hindi or English, that tells an unorganised worker which
government schemes they are entitled to, what each is worth in ₹, and where to
walk to claim it.**

Live on Telegram: [@YojanaSathiBot](https://t.me/YojanaSathiBot)

WhatsApp speaks the same conversation from the same rule engine. The channel is
built and verified end to end against Meta's test number — a real phone, a full
screening, the same Hindi — but it is not yet live on a public number.

> **Status — read before you use it on anyone.**
> The software is complete, tested end to end, and **live**. All seven scheme
> files are filled from official sources with a deep link on every single value:
> PMJJBY and PMSBY (`financialservices.gov.in`), PM-SYM (`maandhan.in` and
> `labour.gov.in`), e-Shram (`eshram.gov.in`), PMUY (`pmuy.gov.in`), and the
> Uttarakhand old-age and widow pensions (`socialwelfare.uk.gov.in`).
>
> **All seven are signed off.** Avinash Negi read each official page in full on
> 9–10 September 2026 and confirmed every encoded value against it; `verified_by`
> in each file names him. The bot gives real verdicts, real ₹ figures and a place
> to walk to.
>
> That signature is enforced, not merely recorded. Until a named human signs a
> file, the rule engine returns `UNKNOWN` for that scheme to every worker,
> contributes ₹0 to every number on the dashboard, and says so at startup — and
> `tests/test_schemes.py` fails the build if this README and the data ever
> disagree about which schemes are signed. A wrong threshold sends someone on a
> day-long trip that costs them a day's wages.
>
> **One file is thinner than the others, and the repository says so.** The
> Uttarakhand widow pension's department page states no amount at all. The
> ₹1,500 comes from myScheme — whose own "Official Website" link for that scheme
> points at a *different* scheme. It is signed on the maintainer's judgement, and
> `data/schemes/uk_widow.toml` records exactly that in its header. Two questions
> to the SSP helpline would settle it.
>
> Where a source refuses people without saying so anywhere official, this project
> declines to. Both Uttarakhand pensions collect "are you already drawing another
> pension?" and **tell the worker to ask at the office** rather than refusing her
> on it, because only myScheme states that bar and a wrong NO is a pension nobody
> claims.
>
> The full source comparison, including what could *not* be resolved, is in
> [`docs/SOURCE_REVIEW_2026-09-09.md`](docs/SOURCE_REVIEW_2026-09-09.md); the
> edge-case audit run before any of this reached a real person is in
> [`docs/PRE_DEPLOY_AUDIT_2026-09-10.md`](docs/PRE_DEPLOY_AUDIT_2026-09-10.md).
>
> **To sign or unsign a scheme:** `python3 -m sathi.review PMJJBY`. It prints
> every value in the file next to the URL it came from, you open that page, and
> if it all matches you type the scheme code and your name. It writes exactly two
> lines and re-validates the file afterwards, so a signature can never carry a
> data change in with it. `--unsign` puts it back. Nothing in that tool checks
> anything for you; it puts the values and the source on one screen so you can.

---

## The problem

India's unorganised sector is **43.99 crore workers** — the Economic Survey
2021-22 figure for 2019-20, quoted by the Ministry of Labour & Employment in
Parliament.[^1] The last full survey to split the workforce found **82.7% of it
outside the organised sector** — 39.14 crore of 47.41 crore employed persons.[^2]
Construction labourers, domestic workers, drivers, street vendors, farm labour,
shop staff.

What they earn sets the price of a wasted day. In the Government's own 2025
labour force survey, a casual labourer earned **₹455 a day if male and ₹315 if
female**; a self-employed worker earned **₹17,914 a month if male and ₹6,374 if
female**.[^3]

The welfare infrastructure exists. **31.48 crore** unorganised workers were
registered on e-Shram as on 26 January 2026, with **14 central schemes**
integrated into it — PMSBY, PMJJBY, PM-SVANidhi, AB-PMJAY, PM-KISAN, ONORC and
others.[^4] The Ministry reported the count had reached 31.78 crore by 14 July
2026.[^5]

[^1]: Ministry of Labour & Employment, *Number of Workers In Unorganised Sector*,
      Lok Sabha written reply, 24 July 2023 — "As per the Economic Survey,
      2021-22, total number of people working in the unorganised sector is around
      43.99 crores during 2019-20."
      <https://www.pib.gov.in/PressReleasePage.aspx?PRID=1942079>

[^2]: Ministry of Labour & Employment, *Workforce in Organised/ Unorganised
      Sector*, 25 July 2016 — "the number of estimated employed persons in
      2011-12 on usual status basis were 47.41 crore, of which 82.7% of workforce
      (39.14 crore persons) was in unorganized sector." NSSO 2011-12 is the last
      survey to publish this split; the PLFS series that replaced it does not
      report the same organised/unorganised breakdown, which is why the year is
      old and stated rather than hidden.
      <https://www.pib.gov.in/newsite/PrintRelease.aspx?relid=147634&reg=48&lang=2>

[^3]: National Statistical Office, MoSPI, *Press Note on Periodic Labour Force
      Survey Annual Report, 2025* (January–December 2025), section 6 — casual
      labour other than public works, ₹455 male / ₹315 female per day;
      self-employment, ₹17,914 male / ₹6,374 female per month.
      <https://www.mospi.gov.in/uploads/latestReleases/latest_release_1774607827733_3e8964a9-268b-4cc9-ad65-cfc8a9e32f08_Press_note_AR_PLFS_2025_23032025_V2.1_26032026_final.pdf>

[^4]: Ministry of Labour & Employment, *e-Shram Cards for Unorganized Workers*,
      2 February 2026 — "As on 26th January 2026, over 31.48 crore unorganised
      workers have already been registered on eShram portal" and "fourteen (14)
      schemes of different Central Ministries/ Departments have already been
      integrated/ mapped with the eShram".
      <https://www.pib.gov.in/PressReleasePage.aspx?PRID=2222263&reg=3&lang=2>

[^5]: Ministry of Labour & Employment, Lok Sabha written reply, 21 July 2026, as
      reported by DD News — over 31.78 crore registered as on 14 July 2026, with
      fifteen central schemes mapped. Cited from the broadcaster because the
      corresponding PIB release page could not be located; treat the 31.48 crore
      figure above as the primary one.
      <https://ddnews.gov.in/en/over-31-78-crore-unorganised-workers-registered-on-e-shram-portal-government/>

## The gap

It is not eligibility. Workers are already entitled. The blockers are:

1. They do not know which schemes exist or apply to them.
2. Rules are scattered, in English, in bureaucratic language.
3. The paperwork is confusing, and **a failed trip to a Common Service Centre
   costs a day's wages** — ₹455 for a male casual labourer, ₹315 for a female
   one[^3] — so the second attempt often never happens.

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

_Running since 3 September 2026 on a single small cloud instance, restarted
under systemd and verified to survive a reboot. All seven schemes were signed
off on 9–10 September 2026, so the engine now returns real verdicts and the
event log can record eligible results._

**There are still no impact numbers here, and that is the honest state.** The
gate that produced zero results has been lifted; the field pilot that would
produce real ones has not run. Nobody has been screened yet except the
maintainer testing his own bot. This section stays empty until a real pilot
happens, and it will be filled from `python3 -m sathi.metrics.report` — not
from an estimate, a projection, or a "potential reach" figure.

The plan for that pilot, including consent and what will be measured, is in
[`docs/PILOT_PLAN.md`](docs/PILOT_PLAN.md).

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
python3 -m sathi.main --whatsapp     # the webhook (needs WHATSAPP_*, behind TLS)
python3 -m sathi.main --preview whatsapp   # what the wire would carry — no token, nothing sent
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
| `/demo` | Fixed fictional people run through the real rules — labelled a demonstration on every reply, opens no session, logs nothing |

## Tests

```bash
python3 check.py
```

20 module self-checks and 15 test files, no framework and nothing to install.
Worth knowing about three of them:

- `tests/test_privacy.py` — the reason the privacy claim above is defensible
  rather than aspirational.
- `tests/test_all_paths.py` — presses **every button at every reachable screen**
  in both languages (4,218 paths, 866 completed sessions), opens every generated
  sheet, runs every path through a real event log, drives every command through
  the channel adapter, and fuzzes the typed questions. It asserts its own
  coverage counters, because a green test that never reached the thing it checks
  is worse than no test.
- `tests/test_rule_boundaries.py` — asks whether the **answers** are right, not
  whether the code runs. Each scheme's rules are re-encoded from the official
  source text, independently of `data/schemes/`, and compared against the engine
  across every combination of the fields any rule touches — 214,326 verdicts,
  plus every named threshold one per line. Pressing every button cannot find a
  wrong threshold; a wrong threshold renders a perfectly well-formed screen.

## Keeping the rules honest after they are written

Two tools, both stdlib, neither of which the bot itself runs.

```bash
python3 -m sathi.review PMJJBY     # sign a scheme off
python3 -m sathi.sources           # has a ministry changed a number?
```

`sathi/review.py` is the only supported way a name reaches `verified_by`. It
prints every value the engine will use beside the URL it came from, one scheme
per screen, then writes **exactly two lines** — a self-check signs a real copy
and asserts precisely two lines differ, so a signature can never carry a changed
threshold in with it. It refuses to run without a terminal, and refuses a name
that looks automated. `--unsign` reverses it.

`sathi/sources.py` answers the question a signature cannot: a person checked
this in September, but is it still true? [`data/sources/`](data/sources/) holds a
fingerprint of each official page plus **43 named claims** — one per value we
rely on — and re-reads the live pages on demand. It also watches for things that
must *not* reappear, like the "16–59" age limit e-Shram no longer states.

[`data/sources/official-text/`](data/sources/official-text/) keeps the pages
themselves, so a rule can be audited without leaving the repository. That turned
out to matter: one URL cited in the morning had 404'd by the afternoon, two of
these hosts refuse an ordinary fetcher, and one official source is a 320 MB scan.

## How this was built

[`docs/LESSONS.md`](docs/LESSONS.md) — ten lessons from building it, including
the ones that cost something.
[`docs/BUILD_LOG.md`](docs/BUILD_LOG.md) — the unedited version: every bug, the
headline numbers that turned out to be wrong, what is still open, and what I
would do differently.
[`docs/assessment/`](docs/assessment/README.md) — a scored breakdown of where
this stands, including why product maturity is a 7 while the engineering is not.

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
