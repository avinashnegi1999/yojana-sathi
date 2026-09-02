# Build log

An honest record of how Scheme Sathi was built: what broke, what I got wrong,
what I had to change after finding out I was wrong, and what is still open.

This is the long version, written for me. `LESSONS.md` is the short version.

Nothing here is tidied up after the fact. Where a decision turned out to be
wrong, the wrong version is still described, because the correction is the
interesting part.

---

## Timeline

| Date | What happened |
|---|---|
| 25 Aug 2026 | Picked the hackathon track by score arithmetic, not preference. Built **Saans**, a different project entirely, to completion. |
| 30 Aug 2026 | Parked Saans. Started Scheme Sathi. Locked the four decisions below before writing code. |
| 31 Aug 2026 | Core built end to end. Scheme data researched from official sources. Bot went live on Telegram. First real testing session found six bugs. |
| 1 Sep 2026 | README problem section given real citations — three of four headline numbers were wrong. Verification worksheet and deploy scripts written. Hit three signup walls trying to host it. |
| 3 Sep 2026 | Outside review found a safety bug in the verification logic. Fixed it, plus abuse controls, retry backoff, container hardening, CI. Bot restarted as a real service. |

---

## Before this: I built a different project first, and parked it

Scheme Sathi is my second entry for this hackathon. The first was **Saans**, a
personal air-exposure agent on Telegram — around 3,500 lines across 13 modules,
zero third-party dependencies, 12/12 checks passing, a live bot, a public repo
under Apache-2.0. It is finished code. I parked it on 30 August.

**How I picked that track in the first place.** Not by what I found
interesting. 50% of the hackathon score is a cited written problem statement
judged on size and severity, so I ranked tracks by the headcount and death toll
I could cite. Clean Air — 1.4 billion people exposed, 1.67 million deaths a
year — beat Tech Employment's 1.5 million graduates a year by roughly 18 points
before a line of code existed. The track was also empty and judging falls during
the November North-India smog peak, so the impact data would collect itself.

**Why I parked it anyway.** It was never deployed and never put in front of a
single user. That is the real reason, and it is worth being precise about it,
because I initially told myself a different one: I had discovered the idea
already existed in another app. But novelty is not a judging criterion here.
Losing on novelty was a feeling, not a score. Losing on "25% deployment and
impact data, ties broken on impact first, and you have zero users" is a score.

The lesson I took into Scheme Sathi was to front-load deployment. The plan puts
the deploy gate at week 6 — 11 October — because the impact criterion needs
roughly five weeks of real usage and cannot be retrofitted in November.

**What Saans taught me technically**, all of which is load-bearing here:

- **"Compute, then narrate."** Saans is a health product; a hallucinated µg/m³
  figure is not cosmetic. Every number was computed in Python and the message
  layer only rendered facts it was handed. That rule is the direct ancestor of
  "the rule engine may not import a language model" below, and it is the single
  most important decision in this codebase.
- **Zero third-party dependencies, discovered rather than decided.** I had
  planned to use FastAPI, python-telegram-bot and APScheduler. Each turned out
  to be about 80 lines of `urllib` for what I actually needed, so all three were
  dropped. Scheme Sathi started from that position instead of arriving at it.
- **Constraints that veto and explain, never a blended score.** Saans lets heat
  and roadside traffic *veto* an hour and say why, rather than folding them into
  one opaque number. Scheme Sathi's three-valued verdicts with an authored
  reason line per criterion are the same idea.
- **I found Saans's two worst bugs by using it myself**, which is exactly what
  happened again here. It recommended a 45-minute run at 10am in 36°C heat,
  because the cleanest hour of the day is very often the hottest — same physics,
  and the model had no idea. And it forecast coarse-grid *ambient* air while
  most people in India run on roads, where kerbside exposure is materially
  worse at commute peaks. Both were obvious the moment a real person read the
  output and neither was visible from the test suite.

---

## The four decisions made before any code

These were settled on day one and never revisited. Every one of them cost
something and each is the reason a later category of bug did not happen.

**1. The rule engine may not import a language model.**
Eligibility is decided by `sathi/rules/engine.py`, a pure function with no
network, no clock, and no randomness. A model may help map "I lay bricks" to a
job category and may rephrase Hindi a human wrote. It never sees a threshold,
never produces a ₹ figure, and never produces a verdict.

`tests/test_rules.py` asserts the import graph of `sathi.rules` stays clean, so
a stray import fails the build rather than a demo.

**2. Three-valued logic, not two.**
Every criterion returns `True`, `False`, or `None`. Missing information is
never quietly treated as failure. A worker who has not answered a question gets
"I don't know", not "no".

This sounds academic until you price the error. The user of this system loses a
day's wages and the bus fare when they walk to a centre for nothing. A wrong
"yes" costs a day. A wrong "no" costs a scheme they were entitled to. "I don't
know, ask this exact question at the centre" costs neither and is still useful.

**3. Unresearched values are the literal string `"TODO"`, including numbers.**
`annual_value_inr = "TODO"`, never `0`. A zero looks researched and no validator
can tell the difference. A file with any `"TODO"` left in it still loads — it is
flagged, and the engine returns UNKNOWN for it.

**4. No name, no phone number, no Aadhaar field anywhere.**
Not "we don't store it" — the fields do not exist on the `Profile` dataclass, so
they cannot be stored by accident. The event log holds coarse bands only, the
session id is a random uuid unrelated to the Telegram chat id, and cells with
fewer than five workers are suppressed in the dashboard.

---

## Bugs

### The six from the first hour of real use

The bot went live and I used it as a worker would. Six bugs in one session.
**Every single one was in the conversation layer. None were in the rule engine.**

1. **Sending `"reply_markup": null` killed every session.** Telegram answers a
   null keyboard with a bare `400` and no useful message. The age question and
   every info command send a message with no buttons, so the session silently
   stopped dead at the first typed question. Nothing crashed, nothing logged.

2. **Free-text occupation was a loop with no exit.** The occupation menu has a
   "something else" button which leads to a free-text box. If the text matched
   nothing, the code showed the menu again — whose "something else" leads back
   to the same box. I hit it on the first run by typing "i dont do any job".

3. **No "not working" category, and no Hinglish keywords.** The offline matcher
   only knew Hindi and English words. Real people type "mistri", "driver ka
   kaam".

4. **No zero-income band — and PM-SYM's own list would have denied it.** The
   income bands started at "up to ₹5,000". A worker with nothing coming in does
   not recognise themselves in that and may pick nothing or pick wrong. Worse,
   the scheme's band list did not include the zero case, so a worker with no
   income was being told they earned too much.

5. **Button labels stayed Hindi in an English session.** The string lookup for
   income and land bands missed the language argument. The *message* was in
   English and the *buttons* under it were in Hindi. Every test that "passed"
   was checking message text; the bug sat in the button labels.

6. **The application pack used `name_hi` and hardcoded Hindi labels.** Same
   class of bug, one layer further out.

The pattern is the lesson: my tests all drove one path a human thought of, and
checked the text of the reply. The bugs were in the buttons and in paths nobody
had clicked. `tests/test_all_paths.py` exists because of this session — it
presses every button at every reachable screen in both languages, 948 paths, and
asserts its own coverage counters so a walk that never reached a screen fails
rather than passing quietly.

### The methodology bug real numbers exposed

Once the scheme files had real values, the impact number jumped in a way that
looked too good. PMSBY is a ₹2,00,000 accident cover. PM-SYM is a ₹36,000/year
pension. I was summing them into one "annual entitlement" figure — roughly a 6x
overstatement, and a dishonest one, because a contingent insurance payout and a
guaranteed annual pension are not the same kind of money at all.

They are now two separate numbers everywhere: in the chat message, in the
application pack, and on the dashboard. The label "annual entitlement surfaced,
not money delivered" travels with the figure wherever it is shown.

This one matters more than a crash. A crash is visible. An inflated impact
number in a hackathon submission is the kind of thing that survives all the way
to a judge.

### The verification bug — the worst one, found by an outside review

I made the repo public and had ChatGPT review it. Most of what it found I had
already written down as known tradeoffs in my own comments. One finding was
real, and it was the most serious bug in the project.

`Scheme.is_verified` was implemented as:

```python
@property
def is_verified(self) -> bool:
    return not self.stubs
```

So "verified" actually meant "contains no `TODO`". But all three scheme files
had been fully researched, so none of them had a `TODO` left — while every one
of them still said:

```toml
verified_by = "unconfirmed — PENDING HUMAN VERIFICATION"
```

The result: startup printed `PMSBY: verified 2026-08-31`, and the engine served
real ELIGIBLE and INELIGIBLE verdicts off values that one person had transcribed
from a PDF once and nobody had checked. The README said in bold not to screen a
real worker on this data. The runtime ignored the README.

The whole project's premise is "don't guess". Here the program was guessing that
*researched* meant *verified*, which are not the same thing at all.

The fix separates them:

```python
is_researched      # no "TODO" left — somebody looked it up
is_human_verified  # verified_by carries a real signature, not the PENDING marker
is_servable        # both. The only thing evaluate() is allowed to gate on.
```

An unservable scheme returns UNKNOWN — **not even a NO**, because turning a
worker away on unchecked data is the expensive direction of the error.

The honest consequence: **today the bot tells every worker "I could not check
this yet" for all three schemes.** That is correct, and it stays that way until
I verify the values at source and sign each file. It is a worse demo and a
better product.

### What fixing it broke, and how that got caught

Enforcing the gate meant no scheme was servable, so no worker ever reached an
eligible result, so the application pack was never generated. `test_all_paths.py`
quietly fell from 948 paths to 180 and produced **zero** packs — it still passed
every assertion about the screens it did reach.

Its own coverage counter caught it:

```python
assert CHECKED["packs"] >= 2, f"no pack was ever generated or checked: {CHECKED}"
```

That assertion was written after the six-bug session, on the theory that a green
test which never reached the thing it checks is worse than no test. It paid for
itself here. The fix was to re-sign the real scheme files with a test signature
for the walk, so every real name, string and threshold is still exercised, while
`test_schemes.py` separately asserts the shipped files stay honestly unsigned.

### Three bugs that only appeared when I ran it as a real service

I had written `deploy/sathi.service` days earlier and never actually run it.
Installing it found three things at once:

1. **No `PYTHONUNBUFFERED=1` in the unit.** Python block-buffers stdout when it
   is a pipe, and journald is a pipe. `journalctl -u sathi -f` showed
   *absolutely nothing* for a bot that was running perfectly. I spent real time
   convinced the service was dead. The Dockerfile had set this; the unit never
   did.

2. **`StartLimitIntervalSec` and `StartLimitBurst` were in `[Service]`.** They
   are `[Unit]` directives. systemd logged `Unknown key … ignoring` and the
   crash-loop rate limit my own comment promised simply did not exist.

3. **`run-locally.sh` did not restart anything.** It ran `systemctl enable
   --now`, which only *starts* a stopped service. Re-running the script on a
   live bot left the old process running the old unit — so an edit looked
   applied and was not. The script is documented as the update path, so it now
   calls `restart`.

### A diagnostic that lied to me

While checking whether the service was really polling, I called `getUpdates`
myself, reasoning that Telegram allows only one poller and would return `409
Conflict` if the bot was live. It returned `200 OK`, so I concluded the service
was down and said so.

That was wrong. Telegram *preempts* an existing long poll rather than always
returning 409, so my probe created the very condition it was testing for.

The reliable checks turned out to be `ss -tnp` showing an established
connection to a `149.154.166.x:443` address held by the bot's PID, and fresh
`session_start` rows appearing in the event log. Also worth knowing:
`pending_update_count` from `getWebhookInfo` does not mean queue depth for a
long-polling bot and should not be read as one.

### The retry loop that was a hot loop

`run_forever()` caught network errors and retried immediately, with no delay.
For a dropped connection that was fine, because `getUpdates` blocks for 50
seconds and paced the loop for free. For a *permanent* error it was not: a
revoked token returns `401` instantly, so the loop became a spin that would peg
a CPU core and write the same line to the log forever. Now 1s → 60s exponential
backoff, reset on the first success.

---

## Things research forced me to change

I wrote the scheme file format first and then went to research the actual
schemes. Three assumptions in my format did not survive contact with the
sources.

**e-Shram is not a benefit.** I had assumed every scheme has a ₹ value. e-Shram
is a registration that issues a UAN card; the benefits are delivered *through*
it. Giving it a rupee figure would have double-counted the PMSBY cover it
unlocks. Added `value_basis = "gateway"` so it can be surfaced as valuable
without contributing a number.

**One yes/no question covers three different memberships.** PM-SYM excludes
members of EPFO, ESIC and NPS. e-Shram's definition of an unorganised worker
excludes EPFO and ESIC but says nothing about NPS. I use a single
`is_statutory_scheme_member` field, which makes the system *stricter* than
e-Shram's own wording for a worker who holds NPS alone. That is a deliberate
choice — under-promising is the safe direction — and it is written down as an
open question rather than hidden.

**A premium is not always a number.** PM-SYM's monthly contribution depends on
the age you join at: ₹55/month at 18, ₹200/month at 40. The field now accepts a
short sentence as well as an integer. It is never summed, only shown, so prose
is safe there — but it must be non-empty, because an empty string reads as
"free".

---

## Numbers in my own README that turned out to be wrong

The problem statement is worth 50% of the hackathon score, and it was the only
part of the repo with no sources. When I went to add citations, three of the
four headline numbers did not survive:

- **44 crore → 43.99 crore.** Close, but the real figure has a source: Economic
  Survey 2021-22, via a PIB Lok Sabha reply.
- **93% → 82.7%.** The number I had was simply wrong. The last full survey to
  split the workforce found 39.14 crore of 47.41 crore, which is 82.7%. The
  footnote says outright why the data is from 2011-12: the current labour force
  survey does not publish the organised/unorganised split.
- **₹6,688/month — deleted.** No source exists. It entered my planning document
  uncited and was never real. I had been quoting it as fact.
- **31.38 crore → 31.48 crore**, as on 26 January 2026, with a PIB release id.

Deleting ₹6,688 turned out to be an upgrade rather than a loss. The replacement
is a *daily* figure from the 2025 labour force survey — a male casual labourer
earns ₹455 a day, a female ₹315 — which actually backs the core claim of the
project. "A wasted trip to a CSC costs a day's wages" stops being rhetoric when
you can name the wage.

---

## What is still open, and what is still wrong

**e-Shram has no upper age limit in my rules, and it might need one.**
The e-Shram FAQ says registration is for workers "16 and above". Another
official e-Shram page describes it as 16–59. My files encode "16 and above", so
the bot currently tells a 70-year-old they are eligible. **If 16–59 is the
correct reading, every worker aged 60 or over is getting a wrong answer today.**

`tests/test_rule_boundaries.py` pins this so it cannot be changed quietly, and
`docs/VERIFICATION.md` carries it as an open question with a concrete way to
settle it — ask a CSC operator.

**Two other judgement calls need a human, not another web page.** PM-SYM's
income ceiling is written as both "₹15,000 or less" and "less than ₹15,000" on
official pages, which changes who qualifies at exactly ₹15,000; the way to
settle it is to call 14434. And whether NPS alone should disqualify someone
from e-Shram is a reading of intent, not a fact to look up.

**Nothing is signed off, so nobody real has been screened.** That is the
blocking item, and it is not a code problem.

**Location routing is a real gap I chose not to close.** The pitch says the
system tells a worker where to walk. It says "go to a CSC", not "go to the CSC
4 km away on the main road". Closing that needs a district or a pincode in the
profile — which directly contradicts the privacy design. I would rather ship a
system that knows less about the worker and says "a CSC" than one that holds a
location. That is a tradeoff, not an oversight, but it is a fair criticism.

**PMSBY asks about a bank *or post office* account and then says "go to your
bank branch".** The official rules cover both. The field holds one location. A
worker who only has a post office account is sent to the wrong counter.

**The largest risk is not technical at all: the AgentFoundry eligibility gate.**
The submission template on the organiser's repo carries a required checkbox —
"Built using AgentFoundry (AF), the official IDE" — and the form cannot be
submitted without ticking it. This project was built locally in Python. I have
written to the organisers asking four things: whether a project must originate
in AF from the first commit or whether importing an existing repo and continuing
there qualifies, what runtime or structural constraints apply, whether the
checkbox is self-declared or verified against a project id and trace history,
and whether the provided tokens are usable from a deployed service or only
inside the IDE. No reply yet. If the answer is "must originate in AF", the
local-Python assumption behind both of my entries is invalid, which is why it
sits above every code task on my list.

**Hosting is blocked on paperwork, not code.** Fly.io wants a card preauth,
which Indian cards routinely block for international transactions. Azure for
Students needs academic verification and my university email has no Microsoft
identity at all. The GitHub Student Pack does *not* include Azure for Students,
which cost me an afternoon to discover. The bot currently runs as a systemd
service on my own laptop, which at least survives logout and reboot.

---

## Tools

**Language and runtime.** Python 3.11+, standard library only. **Zero
third-party dependencies** — not a purity exercise, and not a decision I made up
front. On the previous project I had planned FastAPI, python-telegram-bot and
APScheduler, then found each was roughly 80 lines of `urllib` for what I
actually needed. Having arrived there once, I started here from that position.
The payoff is that there is no `pip install` step that can fail on deploy day,
and a container that installs nothing cannot fail to install. `tomllib`,
`sqlite3`, `urllib`, `dataclasses` and `unicodedata` cover everything this
project does.

**Data format.** TOML for scheme rules, so a non-programmer can read and check a
rule file. Every value carries a `source_url` deep link and a `verified_on`
date.

**Storage.** SQLite, one writer module, schema in SQL rather than an ORM.

**Messaging.** Telegram Bot API over long polling, written directly against
`urllib`. Long polling rather than a webhook because a webhook needs a public
URL, TLS termination and a platform that stays awake — three things that can
fail on deploy day. Long polling needs one outbound connection.

**Testing.** No framework. Plain `assert`, a `_self_check()` in each module, and
test files that run as scripts. `python3 check.py` runs 15 module self-checks
and 6 test files in a couple of seconds with nothing to install.

**Deployment.** systemd unit (the same file runs on a laptop and on a VM),
Docker as an alternative path, GitHub Actions running the full suite and the
image build on every push.

**Text-to-speech.** Optional, driven by an external command via `TTS_CMD`, so
the project does not depend on any particular engine.

**AI assistance.** I used AI coding assistants throughout — Claude Code as the
main one, and ChatGPT for an outside code review late in the project. I want to
be precise about what that did and did not do, because for a system that decides
who is entitled to government money it matters:

- **No scheme threshold, rupee figure, age band or exclusion was authored by an
  AI.** Every value in `data/schemes/*.toml` was read out of an official source
  document, and each one carries a deep link to the sentence it came from. Where
  a value was not yet researched it was stubbed as `"TODO"`, never filled with a
  plausible number.
- **The rule engine contains no AI at runtime either.** That is the architecture
  described at the top of this document, and it is enforced by a test on the
  import graph.
- **The optional runtime model** does two narrow jobs: mapping free text to a
  job category, which is always confirmed back to the worker before it is
  recorded, and rephrasing Hindi a human wrote. Its output is whitelisted
  against known category codes, and a rephrasing that introduces a number the
  original did not contain is discarded entirely. `LLM_API_KEY` unset is a
  *tested* configuration and eligibility output is identical either way.
- **What the assistants genuinely did** was write and refactor application code,
  generate test scaffolding, draft documentation, and — in the case of the
  outside review — find the verification bug described above, which I had
  written and not noticed.
- **What I still had to do myself** is everything the log above is about:
  deciding the architecture, reading the source PDFs, finding six bugs by using
  my own bot, noticing the impact number was inflated, and answering the
  judgement calls that no amount of re-reading a web page will settle.

---

## What I would do differently

**Write the "is this data trustworthy" check as code on day one.** I wrote the
warning in the README, in a test, and in a comment in every scheme file. Three
places, all of them prose. The one place it was not written was the code path
that decides whether to answer a worker — and that is the only place that
actually stops anything.

**Test the buttons, not the messages.** Every test that passed while six bugs
shipped was asserting on message text. The bugs were one layer out.

**Run the deployment scripts the day you write them.** Three bugs sat in a
service file for days because installing it felt like a task for later. It took
ten minutes and found all three.

**Cite the problem statement before writing the solution.** I built the whole
system on a ₹6,688 figure that does not exist. It changed nothing about the code
— but if a judge had asked where it came from, I would have had no answer.

**Deploy before you polish — I have now learned this twice.** Saans is finished,
tested and live, and it is parked because it never reached a user. I started
Scheme Sathi promising myself I would not repeat that, and then spent an
afternoon writing deployment scripts I did not run for two days. The pattern is
the same each time: shipping feels like a task that needs a clear day, and
building feels like progress. Only one of them is measured.
