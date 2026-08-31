-- =====================================================================
-- Event log — append-only, counts only, no PII
-- =====================================================================
-- ! This is the 25% of the score that cannot be retrofitted. Every event lands
-- ! from the very first deployed session; instrumentation added in week 10
-- ! means weeks 6-9 simply do not exist as evidence.
--
-- ! There is no name, phone, Aadhaar, district, village or exact income column
-- ! here, and there must never be. A column that does not exist cannot be
-- ! filled in by a well-meaning patch at 2am.
--
-- ! No UPDATE and no DELETE is issued anywhere in the codebase against this
-- ! table. An impact number you can silently edit is not evidence.

CREATE TABLE IF NOT EXISTS events (
    event_id    TEXT PRIMARY KEY,   -- uuid4
    session_id  TEXT NOT NULL,      -- ! fresh uuid4 per conversation, NOT derived
                                    -- ! from the Telegram id. Two sessions by the
                                    -- ! same worker are unlinkable here by design.
    ts          TEXT NOT NULL,      -- ISO 8601 UTC
    event_type  TEXT NOT NULL,
    scheme_code TEXT,               -- nullable

    -- * Coarse dimensions only, for aggregates. Never free text, never exact.
    state       TEXT,               -- state, never district
    age_band    TEXT,               -- '18-25' | '26-40' | '41-59' | '60+' | 'under-18'
    occupation  TEXT,               -- enum from data/occupations.toml
    income_band TEXT,               -- enum from sathi/core/profile.py

    value_inr   INTEGER,            -- annual entitlement, on match events only
    channel     TEXT                -- 'telegram' | 'cli' | 'whatsapp'
);

CREATE INDEX IF NOT EXISTS idx_events_ts      ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_type    ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);

-- =====================================================================
-- Follow-ups — deliberately NOT joinable to events
-- =====================================================================
-- ? Opt-in (FOLLOWUP_SALT must be set). The 14-day "did you actually get it?"
-- ? question is the only real outcome measure available, and it needs a way to
-- ? message the same person again — which means holding a channel id.
--
-- ! Mitigations: the id is salted-hashed, no profile data sits beside it, there
-- ! is no session_id column so it cannot be joined back to `events`, and rows
-- ! are purged on completion or after 30 days, whichever comes first.

CREATE TABLE IF NOT EXISTS followups (
    id            TEXT PRIMARY KEY,   -- salted hash of the channel id
    channel       TEXT NOT NULL,
    due_ts        TEXT NOT NULL,      -- ISO 8601 UTC
    created_ts    TEXT NOT NULL,
    sent_ts       TEXT,               -- set once asked
    response      TEXT                -- 'yes' | 'no' | 'partial' | NULL
);

CREATE INDEX IF NOT EXISTS idx_followups_due ON followups(due_ts);
