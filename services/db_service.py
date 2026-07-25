"""
services/db_service.py — Database Service Layer
ResumeMatch.ai

All SQLite operations are in this file.  Routes call these functions
instead of writing raw SQL everywhere — keeping the codebase clean
and easy to change.

TABLES CREATED:
  users, candidates, job_descriptions, scores,
  bookmarks, notes, tags, notifications

HOW IT WORKS:
  get_db()     → opens a SQLite connection for the current request
  init_db()    → creates all tables on first run
  Every other function is a named query (SELECT / INSERT / UPDATE / DELETE)

INTERVIEW TIP:
"We use the Repository / Service pattern — all data access is in one
place, so if we switch from SQLite to PostgreSQL later, we only change
this file."
"""

import sqlite3
import json
import os
from datetime import datetime
from flask import current_app, g


# ─── Connection Helpers ────────────────────────────────────────────────────

def get_db():
    """Return a database connection for the current request context."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row   # rows behave like dicts
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# ─── Database Initialisation ───────────────────────────────────────────────

def init_db():
    """Create all tables if they do not exist.  Safe to call every startup."""
    db_path = current_app.config['DATABASE_PATH']
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    c    = conn.cursor()

    c.executescript("""
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
    """)

    # Gracefully add missing columns if upgrading existing database
    cols_to_add = [
        ('status', "TEXT DEFAULT 'Pending'"),
        ('job_title', 'TEXT'),
        ('github', 'TEXT'),
        ('linkedin', 'TEXT'),
        ('match_score', 'REAL DEFAULT 0'),
        ('jd_id', 'INTEGER')
    ]
    for col_name, col_def in cols_to_add:
        try:
            c.execute(f"ALTER TABLE candidates ADD COLUMN {col_name} {col_def}")
        except Exception:
            pass  # column already exists

    try:
        c.execute("ALTER TABLE job_descriptions ADD COLUMN created_date TEXT")
    except Exception:
        pass

    conn.commit()
    conn.close()


# ─── Helper ────────────────────────────────────────────────────────────────

def _row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def _rows_to_list(rows):
    return [dict(r) for r in rows]


# ══════════════════════════════════════════════════════════════════════════
# USER OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def create_user(username, email, password_hash, full_name='', company=''):
    db = get_db()
    db.execute(
        """INSERT INTO users (username, email, password_hash, full_name, company)
           VALUES (?, ?, ?, ?, ?)""",
        (username, email, password_hash, full_name, company)
    )
    db.commit()


def get_user_by_email(email):
    db  = get_db()
    row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return _row_to_dict(row)


def get_user_by_username(username):
    db  = get_db()
    row = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return _row_to_dict(row)


def get_user_by_id(user_id):
    db  = get_db()
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return _row_to_dict(row)


def update_user(user_id, full_name, company, bio, role):
    db = get_db()
    db.execute(
        """UPDATE users SET full_name=?, company=?, bio=?, role=? WHERE id=?""",
        (full_name, company, bio, role, user_id)
    )
    db.commit()


def update_password(user_id, new_hash):
    db = get_db()
    db.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
    db.commit()


def update_last_login(user_id):
    db = get_db()
    db.execute("UPDATE users SET last_login=? WHERE id=?",
               (datetime.now().isoformat(), user_id))
    db.commit()


# ══════════════════════════════════════════════════════════════════════════
# CANDIDATE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def create_candidate(user_id, name, email, phone, filename, filepath,
                     file_type, raw_text, parsed_data, quality_score=0,
                     is_duplicate=0, status='Parsed', job_title='',
                     github='', linkedin='', match_score=0, jd_id=None):
    db = get_db()

    # Check if a candidate with the same name already exists for this user
    existing = db.execute(
        "SELECT id FROM candidates WHERE user_id=? AND LOWER(TRIM(name)) = LOWER(TRIM(?))",
        (user_id, name)
    ).fetchone()

    if existing:
        cand_id = existing['id']
        db.execute(
            """UPDATE candidates
               SET email=?, phone=?, resume_filename=?, resume_path=?, file_type=?,
                   raw_text=?, parsed_data=?, quality_score=?, is_duplicate=?,
                   status=?, job_title=?, github=?, linkedin=?, match_score=?, jd_id=?
               WHERE id=?""",
            (email, phone, filename, filepath, file_type, raw_text,
             json.dumps(parsed_data), quality_score, is_duplicate,
             status, job_title, github, linkedin, match_score, jd_id, cand_id)
        )
        db.commit()
        return cand_id

    cursor = db.execute(
        """INSERT INTO candidates
           (user_id, name, email, phone, resume_filename, resume_path,
            file_type, raw_text, parsed_data, quality_score, is_duplicate,
            status, job_title, github, linkedin, match_score, jd_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, name, email, phone, filename, filepath, file_type,
         raw_text, json.dumps(parsed_data), quality_score, is_duplicate,
         status, job_title, github, linkedin, match_score, jd_id)
    )
    db.commit()
    return cursor.lastrowid


def update_candidate_jd(candidate_id, jd_id, match_score=None):
    db = get_db()
    if match_score is not None:
        db.execute("UPDATE candidates SET jd_id=?, match_score=? WHERE id=?", (jd_id, match_score, candidate_id))
    else:
        db.execute("UPDATE candidates SET jd_id=? WHERE id=?", (jd_id, candidate_id))
    db.commit()


def update_candidate_status(candidate_id, user_id, status, match_score=None):
    """Update candidate status and optionally match score in SQLite."""
    db = get_db()
    if match_score is not None:
        db.execute(
            "UPDATE candidates SET status=?, match_score=? WHERE id=? AND user_id=?",
            (status, match_score, candidate_id, user_id)
        )
    else:
        db.execute(
            "UPDATE candidates SET status=? WHERE id=? AND user_id=?",
            (status, candidate_id, user_id)
        )
    # Also sync score record if exists
    db.execute(
        "UPDATE scores SET status=? WHERE candidate_id=? AND user_id=?",
        (status, candidate_id, user_id)
    )
    db.commit()


def get_candidate(candidate_id):
    db  = get_db()
    row = db.execute("SELECT * FROM candidates WHERE id=?", (candidate_id,)).fetchone()
    if row is None:
        return None
    d = dict(row)
    try:
        d['parsed_data'] = json.loads(d['parsed_data'] or '{}')
    except Exception:
        d['parsed_data'] = {}
    return d


def get_all_candidates(user_id):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM candidates WHERE user_id=? ORDER BY match_score DESC, created_at DESC",
        (user_id,)
    ).fetchall()
    result = []
    seen_names = set()
    for row in rows:
        d = dict(row)
        clean_name = (d.get('name') or '').strip().lower()
        if clean_name and clean_name in seen_names:
            continue
        if clean_name:
            seen_names.add(clean_name)
        try:
            d['parsed_data'] = json.loads(d['parsed_data'] or '{}')
        except Exception:
            d['parsed_data'] = {}
        result.append(d)
    return result


def delete_candidate(candidate_id, user_id):
    db = get_db()
    db.execute("DELETE FROM candidates WHERE id=? AND user_id=?",
               (candidate_id, user_id))
    db.commit()


def search_candidates(user_id, query):
    db   = get_db()
    like = f"%{query}%"
    rows = db.execute(
        """SELECT * FROM candidates
           WHERE user_id=? AND (name LIKE ? OR email LIKE ? OR raw_text LIKE ?)
           ORDER BY created_at DESC""",
        (user_id, like, like, like)
    ).fetchall()
    return _rows_to_list(rows)


def get_candidate_count(user_id):
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM candidates WHERE user_id=?", (user_id,)
    ).fetchone()[0]


# ══════════════════════════════════════════════════════════════════════════
# JOB DESCRIPTION OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def create_jd(user_id, title, company, description, requirements):
    db = get_db()
    try:
        cursor = db.execute(
            """INSERT INTO job_descriptions
               (user_id, title, company, description, requirements, created_at, created_date)
               VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (user_id, title, company, description, requirements)
        )
    except Exception:
        try:
            cursor = db.execute(
                """INSERT INTO job_descriptions
                   (user_id, title, company, description, requirements, created_at)
                   VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                (user_id, title, company, description, requirements)
            )
        except Exception:
            cursor = db.execute(
                """INSERT INTO job_descriptions
                   (user_id, title, company, description, requirements)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, title, company, description, requirements)
            )
    db.commit()
    return cursor.lastrowid


def get_jd(jd_id):
    db  = get_db()
    row = db.execute("SELECT * FROM job_descriptions WHERE id=?", (jd_id,)).fetchone()
    return _row_to_dict(row)


def get_all_jds(user_id):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM job_descriptions WHERE user_id=? ORDER BY created_at DESC",
        (user_id,)
    ).fetchall()
    return _rows_to_list(rows)


def update_jd(jd_id, title, company, description, requirements):
    db = get_db()
    db.execute(
        """UPDATE job_descriptions
           SET title=?, company=?, description=?, requirements=?,
               updated_at=?
           WHERE id=?""",
        (title, company, description, requirements,
         datetime.now().isoformat(), jd_id)
    )
    db.commit()


def delete_jd(jd_id, user_id):
    db = get_db()
    db.execute("DELETE FROM job_descriptions WHERE id=? AND user_id=?",
               (jd_id, user_id))
    db.commit()


# ══════════════════════════════════════════════════════════════════════════
# SCORE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def create_score(candidate_id, jd_id, user_id, overall_score, skill_score,
                 experience_score, education_score, keyword_score,
                 matched_skills, missing_skills, extra_skills,
                 summary, suggestions, interview_questions, status):
    db = get_db()
    jd_id_val = jd_id if jd_id is not None else 0
    # Delete any existing score for this candidate+JD pair
    db.execute(
        "DELETE FROM scores WHERE candidate_id=? AND (jd_id=? OR jd_id IS NULL OR jd_id=0)",
        (candidate_id, jd_id_val)
    )
    cursor = db.execute(
        """INSERT INTO scores
           (candidate_id, jd_id, user_id, overall_score, skill_score,
            experience_score, education_score, keyword_score,
            matched_skills, missing_skills, extra_skills,
            summary, suggestions, interview_questions, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (candidate_id, jd_id_val, user_id, overall_score, skill_score,
         experience_score, education_score, keyword_score,
         json.dumps(matched_skills), json.dumps(missing_skills),
         json.dumps(extra_skills), summary,
         json.dumps(suggestions), json.dumps(interview_questions), status)
    )
    db.commit()
    return cursor.lastrowid


def get_score(candidate_id, jd_id):
    db  = get_db()
    row = db.execute(
        "SELECT * FROM scores WHERE candidate_id=? AND jd_id=?",
        (candidate_id, jd_id)
    ).fetchone()
    if row is None:
        return None
    d = dict(row)
    for field in ['matched_skills','missing_skills','extra_skills',
                  'suggestions','interview_questions']:
        try:
            d[field] = json.loads(d[field] or '[]')
        except Exception:
            d[field] = []
    return d


def get_scores_for_jd(jd_id, user_id):
    """Return all scored candidates for a given JD, ordered by score."""
    db   = get_db()
    rows = db.execute(
        """SELECT s.*, c.name, c.email, c.phone, c.resume_filename,
                  c.file_type, c.quality_score, c.created_at as uploaded_at
           FROM scores s
           JOIN candidates c ON s.candidate_id = c.id
           WHERE s.jd_id=? AND s.user_id=?
           ORDER BY s.overall_score DESC""",
        (jd_id, user_id)
    ).fetchall()
    result = []
    for row in rows:
        d = dict(row)
        for field in ['matched_skills','missing_skills','extra_skills',
                      'suggestions','interview_questions']:
            try:
                d[field] = json.loads(d[field] or '[]')
            except Exception:
                d[field] = []
        result.append(d)
    return result


def update_score_status(score_id, status):
    db = get_db()
    db.execute("UPDATE scores SET status=? WHERE id=?", (status, score_id))
    db.commit()


def get_all_scores(user_id):
    db   = get_db()
    rows = db.execute(
        """SELECT s.*, c.name, c.email, c.resume_filename,
                  j.title as jd_title
           FROM scores s
           JOIN candidates c ON s.candidate_id = c.id
           JOIN job_descriptions j ON s.jd_id = j.id
           WHERE s.user_id=?
           ORDER BY s.overall_score DESC""",
        (user_id,)
    ).fetchall()
    score_list = _rows_to_list(rows)

    # Deduplicate by candidate so each candidate appears ONCE with their highest score
    unique = {}
    for s in score_list:
        cand_key = s.get('candidate_id') or s.get('name')
        if cand_key not in unique:
            unique[cand_key] = s
    return list(unique.values())


# ══════════════════════════════════════════════════════════════════════════
# BOOKMARK OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def toggle_bookmark(user_id, candidate_id):
    """Returns True if bookmarked, False if removed."""
    db  = get_db()
    row = db.execute(
        "SELECT id FROM bookmarks WHERE user_id=? AND candidate_id=?",
        (user_id, candidate_id)
    ).fetchone()
    if row:
        db.execute("DELETE FROM bookmarks WHERE user_id=? AND candidate_id=?",
                   (user_id, candidate_id))
        db.commit()
        return False
    else:
        db.execute("INSERT INTO bookmarks (user_id, candidate_id) VALUES (?, ?)",
                   (user_id, candidate_id))
        db.commit()
        return True


def get_bookmarks(user_id):
    db   = get_db()
    rows = db.execute(
        """SELECT b.*, c.name, c.email, c.resume_filename, c.quality_score
           FROM bookmarks b
           JOIN candidates c ON b.candidate_id = c.id
           WHERE b.user_id=?
           ORDER BY b.created_at DESC""",
        (user_id,)
    ).fetchall()
    return _rows_to_list(rows)


def is_bookmarked(user_id, candidate_id):
    db  = get_db()
    row = db.execute(
        "SELECT id FROM bookmarks WHERE user_id=? AND candidate_id=?",
        (user_id, candidate_id)
    ).fetchone()
    return row is not None


# ══════════════════════════════════════════════════════════════════════════
# NOTE OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def add_note(user_id, candidate_id, note_text):
    db = get_db()
    db.execute(
        "INSERT INTO notes (user_id, candidate_id, note_text) VALUES (?, ?, ?)",
        (user_id, candidate_id, note_text)
    )
    db.commit()


def get_notes(user_id, candidate_id):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM notes WHERE user_id=? AND candidate_id=? ORDER BY created_at DESC",
        (user_id, candidate_id)
    ).fetchall()
    return _rows_to_list(rows)


def delete_note(note_id, user_id):
    db = get_db()
    db.execute("DELETE FROM notes WHERE id=? AND user_id=?", (note_id, user_id))
    db.commit()


# ══════════════════════════════════════════════════════════════════════════
# TAG OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def add_tag(user_id, candidate_id, tag_name):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO tags (user_id, candidate_id, tag_name) VALUES (?, ?, ?)",
            (user_id, candidate_id, tag_name.strip().lower())
        )
        db.commit()
    except Exception:
        pass  # Ignore duplicate tags


def get_tags(user_id, candidate_id):
    db   = get_db()
    rows = db.execute(
        "SELECT * FROM tags WHERE user_id=? AND candidate_id=? ORDER BY tag_name",
        (user_id, candidate_id)
    ).fetchall()
    return _rows_to_list(rows)


def delete_tag(tag_id, user_id):
    db = get_db()
    db.execute("DELETE FROM tags WHERE id=? AND user_id=?", (tag_id, user_id))
    db.commit()


# ══════════════════════════════════════════════════════════════════════════
# NOTIFICATION OPERATIONS
# ══════════════════════════════════════════════════════════════════════════

def add_notification(user_id, message, notif_type='info'):
    db = get_db()
    db.execute(
        "INSERT INTO notifications (user_id, message, type) VALUES (?, ?, ?)",
        (user_id, message, notif_type)
    )
    db.commit()


def get_notifications(user_id, limit=20):
    db   = get_db()
    rows = db.execute(
        """SELECT * FROM notifications WHERE user_id=?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    ).fetchall()
    return _rows_to_list(rows)


def mark_notifications_read(user_id):
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
    db.commit()


def get_unread_count(user_id):
    db = get_db()
    return db.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id=? AND is_read=0",
        (user_id,)
    ).fetchone()[0]


# ══════════════════════════════════════════════════════════════════════════
# DASHBOARD STATISTICS
# ══════════════════════════════════════════════════════════════════════════

def get_dashboard_stats(user_id):
    """Return all stats calculated strictly from current active candidates."""
    db = get_db()

    total_candidates = db.execute(
        "SELECT COUNT(*) FROM candidates WHERE user_id=?", (user_id,)
    ).fetchone()[0]

    total_jds = db.execute(
        "SELECT COUNT(*) FROM job_descriptions WHERE user_id=?", (user_id,)
    ).fetchone()[0]

    shortlisted = db.execute(
        "SELECT COUNT(*) FROM candidates WHERE user_id=? AND LOWER(status)='shortlisted'",
        (user_id,)
    ).fetchone()[0]

    rejected = db.execute(
        "SELECT COUNT(*) FROM candidates WHERE user_id=? AND LOWER(status)='rejected'",
        (user_id,)
    ).fetchone()[0]

    pending = db.execute(
        "SELECT COUNT(*) FROM candidates WHERE user_id=? AND (LOWER(status)='pending' OR status IS NULL OR LOWER(status) NOT IN ('shortlisted','rejected','interview'))",
        (user_id,)
    ).fetchone()[0]

    avg_score_row = db.execute(
        "SELECT AVG(match_score) FROM candidates WHERE user_id=?", (user_id,)
    ).fetchone()[0]
    avg_score = round(avg_score_row or 0, 1)

    # Recent uploads (last 5)
    recent = db.execute(
        """SELECT c.*, c.match_score as overall_score
           FROM candidates c
           WHERE c.user_id=?
           ORDER BY c.created_at DESC LIMIT 5""",
        (user_id,)
    ).fetchall()

    return {
        'total_candidates': total_candidates,
        'total_jds':        total_jds,
        'shortlisted':      shortlisted,
        'rejected':         rejected,
        'pending':          pending,
        'avg_score':        avg_score,
        'recent_uploads':   _rows_to_list(recent),
    }
