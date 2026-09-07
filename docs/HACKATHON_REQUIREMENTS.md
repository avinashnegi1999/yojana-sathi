# Hackathon requirements — evidence and submission gaps

Checked **7 September 2026** against the live organizer pages and submission
template. This is a repository readiness assessment, not organizer acceptance.
The earlier Saans entry and unresolved AgentFoundry question were recovered from
`docs/BUILD_LOG.md` and the project memory; current sources below take precedence.

## Requirement matrix

| Requirement | Official evidence | Current evidence / required action | Status |
|---|---|---|---|
| Deadline | [CFI timeline](https://codeforindia.org/hackathon#timeline): submissions and cloud deployment by **15 November 2026**; winners **5 December 2026** | Exact closing time/timezone is unpublished. The repo's 11 October milestone is internal, not an official deadline. | HUMAN ACTION REQUIRED |
| Track | [CFI challenges](https://codeforindia.org/hackathon): **Livelihood for the Uneducated**, including benefits access | Product purpose fits. Final issue dropdown differs; see conflict below. | PARTIAL |
| Participant eligibility | [CFI FAQ](https://codeforindia.org/hackathon): worldwide, solo or teams, students/professionals/independent developers; free | Avinash is a solo builder. Registration confirmation is not in repository evidence. | HUMAN ACTION REQUIRED |
| Registration | [CFI registration](https://codeforindia.org/hackathon/register) | Complete/confirm privately; fields described below. | HUMAN ACTION REQUIRED |
| AgentFoundry development | [Judging eligibility](https://github.com/karlmehta/code-for-a-billion/blob/main/JUDGING.md) | No established AF development evidence or organizer acceptance of this existing repository. [Migration worksheet](AGENTFOUNDRY_MIGRATION.md). | BLOCKED |
| Public source and setup README | [Hub instructions](https://github.com/karlmehta/code-for-a-billion) | [Repository](https://github.com/avinashnegi1999/yojana-sathi) confirmed public through GitHub on review date; README contains run commands. | COMPLETE |
| License | [CFI FAQ](https://codeforindia.org/hackathon): MIT or Apache-2.0 | `LICENSE` and `pyproject.toml` specify Apache-2.0. | COMPLETE |
| Contribution to CFI organization | [Registration consent](https://codeforindia.org/hackathon/register) names [code-for-india](https://github.com/code-for-india) | No contribution/transfer acceptance evidence. Ask which process is required; preserve repository history. | HUMAN ACTION REQUIRED |
| Cloud deployment | [CFI timeline](https://codeforindia.org/hackathon#timeline): any cloud | Repository runbook records AWS EC2 deployment. This research did not access the host or verify current availability. | PARTIAL |
| Accessible demo | [Issue form](https://github.com/karlmehta/code-for-a-billion/blob/main/.github/ISSUE_TEMPLATE/submission.yml) | README links Telegram; judge-access test and recorded demo remain unverified. WhatsApp has no public production number established. | PARTIAL |
| Demo format | [CFI participation](https://codeforindia.org/hackathon): 2–3 minute video **or** live link | Both are useful; both are not stated as mandatory. Video still needs recording. | HUMAN ACTION REQUIRED |
| Final submission | [Structured issue form](https://github.com/karlmehta/code-for-a-billion/issues/new?template=submission.yml) | No Yojana Sathi submission found among public hub issues on review date. File only after truthful confirmations are possible. | HUMAN ACTION REQUIRED |
| Problem statement and scale | [Issue template](https://github.com/karlmehta/code-for-a-billion/blob/main/.github/ISSUE_TEMPLATE/submission.yml) | README provides cited context; adapt draft to exact form fields and distinguish national need from actual project reach. | PARTIAL |
| Measured impact | [Judging rubric](https://github.com/karlmehta/code-for-a-billion/blob/main/JUDGING.md) | Metrics implementation exists. No real worker outcomes are established by this audit. Local tests and synthetic screens are not impact. | PARTIAL |

Status words correspond to COMPLETE / PARTIAL / BLOCKED / HUMAN ACTION REQUIRED;
a complete row does not imply the whole entry is eligible.

## Registration and final submission are different surfaces

The [registration page](https://codeforindia.org/hackathon/register) asks for
name, email, mobile/country code, country/city/region/postcode, impact area,
problem statement, problem size and GitHub handle. LinkedIn/X are additional
fields. It includes consent to contribute open source to the CFI organization.
Enter personal registration details there, not in this public repository.
Registration does not itself prove final acceptance or AF compliance.

The [final issue template](https://github.com/karlmehta/code-for-a-billion/blob/main/.github/ISSUE_TEMPLATE/submission.yml)
requires team/project name, member names and GitHub handles, a 2–5 sentence
problem, solution including AF usage, repository URL, demo URL, problem
scale/severity, category and contact email. Impact narrative is an optional
field although impact is judged. Three required confirmations cover AF use,
public repository/setup README and working judge-accessible demo. The issue is
public: choose the public contact deliberately. There is no dedicated AF project
URL, export upload, PDF, slide deck or team-size field in this template.

## Judging and defensible evidence

The [rubric](https://github.com/karlmehta/code-for-a-billion/blob/main/JUDGING.md)
allocates 25 points each to problem size, severity, solution quality and proven
impact. Independent judges' scores are averaged; ties favor impact, then size.
It explicitly values field outcomes and measured change. It specifies no
minimum worker count, compulsory impact duration or independent audit certificate.

For this entry, retain citations for the problem, show deterministic tests and
source-linked explanations for quality, and use [IMPACT.md](IMPACT.md) for
measurement definitions. A screening is not an approved benefit. Keep pension
amounts and contingent insurance cover separate. A 20–50 worker pilot is our
proposed evidence collection approach, not a competition quota.

## Official-source conflicts and unresolved restrictions

- The [hub README](https://github.com/karlmehta/code-for-a-billion) still says
  dates/deadline TBD and lists seven broad categories. The current CFI page gives
  the dates above and ten impact areas. Use the dated CFI timeline for planning,
  while asking the organizer to reconcile the submission surface.
- The actual issue template offers Agriculture, Health, Education, Financial
  Inclusion, Governance, Climate and Other. It lacks the named livelihood track.
  Ask which option preserves that track; Financial Inclusion is a plausible
  mapping, **not verified organizer guidance**.
- Public sources do not establish maximum team size, an age minimum, how CFI
  receives the code, a separate qualification round, AF import eligibility,
  mandatory runtime SDK, or a permitted share of work predating AF. Absence of a
  published restriction is not permission. Resolve material uncertainty with CFI.
- No source reviewed makes WhatsApp production approval a condition of entry.
  It remains a channel deployment gate if a public WhatsApp demonstration is
  promised. Government scheme verification remains this product's safety gate.

## Priorities before submission

1. Obtain a written AF eligibility answer and track/category mapping.
2. Confirm registration and the CFI organization contribution process.
3. Complete human scheme/Hindi review, then collect voluntary pilot evidence.
4. Check the cloud bot from an independent account and publish an honest demo.
5. Re-read the live rules/form, fill the submission draft, and save the actual
   submitted issue URL and organizer acknowledgement when they exist.

No organizer was contacted, no registration was submitted, and no acceptance is
claimed by this document.
