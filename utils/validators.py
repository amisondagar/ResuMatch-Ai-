"""utils/validators.py — Input Validation Helpers"""
import re

def validate_email(email):
    pattern = r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password):
    """At least 8 chars, with at least one letter and one number."""
    if len(password) < 8:
        return False
    has_letter = any(c.isalpha() for c in password)
    has_digit  = any(c.isdigit() for c in password)
    return has_letter and has_digit

def validate_username(username):
    """3-30 chars, alphanumeric + underscores only."""
    pattern = r'^[A-Za-z0-9_]{3,30}$'
    return bool(re.match(pattern, username))
