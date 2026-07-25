"""
app.py — Flask Application Entry Point
ResumeMatch.ai

This file creates the Flask app, registers all blueprints (route modules),
and starts the development server.

HOW IT WORKS:
1. create_app() sets up Flask with our config
2. Registers each route blueprint (auth, dashboard, resume, etc.)
3. Ensures upload/report folders exist
4. if __main__ runs the dev server

INTERVIEW TIP:
"We use the Application Factory pattern — create_app() — so the app
can be tested in isolation and configured differently per environment."
"""

import os
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
from flask import Flask, render_template, session, redirect, url_for
from config import Config


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Ensure required folders exist ─────────────────────────────────────
    os.makedirs(app.config['UPLOAD_FOLDER'],  exist_ok=True)
    os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)

    # ── Initialize database (create tables if they don't exist) ───────────
    from services.db_service import init_db
    with app.app_context():
        init_db()

    # ── Register Blueprints (route modules) ───────────────────────────────
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.resume    import resume_bp
    from routes.jd        import jd_bp
    from routes.analysis  import analysis_bp
    from routes.reports   import reports_bp
    from routes.analytics import analytics_bp
    from routes.landing   import landing_bp

    app.register_blueprint(landing_bp)
    app.register_blueprint(auth_bp,      url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(resume_bp,    url_prefix='/resume')
    app.register_blueprint(jd_bp,        url_prefix='/jd')
    app.register_blueprint(analysis_bp,  url_prefix='/analysis')
    app.register_blueprint(reports_bp,   url_prefix='/reports')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    # ── Global 404 / 500 handlers ─────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # ── Context processor — inject user info into every template ──────────
    @app.context_processor
    def inject_user():
        from services.db_service import get_user_by_id, get_unread_count
        user = None
        unread = 0
        if 'user_id' in session:
            user = get_user_by_id(session['user_id'])
            try:
                unread = get_unread_count(session['user_id'])
            except Exception:
                unread = 0
        return dict(current_user=user, unread_count=unread)

    return app


# ── Run the app ────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    print("\n[OK] ResumeMatch.ai is running at http://127.0.0.1:5000\n")
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)
