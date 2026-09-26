# What the numbers mean.

What each number counts — and what it does not claim.

> Nothing here is filled in until real workers use the tool. No projections, no "potential reach". If it isn't in the event log, it isn't reported.

<br>

## The numbers.

| Number | Counts | Does **not** claim |
|---|---|---|
| Workers screened | Sessions that reached an eligibility result | Distinct *people*. Sessions are deliberately not linkable. |
| Schemes matched per worker | Matches ÷ sessions screened | That any were applied for |
| **Newly surfaced** | Matches the worker said they did **not** already hold | Deeper unawareness — only that they said they didn't hold it |
| **Annual entitlement surfaced (₹)** | Yearly value of newly surfaced matches that pay out | **Money delivered.** Nobody received this. It is what they were told they are entitled to. |
| **Accident cover surfaced (₹)** | The same, for insurance covers — PMJJBY's life cover counts here too | That anyone claimed, or will. A cover pays only on a claim. |
| Application packs | Sheets produced in a session | Sheets submitted or accepted |
| Median session time | Last event − first event, per session | Time to finish an application |

<br>

## Surfaced, never delivered.

The ₹ figure is the one most likely to be misread — by us too. It is **"entitlement surfaced"**, never "value delivered". That phrase survives unchanged into the README, the dashboard and the demo video.

<br>

## Payouts and covers are never added.

PM-SYM surfaces a ₹36,000-a-year pension. PMSBY surfaces a ₹2,00,000 cover that pays only if there is an accident. Added together, that is ₹2,36,000 "surfaced" for a worker who can expect ₹36,000 — about six times too much, and the first thing a judge would take apart.

- The dashboard shows a payout total and a cover total. The worker sees them on separate lines too.
- The split joins each `scheme_code` in the log to that scheme file's `value_basis`. No extra column, no migration.
- A code with no matching file counts as `unclassified`, not as either total.
- Schemes with unresearched values add ₹0. The totals can only understate — the right direction to be wrong in.

<br>

## Where "newly surfaced" comes from.

One intake question: which of these schemes do you already have? Any match not in that answer is newly surfaced. That's why the question shipped in the first deployed version.

<br>

## Pensions that start at 60.

PM-SYM and NPS-Traders pay ₹3,000 a month **from age 60**, and the worker pays ₹55–₹200 a month until then. They count at their stated yearly value — but a 25-year-old receives nothing for 35 years. The worker is told: the result and the sheet show each scheme's cost, and the total says each pension starts at its own age.

<br>

## Pilot, not testing.

- **Terminal sessions are left out** unless `--include-cli` is given. They are always someone at a keyboard.
- **A pilot is counted by its link.** Hand out `t.me/YojanaSathiBot?start=csc` or `sathi.avinashnegi.com/?start=csc`, then run `python3 -m sathi.metrics.report --cohort csc --since <pilot start>`.
- **"Who is this for?" can't filter.** That answer is stored without a session id, on purpose — so the link is the separator.
- **Browser sessions are not counted as people.** A cookie is a random routing key, not an identity.

<br>

## Privacy.

- **Coarse bands only:** state, age band, occupation, income band — plus the channel and, after consent, the arrival-link tag.
- **Occupation** is asked only when a screened scheme needs it. No signed scheme does today, so it is usually empty. **Income** is asked only when PM-SYM is screened.
- **Never written:** name, phone, Aadhaar, village, exact income. Those fields don't exist in the profile.
- **Each session gets a fresh random id**, not derived from any messaging account. Two sessions by the same worker can't be linked — which is why "workers screened" honestly means sessions.
- **Breakdown rows under 5 sessions** show as `<5`. Headline totals are not suppressed, and the dashboard says so. This is not a guarantee of anonymity.

<br>

## Freshness.

The dashboard shows each scheme's `verified_on` date and the days since. A rule checked nine months ago may be wrong now, and the report says so.
