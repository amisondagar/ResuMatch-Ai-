"""
routes/analytics.py — Analytics Dashboard Route
ResumeMatch.ai
"""

from flask import Blueprint, render_template, session
from routes.auth import login_required
from services.analytics_service import get_analytics_data

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    data    = get_analytics_data(user_id)
    return render_template('analytics/index.html', data=data)
