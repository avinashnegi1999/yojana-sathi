# AgentFoundry — eligibility gate and legitimate continuation

**Checked 7 September 2026. Status: BLOCKED pending a truthful eligibility basis.**
Opening this repository in an IDE is technically possible. It does not establish
that the hackathon accepts work originally developed elsewhere.

## What is verified

| Question | Finding | Official source |
|---|---|---|
| Is AF mandatory? | Yes: it is an eligibility condition, not merely a sponsor recommendation. | [Judging eligibility](https://github.com/karlmehta/code-for-a-billion/blob/main/JUDGING.md) |
| Does the organizer describe starting inside AF? | Yes, the participation instructions say to start/create the project there. They do not explicitly resolve an existing-repo exception. | [CFI event](https://codeforindia.org/hackathon) |
| Can the IDE open an existing code folder? | Yes: project-tab `+`, then select a folder; framework/tooling detection requires no project configuration. This is a product capability, not competition approval. | [AF getting started, section 3](https://wiki.agentfoundry.me/get-started#3-add-a-project) |
| Is a checkbox required? | Yes: `Built using AgentFoundry (AF), the official IDE`, with `required: true`. The solution field also asks how AF was used. | [Actual YAML form](https://github.com/karlmehta/code-for-a-billion/blob/main/.github/ISSUE_TEMPLATE/submission.yml) |
| Must commit one originate in AF? | Not resolved by the reviewed public rules. Wording creates a material origin risk. | [CFI participation](https://codeforindia.org/hackathon) |
| Can meaningful later development qualify? | No explicit organizer allowance found. Obtain a written answer describing this repository's real history. | [Organizer Q&A channel](https://github.com/karlmehta/code-for-a-billion/discussions) |
| AF project URL, export or trace upload required? | No dedicated fields in the current form. No public mandatory artifact format was found. This does not establish how judges verify a declaration. | [Actual YAML form](https://github.com/karlmehta/code-for-a-billion/blob/main/.github/ISSUE_TEMPLATE/submission.yml) |
| Qualification versus final submission? | Registration describes creating a project in AF; final eligibility also requires AF. No separate exception or qualification-stage exemption was found. | [CFI registration](https://codeforindia.org/hackathon/register), [judging eligibility](https://github.com/karlmehta/code-for-a-billion/blob/main/JUDGING.md) |

The AF wiki still uses its earlier **CodeNow** name in places. The current
[AgentFoundry site](https://agentfoundry.me/) links that wiki. Do not confuse
AgentFoundry's optional agent SDK/runtime features with an established hackathon
runtime requirement.

## Current Yojana Sathi status

The local Git history and `docs/BUILD_LOG.md` record an existing Python project.
The current repository has a standard-library runtime, public Apache-2.0 source,
Telegram and WhatsApp adapters, deterministic rules, tests and deployment files.
There is no verified AF origin, AF development session, approved import, or
organizer exception in the evidence inspected. This audit itself is not AF use.

Project memories `project_codeforindia_hackathon.md`, `project_saans.md` and
`project_scheme_sathi.md` recover the predecessor Saans history and earlier AF
question. They also warn that whether an earlier email was sent is unverified.
No mailbox was inspected here. Do not claim a message was sent or answered.

## Smallest legitimate technical path

If the organizer accepts continuation, use AF as the development IDE for this
same repository. Keep the deterministic core, channel adapters and deployment
architecture. The documented folder workflow requires no AF manifest, SDK,
database, runtime model, rewrite or fabricated provenance file.

Repository preparation is already present: `AGENTS.md` / `CLAUDE.md`, Python
requirements, `check.py`, Dockerfile and an existing Git history. This worksheet
supplies the remaining handoff. Do not generate `.codenow` traces, backdate
commits, rename another tool's output as AF evidence, or alter human scheme
sign-offs to make the demo look ready.

If the answer requires AF origin, keep this repository's provenance intact and
ask whether any explicitly disclosed reuse is permitted. An eligible separate
entry or withdrawal from this event is a human scope decision; a cosmetic
recreation of the repository would not resolve the truthfulness issue.

## Contact attempts — dated, because silence has to be evidenced

# ! The point of this table is not admin. If no answer ever comes, the honest
# ! position is "I asked repeatedly, in public and in private, through every
# ! published channel, and nobody replied" — and that is only defensible if it
# ! is written down as it happens, with dates, rather than reconstructed later.
# ! An unanswered question asked four times in the open is a defensible record.
# ! An unasked one is not, and neither is a quietly ticked checkbox.

| Date | Channel | What happened |
|---|---|---|
| 2026-08 | [Discussion #13](https://github.com/karlmehta/code-for-a-billion/discussions/13) | Asked publicly whether an existing repository can qualify through continued development in AgentFoundry. **Still 0 replies, 1 participant.** The organiser's own Q&A channel appears unattended. |
| 2026-09-12 | `hello@codeforindia.org` | **Hard bounce** — "the address couldn't be found, or is unable to receive mail". The domain's MX records resolve (IONOS), so mail is configured but that mailbox does not exist. This is the address published on both codeforindia.org and its `/contact` page, and linked as a `mailto:` from the site's own footer. |
| 2026-09-12 | `partners@codeforindia.org` | Sent. The second address on the same contact page. Awaiting reply. |

Routes not yet tried, in the order worth trying:

1. **Open an issue** on `karlmehta/code-for-a-billion` — issues are enabled and
   notify differently from Discussions, which is demonstrably unwatched.
2. **Karl Mehta on LinkedIn** (`linkedin.com/in/mehtakarl`, linked from his own
   GitHub profile). The hackathon is his; this is a published professional
   contact, not a dug-up one.
3. The contact form at `codeforindia.org/contact` — lowest odds, since it most
   likely posts to the mailbox that just bounced.

**The standing rule, unchanged: do not tick the "Built using AgentFoundry"
confirmation without an answer worth repeating out loud to a judge.** If the
answer never arrives, not submitting is a real option and costs this project
nothing that matters — the bot is live, the schemes are signed, and the
repository stands on its own.

## Manual steps for Avinash

1. **Done, twice — see the contact table above.** Asked publicly in Discussion
   #13 (no reply) and by email on 2026-09-12 (`hello@` bounced, `partners@`
   sent). Next: chase at seven days, then an issue on the hackathon repository.
   Keep every answer and its date here. Do not treat another participant's
   checked checkbox as organizer permission.
2. Complete/confirm [CFI registration](https://codeforindia.org/hackathon/register)
   and AF signup with your own account. The organizer advertises free entry and
   1M smart-code tokens. Check the actual free allowance in the account; no paid
   subscription is needed merely to perform this proposed continuation.
3. Follow the [official Linux installation guide](https://wiki.agentfoundry.me/get-started):
   download its AppImage through the official link, make the downloaded file
   executable, and launch it. The guide's project-tab `+` opens a selected folder.
   Select `/run/media/avinash/Data/project Scheme Sathi`. No installation or login
   was performed by this audit. Do not import production credentials into the IDE
   just to obtain development evidence; ordinary checks need none.
4. In AF's terminal, establish the branch and baseline with `git status`,
   `python3 --version` and `python3 check.py`. Use a separate local branch for
   subsequent work. Read this repository's agent instructions before asking AF
   to change anything.
5. After an acceptable organizer answer, perform a real outstanding task in AF:
   for example, fix a reproduced pilot defect with a regression test, or implement
   a reviewer-approved source correction. Choose useful work that actually
   remains; do not invent defects or extra functionality to create activity.
6. Save honest evidence: dates, task, starting/ending commit IDs, test output and
   a short screen recording of AF working on the repository. Redact secrets,
   messaging identifiers and worker data. Keep any native traces private until
   reviewed. This evidence pack is our recommendation, not a published required
   export format. Record an AF project URL only if the platform supplies one.
7. Run `python3 check.py`, inspect the resulting diff, and keep normal Git
   history. Describe exactly which development occurred outside AF and inside
   AF. Tick the final checkbox only when that statement is true and consistent
   with the organizer's answer. Ask what evidence to attach if the form changes.

## Organizer question — draft only, not sent

Subject: Code for a Billion — existing Python repository and AgentFoundry eligibility

I am entering Yojana Sathi, a Hindi/English welfare-scheme screening application,
for Livelihood for the Uneducated. Its public repository is
https://github.com/avinashnegi1999/yojana-sathi. Initial development occurred
outside AgentFoundry. Eligibility uses deterministic Python rules; an LLM never
decides eligibility or invents benefit values.

May I open this existing repository in AgentFoundry and perform substantive,
documented further development there, while disclosing its earlier origin, and
truthfully satisfy the required AF confirmation? Or must development originate
in AF from the first commit? Are there minimum AF development, runtime/SDK,
project URL, export, trace or other proof requirements? Do these differ between
registration/qualification and final submission?

Your current site lists Livelihood for the Uneducated, but the final GitHub form
does not. Which category should I select? How should an Apache-2.0 project be
contributed to the Code for India GitHub organization, and what is the exact
15 November closing time/timezone?

## What this audit cannot do

It cannot establish organizer intent, accept participation/IP terms on Avinash's
behalf, create account evidence that does not exist, certify prior AF work, or
sign the final declaration. It has not sent the draft, registered, installed AF,
imported the repository, uploaded traces, transferred the repository, or pushed
changes. These remaining actions require the owner's account and/or an actual
organizer decision, not additional application code.
