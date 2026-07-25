-- ===================================================
-- RESUMatch.ai — Database Schema
-- ===================================================

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    UNIQUE NOT NULL,
    email         TEXT    UNIQUE NOT NULL,
    password_hash TEXT    NOT NULL,
    full_name     TEXT,
    company       TEXT,
    role          TEXT    DEFAULT 'recruiter',
    bio           TEXT,
    created_at    TEXT    DEFAULT (datetime('now')),
    last_login    TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    name            TEXT,
    email           TEXT,
    phone           TEXT,
    resume_filename TEXT    NOT NULL,
    resume_path     TEXT    NOT NULL,
    file_type       TEXT,
    raw_text        TEXT,
    parsed_data     TEXT,
    is_duplicate    INTEGER DEFAULT 0,
    quality_score   REAL    DEFAULT 0,
    status          TEXT    DEFAULT 'Pending',
    job_title       TEXT,
    github          TEXT,
    linkedin        TEXT,
    match_score     REAL    DEFAULT 0,
    jd_id           INTEGER,
    created_at      TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS job_descriptions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    title        TEXT    NOT NULL,
    company      TEXT,
    description  TEXT    NOT NULL,
    requirements TEXT,
    created_at   TEXT    DEFAULT (datetime('now')),
    updated_at   TEXT    DEFAULT (datetime('now')),
    created_date TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS scores (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id        INTEGER NOT NULL,
    jd_id               INTEGER,
    user_id             INTEGER NOT NULL,
    overall_score       REAL    DEFAULT 0,
    skill_score         REAL    DEFAULT 0,
    experience_score    REAL    DEFAULT 0,
    education_score     REAL    DEFAULT 0,
    keyword_score       REAL    DEFAULT 0,
    matched_skills      TEXT,
    missing_skills      TEXT,
    extra_skills        TEXT,
    summary             TEXT,
    suggestions         TEXT,
    interview_questions TEXT,
    status              TEXT    DEFAULT 'pending',
    created_at          TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)      REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    created_at   TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)      REFERENCES users(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE(user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS notes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    note_text    TEXT    NOT NULL,
    created_at   TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)      REFERENCES users(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    tag_name     TEXT    NOT NULL,
    created_at   TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id)      REFERENCES users(id),
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    message    TEXT    NOT NULL,
    type       TEXT    DEFAULT 'info',
    is_read    INTEGER DEFAULT 0,
    created_at TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
