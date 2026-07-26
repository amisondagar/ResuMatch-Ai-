-- RESUMatch.ai - Supabase PostgreSQL Database Schema

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      VARCHAR(255) UNIQUE NOT NULL,
    email         VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(255),
    company       VARCHAR(255),
    role          VARCHAR(50) DEFAULT 'recruiter',
    bio           TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidates (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255),
    email           VARCHAR(255),
    phone           VARCHAR(100),
    resume_filename VARCHAR(255) NOT NULL,
    resume_path     TEXT NOT NULL,
    file_type       VARCHAR(50),
    raw_text        TEXT,
    parsed_data     TEXT,
    is_duplicate    INTEGER DEFAULT 0,
    quality_score   REAL DEFAULT 0,
    status          VARCHAR(50) DEFAULT 'Pending',
    job_title       VARCHAR(255),
    github          VARCHAR(255),
    linkedin        VARCHAR(255),
    match_score     REAL DEFAULT 0,
    jd_id           INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_descriptions (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title        VARCHAR(255) NOT NULL,
    company      VARCHAR(255),
    description  TEXT NOT NULL,
    requirements TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scores (
    id                  SERIAL PRIMARY KEY,
    candidate_id        INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    jd_id               INTEGER,
    user_id             INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    overall_score       REAL DEFAULT 0,
    skill_score         REAL DEFAULT 0,
    experience_score    REAL DEFAULT 0,
    education_score     REAL DEFAULT 0,
    keyword_score       REAL DEFAULT 0,
    matched_skills      TEXT,
    missing_skills      TEXT,
    extra_skills        TEXT,
    summary             TEXT,
    suggestions         TEXT,
    interview_questions TEXT,
    status              VARCHAR(50) DEFAULT 'pending',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, candidate_id)
);

CREATE TABLE IF NOT EXISTS notes (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    note_text    TEXT NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tags (
    id           SERIAL PRIMARY KEY,
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    candidate_id INTEGER NOT NULL REFERENCES candidates(id) ON DELETE CASCADE,
    tag_name     VARCHAR(255) NOT NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id         SERIAL PRIMARY KEY,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    message    TEXT NOT NULL,
    type       VARCHAR(50) DEFAULT 'info',
    is_read    INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
