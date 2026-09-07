# Human review checklist — language, comprehension and device behavior

Prepared **8 September 2026**. **No independent native-speaker Hindi review is
claimed.** Automated key/placeholder checks cannot approve natural language or
prove comprehension. Every box below starts unchecked.

Reviewer name: __________  Language competence: __________

Date: __________  Repository commit: __________  Device/channel: __________

Use fictional profiles and `--no-db` previews for the first pass. Then review
on an actual low-cost Android phone with large text enabled and an adult test
reader who voluntarily agrees. Keep language review separate from scheme-value
sign-off in [VERIFICATION.md](VERIFICATION.md).

## Priority 1 — wording that could change a decision

- [ ] Read `consent.ask` in `data/strings_hi.toml` and
      `data/strings_en.toml` aloud. Explain participation, logging, stopping and
      provider privacy without promising anonymity or a government service.
- [ ] Confirm UNKNOWN is understood as “we cannot determine this”, not refusal,
      rejection, approval or a request to guess a missing answer.
- [ ] Confirm “eligible” is understood as a preliminary rule result, not a
      department's final decision or guaranteed payment.
- [ ] Review income frequency and boundaries, zero income, age, tax, bank
      account, EPFO/ESIC and NPS. Acronyms need everyday explanations; NPS must
      remain a separate question.
- [ ] Review the tax-Yes confirmation: changing income, changing the tax answer
      and keeping both must be neutral and understandable. It must not pressure
      a low-income worker into answering No.
- [ ] Review benefit wording: future pension, contribution/premium and
      conditional insurance cover remain distinct. A gateway registration must
      not sound like a promised cash payment.
- [ ] Review scheme names, exclusions, required documents, application location
      and renewal text in both languages against the signed source worksheet.
      Translation approval does not certify the government facts.

## Priority 2 — whole-flow Hindi/English parity

- [ ] Language picker, consent, state, typed age and occupation labels make sense
      to a first-time reader; the bilingual picker is intentionally bilingual.
- [ ] Try “mazdoor”, “mistri”, “driver”, an unfamiliar occupation and a spelling
      mistake. A category suggestion is confirmed; unsupported text gets a
      usable recovery, not a confident invented occupation.
- [ ] Review income/land/family buttons, “none”, “next”, “don't know” and the
      selected-state indication. Read truncated WhatsApp labels on the phone.
- [ ] Switch with `/language` during intake and after results. Answers and rule
      results must remain the same while visible prompts/buttons/pack labels
      change language consistently.
- [ ] Verify placeholders render actual values: no `{name}`, `{income}`, raw
      TOML keys, Unicode replacement characters or unintended missing text.
- [ ] Review answer recap, known schemes, pending-verification explanation,
      document possession/missing-document text and closing message aloud.
- [ ] Review `/start`, `/language`, `/schemes`, `/privacy`, `/about`, `/help`,
      `/clear`, `/clearall`, `/cancel` in the channel where supported. Deletion
      wording must match that channel's actual limitations.
- [ ] Hindi flow contains no unexplained English sentences; English flow contains
      no accidental Hindi sentences. Official acronyms, URLs and bilingual
      language-selection text are deliberate exceptions, not automatic failures.

## Priority 3 — recovery and physical-device checks

- [ ] An old button or repeated tap does not record a new unintended answer.
- [ ] Invalid age such as `-5`, `9.5`, huge input and mixed text is rejected
      understandably; valid Devanagari digits such as `३०` work.
- [ ] Restart/cancel instructions are visible. Do not invent a universal Back
      button if the current screen only supports restarting.
- [ ] Telegram inline keyboards and WhatsApp list/button messages fit the screen;
      selected labels remain distinguishable after shortening.
- [ ] The actual received attachment opens, Hindi characters survive, and its
      format matches its filename. A terminal preview upload marker is not this
      device check.
- [ ] Use large system text and low brightness; check contrast, line wrapping,
      tappable targets and whether instructions depend on color alone.
- [ ] On a shared phone, the next person cannot casually see the previous
      participant's answers; any channel deletion limitations are explained.

## Record findings and approval

| File/key or screen | Hindi/English | Meaning intended | Issue | Proposed wording | MATCH / CHANGE / NEEDS SOURCE REVIEW |
|---|---|---|---|---|---|
| blank | blank | blank | blank | blank | blank |

Use fictional examples only; do not paste a worker's chat, identity or documents.
After changes, the maintainer runs `python3 check.py` and the reviewer rereads the
affected screen in both languages. Record unresolved safety-critical wording as
a blocker. Finish with an actual human statement:

“I reviewed the listed files/screens at commit __________. Items __________
remain unresolved. My approval covers __________ language/device behavior;
it does not certify unreviewed scheme values or real-world impact.”

Human name/signature: __________  Date: __________
