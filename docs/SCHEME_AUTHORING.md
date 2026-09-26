# Write a scheme file.

No Python needed. You fill in a text file and cite where each value came from.

<br>

## The one rule.

**If an official `.gov.in` source doesn't state it, write `"TODO"`.**

- The engine answers `UNKNOWN` for that scheme — "we couldn't check this, ask at the centre". That is honest, and still useful.
- A guess is not. A wrong threshold sends someone on a trip that costs a day's wage, and most people don't try twice.
- `"TODO"` is the stub for **every** type, numbers included: `annual_value_inr = "TODO"`, never `0`. A zero looks researched, and no validator can tell.
- Never fill a value from a news article, a coaching site, an aggregator or a chatbot.

<br>

## Steps.

1. Copy [`data/schemes/_TEMPLATE.toml`](../data/schemes/_TEMPLATE.toml) to `data/schemes/<scheme>.toml`.
2. Fill what you can find. Cite each value with a `source_url`.
3. Run `python3 check.py`. Structural mistakes fail loudly — an unknown key, a bad operator, a field the app never asks. Stubs don't fail; they are listed.
4. Get it signed (below). Until then every worker gets `UNKNOWN` for it.

<br>

## Every `source_url`.

A deep link to the page that carries **that exact value**. Not the site root, not a PDF listing page. A reviewer should see the number within 30 seconds of clicking.

<br>

## Rules.

- **All `[[criteria]]` must pass.** Any `[[exclusions]]` match disqualifies, with its `reason_hi`.
- **`field`** must name a field on `Profile` ([`sathi/core/profile.py`](../sathi/core/profile.py)). The loader checks.
- **`op`** is one of these:

| `op` | `value` |
|---|---|
| `between` | `[low, high]`, both ends inclusive |
| `in` · `not_in` | a list |
| `lte` · `gte` | a number |
| `eq` | any value |
| `exists` | — |
| `before_nearest_birthday` | a positive whole-number age. Age only. The last whole year below the cutoff stays `UNKNOWN`. Use it only when the source itself counts age by nearest birthday. |

<details>
<summary><b>Every profile field</b></summary>

<br>

`state` · `age` · `occupation` · `is_unorganised_worker` · `income_band` · `land_holding_band` · `family_size` · `has_bank_account` · `is_income_tax_payer` · `is_epfo_or_esic_member` · `nps_exclusion_applies` · `is_woman` · `is_widow` · `uk_pension_income_or_bpl` · `uk_pension_selected` · `receives_other_pension` · `household_has_lpg` · `pmuy_declaration_met` · `is_bpl` · `has_disability_80pct` · `is_small_trader` · `is_vishwakarma_artisan` · `took_business_loan_5yr` · `has_government_service_in_family` · `known_schemes`

- `is_unorganised_worker` is what the worker says. It is never inferred from a job title.
- `nps_exclusion_applies` is a yes / no / not-sure finding about the exclusion, not a general claim of NPS membership. Other or uncertain NPS types stay unresolved.

A scheme that needs a field not on this list is a product decision, not a data one: every new field is a new question a worker has to answer. Open an issue.

</details>

<br>

## Benefit.

| Key | What it holds |
|---|---|
| `annual_value_inr` | ₹ a year, as the scheme states it. For a cover, the cover amount. |
| `value_basis` | `annual_payout` · `insurance_cover` · `one_time` · `subsidy` · `in_kind` · `gateway` |
| `premium_inr` | ₹ a year the **worker** pays. `0` if free. |
| `exclusive_group` | Optional. Alternative routes to one payment share a group, and are never added together. |
| `annual_value_age_bands` | Optional. A different amount from a stated age, e.g. from 80. |

Where to apply is one of `csc` · `bank_branch` · `post_office` · `eshram_centre` · `online`.

<br>

## Words a worker hears.

These may be read aloud to someone who doesn't read. Write speech, not notices.

- **`pass_hi`** — one plain sentence: why they qualify.
- **`fail_hi`** — why not, **and what they can do instead**. "You need a bank account — any public sector bank will open a zero-balance account with your Aadhaar" helps. "Not eligible" doesn't.
- The `_en` keys are the English versions, with the same citation.

<br>

## Precision that matters.

- **Income.** "Family income" and "personal income" are different rules. Say which one the source says.
- **Age.** Note whether the source's bounds are inclusive.
- **Occupation.** Use the scheme's own categories, not ours.
- **Land.** Always with units.
- **Documents.** The exact names the office uses, not paraphrases.

<br>

## Sign it.

```bash
python3 -m sathi.review <CODE>
```

It shows every value beside its source. You open each page, and if everything matches, you type the code and your name. It writes exactly two lines — a signature can never carry a data change in with it. `--unsign` reverses it.

A signature is a change in what workers are told, so two tests must change with it:

- **`SIGNED_OFF`** in [`tests/test_schemes.py`](../tests/test_schemes.py) pins the signed list.
- **The hand-written rules** in [`tests/test_rule_boundaries.py`](../tests/test_rule_boundaries.py) must cover the scheme. Every signed scheme is swept against them.

<br>

<sub>Research notes behind the first schemes: [`history/SCHEME_AUDIT.md`](history/SCHEME_AUDIT.md).</sub>
