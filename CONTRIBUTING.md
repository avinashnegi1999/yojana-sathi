# Contributing.

<br>

## Fix or add a scheme rule — the one that matters most.

No programming needed. Every changed value — a threshold, a ₹ amount, an age band, an exclusion — needs:

- a `source_url` deep-linking the **official** `.gov.in` page that states it. Not a site root, a news article, an aggregator or a chatbot.
- an updated `verified_on` date.
- a maintainer's sign-off with `python3 -m sathi.review <CODE>`. A hand-edited signature fails `tests/test_schemes.py`.

**A rule change without a source is closed.** A wrong threshold costs a worker a day's wage, and most don't come back.

No official source? Leave `"TODO"`. The bot says "we couldn't check this" — honest, and still useful.

Start with [`docs/SCHEME_AUTHORING.md`](docs/SCHEME_AUTHORING.md).

<br>

## Hindi wording.

Worker-facing text is in the scheme files and `data/strings_hi.toml`. Corrections from native and regional speakers are needed — the project fails if the Hindi reads like a translated form. Say which region's usage you write for.

<br>

## Code.

```bash
python3 check.py    # must pass before a PR
```

- Python 3.11+, standard library only. A new dependency needs one line on what the stdlib couldn't do.
- `sathi/rules/` may not import a language model. That boundary is the point of the project.
- Comment tags: `# !` important · `# *` section · `# TODO` task · `# ?` open question.
- Sign commits with `git commit -s` (DCO).

<br>

## Report a wrong result.

Open an issue with the answers that produced it — ages and bands only, **no personal details** — and what you expected. A wrong eligibility result is the highest-priority bug here.
