"""
routes/reports.py — Unified Candidate Reports & Export Service
ResumeMatch.ai
"""

import os
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, send_file, current_app)
from routes.auth import login_required
from services.db_service import (get_candidate, get_jd, get_score,
                                 get_scores_for_jd, get_all_jds,
                                 get_all_scores, get_all_candidates)
from services.report_service import (generate_candidate_pdf,
                                     generate_ranking_pdf, generate_csv)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/')
@login_required
def index():
    user_id   = session['user_id']
    jd_id     = request.args.get('jd_id', type=int)
    status_f  = request.args.get('status', '')
    min_score = request.args.get('min_score', 0, type=float)

    jds = get_all_jds(user_id)

    if jd_id:
        scores = get_scores_for_jd(jd_id, user_id)
    else:
        scores = get_all_scores(user_id)

    # Apply filters
    if status_f:
        scores = [s for s in scores if (s.get('status') or '').strip().lower() == status_f.strip().lower()]
    if min_score > 0:
        scores = [s for s in scores if float(s.get('overall_score') or 0) >= min_score]

    selected_jd = get_jd(jd_id) if jd_id else None

    return render_template('reports/index.html',
                           scores=scores, jds=jds, selected_jd=selected_jd,
                           selected_jd_id=jd_id, status_filter=status_f,
                           min_score=min_score)


# ── Candidate PDF Report ───────────────────────────────────────────────────

@reports_bp.route('/candidate/<int:candidate_id>/pdf')
@login_required
def candidate_pdf(candidate_id):
    user_id      = session['user_id']
    jd_id        = request.args.get('jd_id', type=int)
    candidate    = get_candidate(candidate_id)

    if not candidate or candidate['user_id'] != user_id:
        flash('Candidate not found.', 'danger')
        return redirect(url_for('reports.index'))

    jd = get_jd(jd_id) if jd_id else None
    score = get_score(candidate_id, jd_id) if jd_id else None

    if not score:
        scores = get_all_scores(user_id)
        cand_scores = [s for s in scores if s.get('candidate_id') == candidate_id]
        if cand_scores:
            score = cand_scores[0]
            if not jd and score.get('jd_id'):
                jd = get_jd(score['jd_id'])

    if not score:
        pd = candidate.get('parsed_data') or {}
        skills = pd.get('skills') or []
        overall = float(candidate.get('match_score') or candidate.get('quality_score') or 65.0)
        score = {
            'overall_score': overall,
            'skill_score': overall,
            'keyword_score': overall,
            'experience_score': overall,
            'education_score': overall,
            'status': candidate.get('status') or 'Pending',
            'matched_skills': skills,
            'missing_skills': [],
            'summary': pd.get('summary') or f"{candidate.get('name', 'Candidate')} candidate profile.",
            'suggestions': ['Continue building domain skills and project experience.']
        }

    if not jd:
        jd = {
            'title': candidate.get('job_title') or 'Software Engineer',
            'company': 'Acme Corp'
        }

    ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename    = f"report_{candidate.get('name','candidate')}_{ts}.pdf".replace(' ', '_')
    output_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)

    result = generate_candidate_pdf(candidate, score, jd, output_path)

    if result:
        return send_file(output_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    else:
        flash('Could not generate PDF. Please try again.', 'danger')
        return redirect(url_for('reports.index'))


# ── Full Ranking PDF Report ────────────────────────────────────────────────

@reports_bp.route('/ranking/pdf')
@login_required
def ranking_pdf():
    user_id = session['user_id']
    jd_id   = request.args.get('jd_id', type=int)

    if not jd_id:
        flash('Please select a job description to export ranking PDF.', 'warning')
        return redirect(url_for('reports.index'))

    jd     = get_jd(jd_id)
    scores = get_scores_for_jd(jd_id, user_id)

    if not jd or jd['user_id'] != user_id:
        flash('Job description not found.', 'danger')
        return redirect(url_for('reports.index'))

    if not scores:
        # Fallback to candidates assigned to this JD
        candidates = [c for c in get_all_candidates(user_id) if c.get('jd_id') == jd_id]
        if not candidates:
            candidates = get_all_candidates(user_id)
        scores = []
        for c in candidates:
            scores.append({
                'candidate_id': c['id'],
                'name': c.get('name', 'Candidate'),
                'overall_score': float(c.get('match_score') or c.get('quality_score') or 60.0),
                'skill_score': float(c.get('match_score') or c.get('quality_score') or 60.0),
                'status': c.get('status') or 'Pending'
            })

    if not scores:
        flash('No candidates found for this job report.', 'warning')
        return redirect(url_for('reports.index'))

    ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename    = f"rankings_{jd.get('title','job')}_{ts}.pdf".replace(' ', '_')
    output_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)

    result = generate_ranking_pdf(scores, jd, output_path)

    if result:
        return send_file(output_path, as_attachment=True, download_name=filename, mimetype='application/pdf')
    else:
        flash('Could not generate ranking PDF.', 'danger')
        return redirect(url_for('reports.index'))


# ── CSV Export ──────────────────────────────────────────────────────────────

@reports_bp.route('/export/csv')
@login_required
def export_csv():
    user_id = session['user_id']
    jd_id   = request.args.get('jd_id', type=int)

    if jd_id:
        scores = get_scores_for_jd(jd_id, user_id)
        jd     = get_jd(jd_id)
        tag    = jd.get('title', 'job').replace(' ', '_') if jd else 'export'
    else:
        scores = get_all_scores(user_id)
        tag    = 'all_candidates'

    # Fallback to all candidates list if no score records exist yet
    if not scores:
        candidates = get_all_candidates(user_id)
        if candidates:
            scores = []
            for c in candidates:
                pd = c.get('parsed_data') or {}
                scores.append({
                    'candidate_id': c['id'],
                    'name': c.get('name', 'Candidate'),
                    'email': c.get('email') or pd.get('email') or '',
                    'phone': c.get('phone') or pd.get('phone') or '',
                    'job_title': c.get('job_title') or pd.get('job_title') or 'Software Professional',
                    'status': c.get('status') or 'Pending',
                    'overall_score': float(c.get('match_score') or c.get('quality_score') or 0),
                    'skill_score': float(c.get('match_score') or c.get('quality_score') or 0),
                    'experience_score': float(c.get('match_score') or c.get('quality_score') or 0),
                    'education_score': float(c.get('match_score') or c.get('quality_score') or 0),
                    'keyword_score': float(c.get('match_score') or c.get('quality_score') or 0),
                    'matched_skills': pd.get('skills') or [],
                    'missing_skills': [],
                    'summary': pd.get('summary') or '',
                    'uploaded_at': c.get('created_at')
                })

    if not scores:
        flash('No candidates available to export.', 'warning')
        return redirect(url_for('reports.index'))

    ts          = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename    = f"resumematch_{tag}_{ts}.csv"
    output_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)

    result = generate_csv(scores, output_path)

    if result:
        return send_file(output_path, as_attachment=True, download_name=filename, mimetype='text/csv')
    else:
        flash('Could not generate CSV export.', 'danger')
        return redirect(url_for('reports.index'))

