# Checkpoint — 9 September 2026

Supersedes `outputs/resume-checkpoint.md` in the 8 September Codex workspace.

---

## 1. What is deployed

**Live release: `sathi-20260909T032918Z`** on EC2 `13.206.84.69`
(instance `i-01da4c2ab1f689d8b`), activated 2026-09-09.

Three releases were activated today, in this order:

| Release | Contents | Evidence |
|---|---|---|
| `sathi-20260908T152844Z` | The seven-scheme expansion, as staged by the previous session | Staged suite rerun with an explicit status record: `/tmp/sathi-recheck-20260908T152844Z.log`, ends `all checks passed` + `EXIT_STATUS=0` |
| `sathi-20260908T214843Z` | The above plus the first source-review pass | Staged suite: `/tmp/sathi-check-20260908T214843Z.log`, `all checks passed` + `EXIT_STATUS=0`, 2,109 paths per language |
| `sathi-20260909T032918Z` | **Current.** Adds the browser-pass findings: the widow rate restored from myScheme, and the no-other-pension eligibility bar on both pensions | Staged suite: `/tmp/sathi-check-20260909T032918Z.log`, `all checks passed` + `EXIT_STATUS=0` |

The first was activated because the previous session had staged and
checksum-verified it but never confirmed the test run finished. Its log ended
with a success line but recorded no exit status, so the suite was rerun with one
before anything touched production, per the standing instruction.

**Verification after each activation** (`/tmp/sathi-verify-live.py`, exit 0):

- Telegram API authentication OK — bot `@YojanaSathiBot`
- WhatsApp local verification handshake OK
- Public HTTPS certificate valid; unsigned webhook POST rejected with 403
- Existing SQLite database `PRAGMA quick_check` = ok, read-only

**Preserved, confirmed by inspection:** `/etc/sathi/sathi.env` unchanged
(sha256 compared before and after by the activation script itself),
`/var/lib/sathi/sathi.db` unchanged at 151,552 bytes and its original mtime,
all pre-existing backup directories intact. New rollback backups created:
`/opt/sathi-backup-20260908T152844Z`, `/opt/sathi-backup-20260909T032918Z`.

**Services:** `sathi`, `sathi-whatsapp`, `caddy` — all `active (running)`,
`NRestarts=0`. Exactly one Telegram poller (`39851`) and one WhatsApp listener
(`39852`). No second poller was started at any point.

**Candidate integrity, checked before deploying each one:** archive SHA-256
matched the recorded value, all 60 manifest hashes verified, and the packaged
files were byte-identical to the working tree in `E:\project Scheme Sathi`.

---

## 2. Exact commands to try

Telegram: <https://t.me/YojanaSathiBot>. Hindi is the default; `/language`
switches. WhatsApp webhook host: <https://13.206.84.69.nip.io/>.

| Send | What should happen |
|---|---|
| `/start` | Language picker, then consent, then the intake questions |
| `/demo` | **Start here.** Fixed fictional profiles run through the real rule calculation. Every reply is labelled a demonstration and says review is pending. No session is opened and nothing is logged. |
| `/schemes` | All seven schemes, one message each, with the official source URL and the date it was checked. Each says it is not yet verified. |
| `/language` | Switches Hindi ⇄ English mid-conversation without losing answers |
| `/privacy` | What is and is not stored |
| `/about`, `/help` | Orientation |
| `/clear` | Deletes this session's messages — **only those under 48 hours old**, which is Telegram's limit, and the reply says so |
| `/clearall` | Wider delete; distinguishes "already deleted" from "too old" |
| `/cancel` | Drops the profile immediately |

**Expected result of a full real screening today: every scheme answers "we could
not check this yet."** That is correct, not a fault — see section 3. Walk the
whole intake anyway; the questions, the read-backs, the document checklist and
the generated application pack are all real.

Worth testing specifically, because they are new and untested by a human:

- The Uttarakhand pension follow-ups (`is_widow`, family income-or-BPL, **already
  receiving another pension** — new today, local selection). Pick Uttarakhand as
  your state to see them; pick another state and they should be skipped.
- Answer "yes" to *already receiving another pension* and both pensions should
  turn INELIGIBLE with a message telling you to ask which single pension suits
  you, not a flat refusal.
- The Ujjwala questions (woman applicant, household LPG, declaration).
- "Don't know" on any follow-up — the answer must stay unknown, never default.
- The same run in English, checking no Devanagari appears on a button.

---

## 3. Which schemes support real screening

**None. All seven are demonstration-and-questions only.**

Every file still carries `verified_by = "unconfirmed — PENDING HUMAN
VERIFICATION"`, so the engine returns `UNKNOWN` for every scheme to every
worker, contributes ₹0 to every dashboard number, and says so at startup. That
gate is enforced in code and asserted by tests, not merely documented.

| Scheme | Source-confirmed 9 Sep | Blocking gap |
|---|---|---|
| PMJJBY | ✅ every value verbatim | Human sign-off |
| PMUY / Ujjwala | ✅ every value verbatim | Human sign-off |
| UK old-age pension | ✅ every value verbatim | Human sign-off |
| PMSBY | ✅ (partial-disability wording row now closed) | Human sign-off; entry-at-exactly-70 conflict |
| e-Shram | ✅ age and income rows now closed against the current FAQ | Human sign-off; farmer scope |
| PM-SYM | ✅ inclusive ₹15,000 ceiling closed on the ministry page | Human sign-off; NPS scope, worker status |
| UK widow pension | ✅ rate and eligibility, via myScheme | Human sign-off; the no-other-pension bar is not on the department's page |

`/demo` output is fictional throughout and is never written to the impact
database. Nothing in this project claims a benefit was delivered because a
profile matched a rule.

---

## 4. Remaining human decisions and external blockers

**Blocked on Avinash, in priority order:**

1. **AgentFoundry — still the top risk, and now demonstrably hard.** The
   submission form has a **required** checkbox reading *"Built using
   AgentFoundry (AF), the official IDE"*. The submission cannot be filed without
   it. [Discussion #13](https://github.com/karlmehta/code-for-a-billion/discussions/13)
   is still **Unanswered, 0 comments**. Escalate through another channel —
   the CFI registration contact, or the AgentFoundry sign-up itself.
   *One useful data point found today:* AgentFoundry is a downloadable IDE with
   BYOK support that advertises "we auto-detect your existing tools", not a
   cloud-only sandbox. So opening this repo in it is a normal thing to do — but
   that is an argument for your case, **not** an answer from the organisers, and
   only they can decide whether it satisfies the checkbox.
2. **Confirm the "not already receiving another pension" condition at the
   office.** It comes from myScheme, not from the department's own service
   pages, and it now decides verdicts for both pensions. Most consequential
   unconfirmed fact in the repo.
3. **Settle whose income the ₹4,000 line means** — the department page says the
   applicant's, myScheme says the family's. The code asks the stricter family
   reading and tells the worker the sources differ.
3b. **Confirm the widow rate.** myScheme states ₹1,500/month, which is enough to
   ship as unsigned data but not to sign. Its own citation is the state
   guidelines page 16 (a 320 MB scan), or use the 21/04/2021 rate GO
   No. 40/XVII-2/22-19(05) 2019-T.C.
4. **Decide PM-SYM's NPS scope** — plain NPS, or government-funded NPS only. The
   current broader exclusion can wrongly turn away someone eligible.
5. **Sign the schemes** — `docs/VERIFICATION.md`, helped by the quoted wording
   in `docs/SOURCE_REVIEW_2026-09-09.md`.
6. **Hindi review by a native speaker.** Never done. Both string files are
   Claude-drafted.
7. **Partner outreach and users.** Unchanged, and entirely yours.

**On browser automation:** the previous session's Chrome was blocked by an
administrator policy. This session used the in-app browser instead, which worked
and is how myScheme and the legacy-TLS state sites were finally read. What still
has *not* happened is a real conversation on a real phone — hence section 2.

---

## 5. GitHub and submission status

**Four commits are ready locally on `audit/readiness-2026-09-08` and are NOT
pushed.** `git push` hung on Git Credential Manager, which cannot prompt from a
non-interactive session. Run this yourself:

```bash
git -C "E:/project Scheme Sathi" push -u origin audit/readiness-2026-09-08
```

| Commit | What |
|---|---|
| `fd8df7c` | Add four schemes, and the questions they turned out to need — the expansion exactly as deployed |
| `46104a3` | Stop quoting a pension rate whose source went 404 — first source-review pass |
| `3de4ca6` | Write down what the entry form actually asks for |
| `0fb38a8` | Find the pension rule a fetcher could not see — browser pass |
| `a8b1819` | Point the checkpoint at the release that is actually running |

The split is deliberate: the first commit is byte-for-byte what was staged and
tested on the server, so it can be reviewed against the deployed release; the
second is only today's changes.

**The hackathon entry is NOT submitted, and must not be until item 1 above is
resolved.** Requirements as rechecked on 9 September, recorded in
`docs/SUBMISSION_DRAFT.md`:

- **Scale and severity of the problem is 50% of the score** — the largest
  available gain, and it is writing, not code.
- Deployment and impact data is 25%, and the field is optional.
- The track dropdown has no "Livelihood for the Uneducated" option (Agriculture,
  Health, Education, Financial Inclusion, Governance, Climate, Other), although
  the site lists that impact area and names "benefits access" in it. **Ask which
  value to select.**
- A working demo URL is required. Because no scheme is signed, the video should
  show `/demo` and explain the gate honestly rather than implying live verdicts.

---

## 6. Files and commands

**Changed today** (all in `E:\project Scheme Sathi`):

```
data/schemes/uk_widow.toml      benefit amount -> "TODO"; exclusive_group
data/schemes/uk_old_age.toml    exclusive_group
sathi/core/schemes.py           optional benefit.exclusive_group + accessor
sathi/rules/engine.py           total_value grouping; value_totals(); self-checks
sathi/render/templates.py       calls engine.value_totals
sathi/pack/pack.py              calls engine.value_totals
tests/test_schemes.py           KNOWN_STUBS gate + rot check
tests/test_expansion.py         pension-overlap regression; fixture clears stubs
tests/test_rule_boundaries.py   fixture clears stubs
tests/test_all_paths.py         fixture clears stubs; 2,000-path coverage floor
README.md                       seven schemes; real counters; the TODO admitted
docs/SOURCE_REVIEW_2026-09-09.md   NEW — the review packet for sign-off
docs/SCHEME_AUDIT.md            rows closed by the 9 Sep re-check
docs/SCHEME_EXPANSION.md        overlap done; widow amount withdrawn
docs/VERIFICATION.md            pointer to the review packet
docs/SUBMISSION_DRAFT.md        what the official form actually requires
docs/CHECKPOINT_2026-09-09.md   NEW — this file
```

**Local suite:** `py -3 check.py` → 18 module self-checks, 15 test files, 1,344
walked paths, 214,326 rule comparisons, 3,024 pension/PMUY condition
combinations, plus a direct check that two eligible profiles between them are
offered every document of every scheme in both languages. Exit 0.

**Server:**

```bash
# read-only status
ssh -i ~/.ssh/sathi_aws -o StrictHostKeyChecking=yes ubuntu@13.206.84.69 \
  'systemctl show sathi sathi-whatsapp caddy -p ActiveState -p NRestarts; \
   python3 -c "import json;print(json.load(open(\"/opt/sathi/release-manifest.json\"))[\"release\"])"'

# live checks (needs sudo: reads the service environment)
ssh ... 'sudo python3 /tmp/sathi-verify-live.py'

# rollback to the previous release
ssh ... 'sudo systemctl stop sathi sathi-whatsapp && \
  sudo mv /opt/sathi /opt/sathi-rolledback-$(date -u +%Y%m%dT%H%M%SZ) && \
  sudo mv /opt/sathi-backup-20260909T032918Z /opt/sathi && \
  sudo systemctl start sathi sathi-whatsapp'
```

---

## 7. Next steps, in order

1. Push the two commits (section 5).
2. Chase the AgentFoundry answer. Nothing else unblocks the submission.
3. Confirm the no-other-pension bar and the income scope at the office — both
   now change verdicts.
4. Test `/demo` and a full screening on your own phone, in both languages.
5. Write the Problem section with sourced numbers — 50% of the score.
6. Work through `docs/VERIFICATION.md` using the quoted wording in
   `docs/SOURCE_REVIEW_2026-09-09.md`.
7. Hindi review with a native speaker.
8. Partner outreach — the deploy gate of 11 Oct 2026 needs real users, and five
   weeks of usage cannot be retrofitted.

**Do not claim this project is complete.** The software runs, is deployed and is
tested; the eligibility review is unfinished by design, no worker has been given
a verdict, and the submission is blocked on an unanswered eligibility question.
