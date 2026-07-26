"""
config.py — Application Configuration
ResumeMatch.ai

All app-wide settings live here. Changing a value here affects the whole app.
"""

import os
import secrets

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load .env / .env.local if present locally
for env_name in ['.env', '.env.local']:
    env_path = os.path.join(BASE_DIR, env_name)
    if os.path.exists(env_path):
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"\''))
        except Exception:
            pass


class Config:
    # ─── Security ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # ─── Database ────────────────────────────────────────────────────────────
    DATABASE_URL = os.environ.get('DATABASE_URL')

    # ─── Paths ───────────────────────────────────────────────────────────────
    BASE_DIR  = BASE_DIR
    IS_VERCEL = bool(os.environ.get('VERCEL'))

    if IS_VERCEL:
        DATABASE_PATH  = os.path.join('/tmp', 'resumematch.db')
        UPLOAD_FOLDER  = os.path.join('/tmp', 'uploads')
        REPORTS_FOLDER = os.path.join('/tmp', 'reports')
    else:
        DATABASE_PATH  = os.path.join(BASE_DIR, 'database', 'resumematch.db')
        UPLOAD_FOLDER  = os.path.join(BASE_DIR, 'uploads')
        REPORTS_FOLDER = os.path.join(BASE_DIR, 'reports')

    # ─── Upload Settings ─────────────────────────────────────────────────────
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024          # 16 MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}

    # ─── App Settings ────────────────────────────────────────────────────────
    DEBUG = True
    TESTING = False

    # ─── ATS Score Weights (must sum to 1.0) ─────────────────────────────────
    SCORE_WEIGHTS = {
        'skills':     0.40,   # Skills match (40%)
        'keywords':   0.30,   # Keyword presence (30%)
        'experience': 0.20,   # Years of experience (20%)
        'education':  0.10,   # Education level (10%)
    }

    # ─── Candidate Status Options ─────────────────────────────────────────────
    CANDIDATE_STATUSES = ['pending', 'shortlisted', 'rejected', 'interview']

    # ─── ATS Threshold ────────────────────────────────────────────────────────
    SHORTLIST_THRESHOLD = 70   # Auto-shortlist above this score
    REJECT_THRESHOLD    = 30   # Auto-reject below this score
