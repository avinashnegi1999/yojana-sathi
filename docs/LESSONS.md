# Lessons

The short version of how this was built and what I learned. The long version,
including every bug and the things still unresolved, is in `BUILD_LOG.md`.

---

## 1. Decide what the expensive mistake is, then build around it

The user of this system is an unorganised worker deciding whether to spend a day
walking to a government centre. A male casual labourer earns ₹455 a day, a
female ₹315 — that is the price of a wrong answer, and it is a cited figure, not
a rhetorical one.

That single fact set the architecture:

- A wrong **yes** costs a day's wages and the fare.
- A wrong **no** costs a scheme the worker was entitled to.
- **"I don't know — ask this exact question at the centre"** costs neither, and
  is still useful when they get there.

So the engine has three verdicts, not two, and the third one is the one the
design protects. Most systems treat "unknown" as a degraded answer. Here it is a
legitimate product, because it is honest and it still sends the worker in with
something to say.

## 2. Keep the language model out of the decision

Eligibility is decided by a pure function with no network, no clock and no
randomness. A model helps map "I lay bricks" to a job category — always
confirmed back to the worker before it is recorded — and rephrases Hindi that a
person wrote. It never sees a threshold, never produces a rupee figure, never
produces a verdict.

This is enforced, not just intended: a test asserts that importing the rules
package pulls in no model and no HTTP client, so a stray import fails the build
rather than a demo. Running with no API key is a *tested* configuration and the
eligibility output is identical either way.

The general form of the lesson: **compute, then narrate.** Calculate every
number in code; let the language layer only render facts it was handed.

## 3. A system that cannot say "I haven't checked this" will invent something

Every unresearched value in a scheme file is the literal string `"TODO"` —
including numbers. `annual_value_inr = "TODO"`, never `0`, because a zero looks
researched and no validator can tell the difference. Any file with a `"TODO"`
left in it still loads; it is flagged, and the engine returns UNKNOWN for it
rather than guessing.

Every value that *is* filled in carries a deep link to the sentence in the
official document it came from, and a date. A reviewer can audit any single rule
in about thirty seconds without opening the code.

## 4. Writing a safety rule in prose is not the same as enforcing it

This is the lesson that cost me the most.

I had written, in bold in the README, that the scheme data had not been checked
by a second person and that nobody real should be screened on it. I had written
it in a comment at the top of every scheme file. I had written a test asserting
the warning was still there.

Three places — all of them prose. Meanwhile the code treated "this file has no
`TODO` left in it" as "this file is verified", so the app printed
`PMSBY: verified` at startup and served real eligible/ineligible verdicts off
data one person had transcribed from a PDF once.

The two states are now separate in code — *researched* and *signed off by a
named human* — and only a scheme that is both can produce a verdict. Anything
else returns UNKNOWN, not a refusal, because turning a worker away on unchecked
data is the expensive direction.

The consequence is honest and inconvenient: **today the bot tells every worker
"I could not check this yet" for all three schemes**, and it will keep doing
that until I verify each value at its source and sign the file. It is a worse
demo and a better product.

**The transferable lesson:** a warning in a README protects nobody. If a rule
matters, the code path that would violate it has to be the thing that stops.

## 5. Test what the user touches, not what is convenient to assert

I put the bot live and used it as a worker would. Six bugs in the first hour —
**every one in the conversation layer, none in the rule engine.**

The engine was the part I had tested hardest, and it was fine. The bugs were a
`null` keyboard field that made Telegram reject the message with a bare `400` and
silently kill the session; a free-text box that looped back to the menu that led
into it; income bands with no option for a worker earning nothing; and English
screens whose *messages* were English while the *buttons* under them were Hindi.

Every test that passed while those shipped was asserting on message text. The
bugs were one layer out.

What exists now is a walk that presses every button at every reachable screen in
both languages — 948 paths — and, separately, a rule-validation test that
re-encodes each scheme's rules from the official source text independently of
the data files and compares that against the engine across ~10,000
combinations. The two find different things: one finds broken screens, the other
finds wrong answers. Pressing every button can never catch a wrong threshold,
because a wrong threshold renders a perfectly well-formed screen.

## 6. Make a test fail when it stops testing anything

When I enforced the verification rule from lesson 4, no scheme could produce a
verdict, so no worker reached an eligible result, so the application pack was
never generated. The exhaustive walk quietly dropped from 948 paths to 180 and
built **zero** packs — while still passing every assertion about the screens it
did reach.

It was caught because that test counts its own coverage and asserts on the
counters. A green test that never reached the thing it checks is worse than no
test, because it buys confidence you have not earned.

## 7. Check your own headline numbers before someone else does

The problem statement is half the score, and it was the only part of the project
with no sources. When I went to add citations, three of four headline numbers
did not survive: 93% was actually 82.7%, 44 crore was 43.99 crore, and a
₹6,688/month figure I had been quoting as fact **has no source at all** — it
entered my planning notes uncited and was never real.

Deleting it turned out to be an upgrade. The replacement is the ₹455/₹315 daily
wage from the 2025 labour force survey, which actually backs the core claim of
the whole project. "A wasted trip costs a day's wages" stops being rhetoric once
you can name the wage.

## 8. Don't let one number stand in for two different things

Once real values were in, the impact figure jumped. I was summing PMSBY's
₹2,00,000 accident cover with PM-SYM's ₹36,000/year pension — roughly a six-fold
overstatement, and a dishonest one, because a contingent insurance payout and a
guaranteed annual pension are not the same kind of money.

They are two separate numbers everywhere now, and the label "annual entitlement
surfaced, not money delivered" travels with the figure into the chat message,
the printed sheet and the dashboard.

A crash is visible. An inflated impact number is the kind of error that survives
all the way to a judge.

## 9. Collect less, so there is less to protect

There is no name field, no phone field and no Aadhaar field anywhere in this
project — not "we don't store it", the fields do not exist, so they cannot be
filled in by accident. The event log holds coarse bands rather than exact
figures, the session id is random and unrelated to the Telegram chat id, and any
statistic covering fewer than five workers is suppressed.

This costs something real, and I want to be straight about it: the pitch says
the system tells a worker where to walk, and it says "go to a CSC" rather than
"the CSC 4 km away". Closing that gap needs a district or a pincode in the
profile. I would rather ship a system that knows less and says less than one
that holds a worker's location. That is a tradeoff I chose, not one I overlooked.

## 10. Run the deployment the day you write it

I wrote a systemd unit and a deploy script days before running them. Installing
them for real found three bugs in ten minutes: the unit was missing
`PYTHONUNBUFFERED`, so the log showed *nothing* for a perfectly healthy bot; two
rate-limit directives were in the wrong section and were being silently ignored;
and the "update" script only started a stopped service, so re-running it on a
live bot left the old process running the old configuration.

None of those were hard. All of them were invisible until the thing actually ran.

The larger version of this lesson is why this is my second project for this
hackathon rather than my first. The first one — a complete, tested, live air
quality agent — is parked because it never reached a user. Building feels like
progress and shipping feels like a task that needs a clear day. Only one of them
is measured.

---

## Where AI fits in this

I used AI coding assistants throughout, and for a system that decides who is
entitled to government money I want to be exact about the boundary.

**What they did not do:** no scheme threshold, age band, rupee figure or
exclusion was authored by an AI. Every value in the rule files was read out of an
official source document and carries a deep link to the sentence it came from.
Anything not yet researched was stubbed as `"TODO"` rather than filled with a
plausible number. The rule engine contains no model at runtime either, and a test
enforces that.

**What they did:** write and refactor application code, generate test
scaffolding, draft documentation, and — via an outside review late in the
project — find the verification bug in lesson 4, which I had written and not
noticed.

**What I still had to do myself:** decide the architecture, read the source
PDFs, find six bugs by using my own bot, notice the impact number was inflated,
delete a statistic I had been repeating for weeks, and answer the judgement calls
that no amount of re-reading a web page will settle — such as whether PM-SYM's
"₹15,000 or less" includes exactly ₹15,000, which is a phone call to 14434, not
a search.

The through-line of every lesson above is the same one: **the value of this
system is that it refuses to guess.** That property does not come from the
model, and it does not come from the tests. It comes from deciding in advance
what you are not willing to be wrong about, and then making the code enforce it
rather than the documentation.
