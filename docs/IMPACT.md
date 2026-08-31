# Impact methodology

What each number counts, and what it does not claim.

> Nothing here is populated until the tool is deployed and real workers have
> used it. There are no projections in this project and no "potential reach"
> figures. If it is not in the event log, it does not get reported.

## The six numbers

| Number | Counts | Does **not** claim |
|---|---|---|
| Workers screened | Distinct sessions that reached an eligibility evaluation | Distinct *people*. Sessions are deliberately not linkable — see Privacy. |
| Schemes matched per worker | Matches ÷ sessions screened | That any of them were applied for |
| **Newly surfaced** | Matched schemes the worker said they did **not** already have | That the worker was previously unaware in any deeper sense — only that they said they did not hold it |
| **Annual entitlement surfaced (₹)** | Sum of annual value over newly-surfaced matches whose `value_basis` is a payout | **Money delivered.** Nobody received this. It is what they were told they are entitled to. |
| **Accident cover surfaced (₹)** | The same sum restricted to `value_basis = "insurance_cover"` | That anyone claimed, or will claim. A cover pays only on a claim, and is never added to the payout total. |
| Application packs generated | Packs produced in a session | Packs submitted, or accepted |
| Median session time | Last event − first event, per session, median | Time to complete an application |

**The ₹ figure is the one most likely to be misread**, including by us. It is
"entitlement surfaced", never "value delivered". That phrasing has to survive
into the README, the dashboard and the demo video unchanged.

**Payouts and covers are reported as two separate numbers.** PM-SYM surfaces a
₹36,000/year pension; PMSBY surfaces a ₹2,00,000 accident cover that pays only
if an accident happens. Summing them would report ₹2,36,000 "surfaced" per
worker when the money they can expect to receive is ₹36,000 — a ~6x overstatement
and the first thing a judge would take apart. The dashboard shows a payout total
and a cover total, and the worker-facing message states them on separate lines
in the same terms.

The split is derived by joining `scheme_code` in the event log back to the scheme
file's `value_basis`, so it needs no extra column and no migration. A scheme code
in the log with no matching file is counted as `unclassified` rather than folded
into either number.

Schemes still carrying unresearched values contribute ₹0, because their benefit
amount is a stub. The reported total therefore under-states rather than
over-states — the right direction to be wrong in.

## Where "newly surfaced" comes from

During intake the worker is asked which of the schemes they already have. Any
match not in that set is counted as newly surfaced. It depends entirely on that
one question, which is why it ships in the first deployed version and not later.

## Privacy

Counts and coarse bands only: state, age band, occupation, income band. No
name, phone, Aadhaar, village or exact income is written to the event log, and
those fields do not exist in the profile.

Each session gets a fresh random id that is **not** derived from the messaging
account, so two sessions by the same worker are not linkable in the log. That
is why "workers screened" is honestly "sessions screened" — the alternative
would be tracking people, which is worse.

Aggregates covering fewer than 5 sessions are suppressed and shown as `<5`, so
that state × occupation × age cannot re-identify one person in a small district.

## Data freshness

The dashboard shows each scheme's `verified_on` date and days since. A rule
verified nine months ago may no longer be correct, and the report says so rather
than presenting every number as equally current.
