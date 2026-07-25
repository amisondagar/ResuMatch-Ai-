"""
routes/landing.py — Landing / Home Page Route
ResumeMatch.ai
"""

from flask import Blueprint, render_template, session, redirect, url_for

landing_bp = Blueprint('landing', __name__)


@landing_bp.route('/')
def index():
    """Show landing page (or redirect logged-in users to dashboard)."""
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')


@landing_bp.route('/about')
def about():
    return render_template('landing.html')
