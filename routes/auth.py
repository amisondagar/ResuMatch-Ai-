"""
routes/auth.py — Authentication Routes
ResumeMatch.ai

Handles: Register, Login, Logout, Forgot Password, Change Password, Profile
"""

import bcrypt
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session)
from services.db_service import (create_user, get_user_by_email,
                                 get_user_by_username, get_user_by_id,
                                 update_user, update_password,
                                 update_last_login, add_notification)
from utils.validators import validate_email, validate_password

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator: redirect to login if not authenticated."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


# ── Register ───────────────────────────────────────────────────────────────

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username  = request.form.get('username', '').strip()
        email     = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        company   = request.form.get('company', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')

        # ── Validation ─────────────────────────────────────────────────────
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not validate_email(email):
            errors.append('Please enter a valid email address.')
        if not validate_password(password):
            errors.append('Password must be at least 8 characters with letters and numbers.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if get_user_by_email(email):
            errors.append('An account with this email already exists.')
        if get_user_by_username(username):
            errors.append('This username is already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('auth/register.html',
                                   username=username, email=email,
                                   full_name=full_name, company=company)

        # ── Create User ────────────────────────────────────────────────────
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        create_user(username, email, password_hash, full_name, company)

        user = get_user_by_email(email)
        session['user_id'] = user['id']
        update_last_login(user['id'])

        # Welcome notification
        add_notification(user['id'],
                         f"Welcome to ResumeMatch.ai, {full_name or username}! "
                         f"Start by uploading resumes and creating a job description.",
                         'success')

        flash(f'Welcome, {full_name or username}! Your account is ready.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html')


# ── Login ──────────────────────────────────────────────────────────────────

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = get_user_by_email(email)

        if user and bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            session['user_id'] = user['id']
            update_last_login(user['id'])
            flash(f'Welcome back, {user["full_name"] or user["username"]}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


# ── Logout ─────────────────────────────────────────────────────────────────

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('landing.index'))


# ── Forgot Password ────────────────────────────────────────────────────────

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = get_user_by_email(email)

        if user:
            # In a real app: send reset email with token
            # For demo: directly show reset page with user ID in session
            session['reset_user_id'] = user['id']
            flash('Identity verified! Please set your new password.', 'success')
            return redirect(url_for('auth.reset_password'))
        else:
            flash('No account found with that email address.', 'danger')

    return render_template('auth/forgot_password.html')


# ── Reset Password (demo flow — no email token) ────────────────────────────

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_user_id' not in session:
        flash('Please start the forgot password process.', 'warning')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password', '')
        confirm      = request.form.get('confirm_password', '')

        if not validate_password(new_password):
            flash('Password must be at least 8 characters with letters and numbers.', 'danger')
        elif new_password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            user_id      = session.pop('reset_user_id')
            new_hash     = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
            update_password(user_id, new_hash)
            flash('Password updated successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html')


# ── Change Password (logged in) ────────────────────────────────────────────

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        current  = request.form.get('current_password', '')
        new_pwd  = request.form.get('new_password', '')
        confirm  = request.form.get('confirm_password', '')

        if not bcrypt.checkpw(current.encode(), user['password_hash'].encode()):
            flash('Current password is incorrect.', 'danger')
        elif not validate_password(new_pwd):
            flash('New password must be at least 8 characters with letters and numbers.', 'danger')
        elif new_pwd != confirm:
            flash('New passwords do not match.', 'danger')
        else:
            new_hash = bcrypt.hashpw(new_pwd.encode(), bcrypt.gensalt()).decode()
            update_password(user['id'], new_hash)
            flash('Password changed successfully!', 'success')
            return redirect(url_for('dashboard.profile'))

    return render_template('auth/change_password.html', user=user)


# ── Profile ────────────────────────────────────────────────────────────────

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user = get_user_by_id(session['user_id'])

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        company   = request.form.get('company', '').strip()
        bio       = request.form.get('bio', '').strip()
        role      = request.form.get('role', 'recruiter')

        update_user(user['id'], full_name, company, bio, role)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('dashboard/profile.html', user=user)
