"""
utils/helpers.py — Shared Helper Functions
ResumeMatch.ai

Small utility functions used across the whole app.
"""

import os
import hashlib
from datetime import datetime


def allowed_file(filename, allowed_extensions):
    """Check if the uploaded file has an allowed extension."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions


def secure_unique_filename(filename):
    """
    Generate a unique filename to avoid collisions.
    e.g.  john_resume.pdf  →  1a2b3c4d_john_resume.pdf
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base, ext = os.path.splitext(filename)
    # Remove spaces and special chars from the base name
    safe_base = "".join(c if c.isalnum() or c in '-_' else '_' for c in base)
    return f"{timestamp}_{safe_base}{ext}"


def compute_file_hash(filepath):
    """Compute MD5 hash of a file (used for duplicate detection)."""
    h = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def format_score_color(score):
    """Return a CSS color class based on ATS score."""
    if score >= 75:
        return 'success'
    elif score >= 50:
        return 'warning'
    elif score >= 30:
        return 'orange'
    else:
        return 'danger'


def score_to_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 90: return 'A+'
    if score >= 80: return 'A'
    if score >= 70: return 'B+'
    if score >= 60: return 'B'
    if score >= 50: return 'C'
    if score >= 40: return 'D'
    return 'F'


def time_ago(dt_string):
    """Convert a datetime string to a human-readable 'X ago' string."""
    try:
        dt  = datetime.fromisoformat(dt_string)
        now = datetime.now()
        diff = now - dt
        seconds = int(diff.total_seconds())

        if seconds < 60:
            return 'just now'
        elif seconds < 3600:
            mins = seconds // 60
            return f"{mins} minute{'s' if mins > 1 else ''} ago"
        elif seconds < 86400:
            hrs = seconds // 3600
            return f"{hrs} hour{'s' if hrs > 1 else ''} ago"
        elif seconds < 604800:
            days = seconds // 86400
            return f"{days} day{'s' if days > 1 else ''} ago"
        else:
            return dt.strftime('%b %d, %Y')
    except Exception:
        return dt_string or 'Unknown'


def truncate(text, length=100):
    """Truncate text to a max length with ellipsis."""
    if not text:
        return ''
    return text[:length] + '...' if len(text) > length else text


def clean_text(text):
    """Remove extra whitespace and newlines from extracted text."""
    if not text:
        return ''
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return ' '.join(lines)


def get_file_size_str(filepath):
    """Return human-readable file size."""
    try:
        size = os.path.getsize(filepath)
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        else:
            return f"{size / (1024*1024):.1f} MB"
    except Exception:
        return 'Unknown'


def calculate_quality_score(parsed_data, raw_text):
    """
    Calculate a resume quality score based on completeness.
    Checks: contact info, education, experience, skills, length.
    Returns a score 0-100.
    """
    score = 0

    # Contact info (20 pts)
    if parsed_data.get('email'):   score += 7
    if parsed_data.get('phone'):   score += 7
    if parsed_data.get('name'):    score += 6

    # Sections present (40 pts)
    if parsed_data.get('skills'):      score += 15
    if parsed_data.get('education'):   score += 10
    if parsed_data.get('experience'):  score += 15

    # Length (20 pts — longer = more content)
    word_count = len((raw_text or '').split())
    if word_count > 500:  score += 20
    elif word_count > 300: score += 15
    elif word_count > 100: score += 10
    else:                  score += 5

    # Projects / Certifications (20 pts)
    if parsed_data.get('projects'):       score += 10
    if parsed_data.get('certifications'): score += 10

    return min(score, 100)
