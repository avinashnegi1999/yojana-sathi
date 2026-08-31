# Authoring a scheme rule file

No Python required. You are filling in a text file and citing where each number
came from.

## The one rule

**If you cannot find a value on an official `.gov.in` source, leave it as
`"TODO"`.**

The loader detects the literal string `"TODO"` and the rule engine reports
`UNKNOWN` for that scheme — "we could not check this, ask at the CSC". That is
an honest answer and still useful to a worker.

A guessed threshold is not. It sends someone on a day-long trip that costs them
a day's wages, and most people do not make a second attempt.

Stubs are the string `"TODO"` for **every** type, numbers included:
`annual_value_inr = "TODO"`, never `= 0`. A zero looks like a researched answer
and the validator cannot tell the difference.

## Steps

1. Copy `data/schemes/_TEMPLATE.toml` to `data/schemes/<scheme>.toml`.
2. Fill what you can find, citing each value.
3. Run `python3 check.py`. Structural mistakes — an unknown key, a bad
   operator, a field the app never asks about — fail loudly. Unfilled values do
   not; they are simply reported as stubs.

## What each `source_url` has to be

A deep link to the page carrying **that specific value**. Not the site root.
Not a PDF listing page. A reviewer must be able to click it and see the number.

## Fields the engine understands

`field` must name a field on `Profile` (`sathi/core/profile.py`):

`state` · `age` · `occupation` · `income_band` · `land_holding_band` ·
`family_size` · `has_bank_account` · `is_income_tax_payer` · `known_schemes`

If a scheme needs something not on that list, open an issue — adding a field
means adding a question the worker has to answer, which is a product decision,
not a data one.

`op` is one of: `between` (`[low, high]`) · `in` / `not_in` (a list) ·
`lte` / `gte` (a number) · `eq` (any) · `exists`.

All `[[criteria]]` must pass. Any `[[exclusions]]` match disqualifies.

## Wording `pass_hi` and `fail_hi`

These are read aloud to someone who may not read. Write them as speech.

- `pass_hi` — one plain sentence saying why they qualify.
- `fail_hi` — why they do not, **and what they could do instead**. A dead end
  is a failure of the tool, not of the worker. "You need a bank account — any
  public sector bank will open a zero-balance account with your Aadhaar" is a
  useful answer. "Not eligible" is not.

---

# Research checklist — the first three schemes

Accuracy over coverage. Three schemes done correctly beats twenty done
approximately.

## 1. e-Shram registration

- **Primary:** `eshram.gov.in` — registration criteria page
- **Secondary:** Ministry of Labour & Employment, `labour.gov.in` — guidelines / FAQ PDF

**? Resolve this first, before the rules:** e-Shram is a registration and an
identity (UAN), not obviously a benefit scheme with a payout. It is the gateway
that unlocks others. Confirm whether it carries a benefit in its own right —
there is commonly an accident cover associated, and it matters whether that is
intrinsic to registration or a separate linked scheme. The answer decides
whether e-Shram gets a `benefit.annual_value_inr` or is modelled purely as a
`prerequisites` entry on the other schemes.

## 2. PM-SYM (Pradhan Mantri Shram Yogi Maandhan)

- **Primary:** `maandhan.in` — official scheme portal, eligibility page
- **Secondary:** `labour.gov.in` — scheme notification / gazette

**? Focus on the exclusions.** Contributory pension schemes of this type
commonly exclude members of other statutory schemes and income-tax payers.
Find the authoritative list and cite it — that is a category of rule to go
looking for, not a rule to assume.

## 3. PMSBY (Pradhan Mantri Suraksha Bima Yojana)

- **Primary:** `jansuraksha.gov.in` — PMSBY rules
- **Secondary:** Department of Financial Services, `financialservices.gov.in`

**? Check:** whether cover is per person or per bank account, whether auto-debit
consent is required, the renewal cycle, and how it interacts with PMJJBY — if a
worker should hear about both together, that is worth knowing before the
conversation flow is built.

## Precision that matters

- **Income:** "family income" and "personal income" are different rules. Record
  which one the scheme text actually says, in `pass_hi`/`fail_hi` too.
- **Age bands:** note whether bounds are inclusive. `between = [18, 40]` is
  inclusive of both in this engine.
- **Occupation:** use the categories the scheme itself defines, not ours.
- **Land holding:** always with units.
- **Documents:** the exact names the office asks for, not paraphrases.
