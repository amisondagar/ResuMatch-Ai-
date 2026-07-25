"""
routes/dashboard.py — Dashboard Routes
ResumeMatch.ai

Shows summary statistics, recent uploads, charts, and notifications.
"""

from flask import Blueprint, render_template, session, jsonify, request
from routes.auth import login_required
from services.db_service import (get_dashboard_stats, get_notifications,
                                 mark_notifications_read, get_unread_count,
                                 get_bookmarks)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    user_id = session['user_id']
    stats   = get_dashboard_stats(user_id)
    notifs  = get_notifications(user_id, limit=5)
    unread  = get_unread_count(user_id)
    return render_template('dashboard/index.html',
                           stats=stats, notifications=notifs, unread=unread)


@dashboard_bp.route('/notifications')
@login_required
def notifications():
    user_id = session['user_id']
    notifs  = get_notifications(user_id, limit=50)
    mark_notifications_read(user_id)
    return render_template('dashboard/notifications.html', notifications=notifs)


@dashboard_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_read():
    mark_notifications_read(session['user_id'])
    return jsonify({'ok': True})


@dashboard_bp.route('/bookmarks')
@login_required
def bookmarks():
    user_id   = session['user_id']
    bookmarks = get_bookmarks(user_id)
    return render_template('dashboard/bookmarks.html', bookmarks=bookmarks)


@dashboard_bp.route('/profile')
@login_required
def profile():
    from services.db_service import get_user_by_id
    user = get_user_by_id(session['user_id'])
    return render_template('dashboard/profile.html', user=user)
