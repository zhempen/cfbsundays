-- CFB Sundays Tuesday email subscribers. Safe to run on every deploy.
CREATE TABLE IF NOT EXISTS subscribers (
  norm            TEXT PRIMARY KEY,   -- normalized address: one subscription per person
  email           TEXT NOT NULL,      -- address mail goes to (as typed, lowercased)
  schools         TEXT NOT NULL,      -- JSON array, 1 to 4 school names
  status          TEXT NOT NULL,      -- pending | active | unsubscribed
  pending_email   TEXT,               -- waiting on a confirmation click
  pending_schools TEXT,
  confirm_token   TEXT,
  confirm_sent_at INTEGER,            -- unix seconds
  confirms_today  INTEGER NOT NULL DEFAULT 0,
  unsub_token     TEXT NOT NULL,
  created_at      INTEGER NOT NULL,
  confirmed_at    INTEGER,
  last_sent_at    INTEGER             -- last Tuesday email
);
CREATE INDEX IF NOT EXISTS subscribers_confirm ON subscribers(confirm_token);
CREATE INDEX IF NOT EXISTS subscribers_unsub ON subscribers(unsub_token);

-- signup attempts per hashed IP, for rate limiting (rows older than a day are pruned)
CREATE TABLE IF NOT EXISTS attempts (
  ip_hash TEXT NOT NULL,
  at      INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS attempts_ip ON attempts(ip_hash, at);

-- one row per Tuesday send, so a re-run never mails the same week twice
CREATE TABLE IF NOT EXISTS sends (
  season  INTEGER NOT NULL,
  week    INTEGER NOT NULL,
  sent_at INTEGER NOT NULL,
  count   INTEGER NOT NULL,
  PRIMARY KEY (season, week)
);
