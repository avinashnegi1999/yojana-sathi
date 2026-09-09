# Official source text — snapshots

One file per scheme, holding the wording of the government page each rule in
[`data/schemes/`](../../schemes/) was transcribed from, as it read on the date
in the file header.

This exists so that anyone — a reviewer, a judge, or someone who forks this
repo — can audit a rule without leaving the repository. Open
`data/schemes/pmjjby.toml`, open `pmjjby.md` here, and compare. No page to
load, no site that might have moved.

| File | Scheme | Published by |
|---|---|---|
| `pmjjby.md` | Pradhan Mantri Jeevan Jyoti Bima Yojana | Dept. of Financial Services, Min. of Finance |
| `pmsby.md` | Pradhan Mantri Suraksha Bima Yojana | Dept. of Financial Services, Min. of Finance |
| `eshram.md` | e-Shram registration | Min. of Labour & Employment |
| `pm_sym.md` | Pradhan Mantri Shram Yogi Maandhan | Min. of Labour & Employment |
| `pmuy.md` | Pradhan Mantri Ujjwala Yojana | Min. of Petroleum & Natural Gas |
| `uk_old_age.md` | Uttarakhand old-age pension | Social Welfare Dept., Govt. of Uttarakhand |
| `uk_widow.md` | Uttarakhand widow pension | Social Welfare Dept., Govt. of Uttarakhand |

## Read this before trusting a file here

**The live page is authoritative. These are not.** Government rules change, and
a copy in a repository cannot tell you the day it stopped being true — that is
exactly how a worker ends up travelling to a bank on last quarter's premium.

That is what [`data/sources/*.json`](..) is for. Each carries a fingerprint of
the page plus a named pattern for every value we rely on, and:

```
python3 -m sathi.sources
```

re-reads the live pages and reports which of our claims they still support.
Run that before trusting anything in this folder, and after any long gap.

## What was and was not changed

Navigation menus, accessibility widgets, font-size controls, social links and
footers were stripped. Each page was then laid out for reading: one heading per
question, answers as separate paragraphs, the sites' `(i)`/`(ii)`/`a)` runs as
lists, and a table of contents where there are four or more questions. **Bold**
was added on amounts, ages, durations and cover periods, because those are what
a person scans a scheme page for.

**The substance is unedited** — no rewording, no summarising, no reordering,
nothing added or removed. Layout and emphasis are ours; every word is theirs.

Each file records a SHA-256 taken over its wording **with the markdown
stripped**, so re-laying a page out or emphasising a figure does not disturb it,
while an edit to what the page actually says does. The formatter asserts this on
every run — it caught itself gluing `**Rs.15000**or less` together once, which
is exactly the silent edit that check exists to prevent.

Two consequences of automated extraction, so nobody mistakes them for the
source's own doing: tables arrive flattened into lines, and the numbering the
site shows beside each question is sometimes lost. Where a question's number
matters, check it on the live page.

## Attribution and reuse

Every file is public information published by a ministry or state department of
the Government of India for citizens, reproduced here unmodified, with its
publisher, source URL and retrieval date. It is included to make an
open-source public-interest tool auditable.

Nothing here is a government endorsement of this project, and none of it is
approved by the departments named. Neither is it legal advice. If a rule here
disagrees with the department, the department is right.

## The gap this folder does not close

A snapshot proves what a page said. It does not prove the rule was read
correctly into `data/schemes/`, and it does not prove a person checked it. That
second thing is `verified_by` in each scheme file, and it is still pending on
all seven — see [`docs/VERIFICATION.md`](../../../docs/VERIFICATION.md) and
[`docs/SOURCE_REVIEW_2026-09-09.md`](../../../docs/SOURCE_REVIEW_2026-09-09.md).
