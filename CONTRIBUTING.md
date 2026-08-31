# Contributing

## Adding or correcting a scheme rule — the important one

This is the contribution that matters most, and it needs no programming.

**Every value must be cited.** A pull request that changes a threshold, a ₹
amount, an age band, or an exclusion must include, for that value:

- a `source_url` deep-linking the **official** `.gov.in` page carrying it —
  not the site root, not a news article, not an aggregator, not a chatbot
- an updated `verified_on` date
- your name in `verified_by`

**PRs that change a rule without a source are closed.** This is not
bureaucracy. A wrong threshold sends a worker on a day-long trip to a CSC that
costs them a day's wages, and they usually do not come back for a second try.

If you cannot find an official source for a value, leave it as `"TODO"`. The
system reports "we could not check this" — which is honest and still useful.
Guessing is the one thing it must never do.

Read [`docs/SCHEME_AUTHORING.md`](docs/SCHEME_AUTHORING.md) first.

## Translations and Hindi wording

Every user-facing string is in the scheme files and `data/strings_hi.toml`.
Corrections from native and regional speakers are welcome and needed — the
whole project fails if the Hindi reads like a translated form. Say in the PR
which region's usage you are writing for.

## Code

```bash
python3 check.py    # must pass before you open a PR
```

- Python 3.11+, standard library only. A new dependency needs a line in the PR
  explaining what the stdlib could not do.
- No language model may be imported from `sathi/rules/`. Eligibility is
  deterministic; that boundary is the point of the project.
- Comment tags in use: `# !` important, `# *` section, `# TODO` task,
  `# ?` open question.

Sign off commits with `git commit -s` (DCO).

## Reporting a wrong result

Open an issue with the profile answers that produced it (**no personal
details** — ages and bands only) and what you expected. A wrong eligibility
result is the highest-priority bug class in this repo.
