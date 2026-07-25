"""
routes/analysis.py — AI Analysis Routes
ResumeMatch.ai

Handles:
  - Run ATS analysis (single candidate vs JD)
  - Bulk analysis (all candidates vs a JD)
  - View result
  - Candidate ranking
  - Side-by-side comparison
  - Update candidate status
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, jsonify)
from routes.auth import login_required
from services.db_service import (get_candidate, get_jd, get_all_candidates,
                                 get_all_jds, create_score, get_score,
                                 get_scores_for_jd, update_score_status,
                                 add_notification, get_all_scores)
from ai.matcher import matcher
from ai.question_gen import generate_questions
from config import Config

analysis_bp = Blueprint('analysis', __name__)


# ── Run Analysis: Single Candidate ─────────────────────────────────────────

@analysis_bp.route('/run', methods=['GET', 'POST'])
@login_required
def run():
    user_id = session['user_id']
    candidates = get_all_candidates(user_id)
    jds = get_all_jds(user_id)

    # Pre-select from query params (coming from resume detail page)
    selected_candidate_id = request.args.get('candidate_id', type=int)
    selected_jd_id = request.args.get('jd_id', type=int)

    if request.method == 'POST':
        candidate_id = request.form.get('candidate_id', type=int)
        jd_id = request.form.get('jd_id', type=int)

        if not candidate_id or not jd_id:
            flash('Please select both a candidate and a job description.', 'danger')
            return render_template('analysis/run.html',
                                   candidates=candidates, jds=jds)

        candidate = get_candidate(candidate_id)
        jd = get_jd(jd_id)

        if not candidate or candidate['user_id'] != user_id:
            flash('Candidate not found.', 'danger')
            return redirect(url_for('analysis.run'))
        if not jd or jd['user_id'] != user_id:
            flash('Job description not found.', 'danger')
            return redirect(url_for('analysis.run'))

        # ── Run the AI matching ───────────────────────────────────────────
        result = matcher.match(
            resume_text=candidate.get('raw_text', ''),
            resume_parsed=candidate.get('parsed_data', {}),
            jd_text=jd['description'] + ' ' + (jd.get('requirements') or ''),
            config_weights=Config.SCORE_WEIGHTS
        )

        # ── Generate interview questions ───────────────────────────────────
        questions = generate_questions(result['matched_skills'], jd['description'])

        # ── Save to DB ────────────────────────────────────────────────────
        current_status = candidate.get('status') or 'pending'
        score_id = create_score(
            candidate_id=candidate_id,
            jd_id=jd_id,
            user_id=user_id,
            overall_score=result['overall_score'],
            skill_score=result['skill_score'],
            experience_score=result['experience_score'],
            education_score=result['education_score'],
            keyword_score=result['keyword_score'],
            matched_skills=result['matched_skills'],
            missing_skills=result['missing_skills'],
            extra_skills=result['extra_skills'],
            summary=result['summary'],
            suggestions=result['suggestions'],
            interview_questions=questions,
            status=current_status.lower()
        )

        add_notification(
            user_id,
            f"ATS Analysis complete: {candidate.get('name', 'Candidate')} "
            f"scored {result['overall_score']}% for {jd['title']}.",
            'success' if result['overall_score'] >= 70 else 'info'
        )

        flash(f"Analysis complete! Score: {result['overall_score']}%", 'success')
        return redirect(url_for('analysis.result',
                                candidate_id=candidate_id, jd_id=jd_id))

    return render_template('analysis/run.html',
                           candidates=candidates, jds=jds,
                           selected_candidate_id=selected_candidate_id,
                           selected_jd_id=selected_jd_id)


# ── Bulk Analysis: All Candidates vs One JD ────────────────────────────────

@analysis_bp.route('/bulk', methods=['POST'])
@login_required
def bulk_analyze():
    user_id = session['user_id']
    jd_id = request.form.get('jd_id', type=int)

    if not jd_id:
        flash('Please select a job description.', 'danger')
        return redirect(url_for('analysis.ranking'))

    jd = get_jd(jd_id)
    candidates = get_all_candidates(user_id)

    if not jd or jd['user_id'] != user_id:
        flash('Job description not found.', 'danger')
        return redirect(url_for('analysis.ranking'))

    if not candidates:
        flash('No candidates found. Please upload resumes first.', 'warning')
        return redirect(url_for('resume.upload'))

    jd_text = jd['description'] + ' ' + (jd.get('requirements') or '')
    count = 0

    for candidate in candidates:
        result = matcher.match(
            resume_text=candidate.get('raw_text', ''),
            resume_parsed=candidate.get('parsed_data', {}),
            jd_text=jd_text,
            config_weights=Config.SCORE_WEIGHTS
        )
        questions = generate_questions(result['matched_skills'], jd['description'])

        current_status = candidate.get('status') or 'pending'
        create_score(
            candidate_id=candidate['id'],
            jd_id=jd_id,
            user_id=user_id,
            overall_score=result['overall_score'],
            skill_score=result['skill_score'],
            experience_score=result['experience_score'],
            education_score=result['education_score'],
            keyword_score=result['keyword_score'],
            matched_skills=result['matched_skills'],
            missing_skills=result['missing_skills'],
            extra_skills=result['extra_skills'],
            summary=result['summary'],
            suggestions=result['suggestions'],
            interview_questions=questions,
            status=current_status.lower()
        )
        count += 1

    add_notification(user_id,
                     f"Bulk analysis complete: {count} candidates analyzed for {jd['title']}.",
                     'success')
    flash(f'Bulk analysis complete! {count} candidates analyzed.', 'success')
    return redirect(url_for('analysis.ranking', jd_id=jd_id))


# ── View Result ────────────────────────────────────────────────────────────

@analysis_bp.route('/result')
@login_required
def result():
    user_id = session['user_id']
    candidate_id = request.args.get('candidate_id', type=int)
    jd_id = request.args.get('jd_id', type=int)

    if not candidate_id or not jd_id:
        flash('Invalid request.', 'danger')
        return redirect(url_for('analysis.ranking'))

    candidate = get_candidate(candidate_id)
    jd = get_jd(jd_id)
    score = get_score(candidate_id, jd_id)

    if not score:
        flash('No analysis found. Please run the analysis first.', 'warning')
        return redirect(url_for('analysis.run',
                                candidate_id=candidate_id, jd_id=jd_id))

    return render_template('analysis/result.html',
                           candidate=candidate, jd=jd, score=score)


# ── Ranking ────────────────────────────────────────────────────────────────

@analysis_bp.route('/ranking')
@login_required
def ranking():
    return redirect(url_for('reports.index', **request.args))


# ── Update Status ──────────────────────────────────────────────────────────

@analysis_bp.route('/status/<int:score_id>', methods=['POST'])
@login_required
def update_status(score_id):
    new_status = request.form.get('status', 'pending')
    valid = ['pending', 'shortlisted', 'rejected', 'interview']
    if new_status in valid:
        update_score_status(score_id, new_status)
        return jsonify({'ok': True, 'status': new_status})
    return jsonify({'ok': False}), 400


# ── Compare Candidates ─────────────────────────────────────────────────────

@analysis_bp.route('/compare')
@login_required
def compare():
    user_id = session['user_id']
    c1_id = request.args.get('c1', type=int)
    c2_id = request.args.get('c2', type=int)
    jd_id = request.args.get('jd_id', type=int)

    jds = get_all_jds(user_id)
    candidates = get_all_candidates(user_id)

    c1 = c2 = s1 = s2 = jd = None

    if c1_id and c2_id and jd_id:
        c1 = get_candidate(c1_id)
        c2 = get_candidate(c2_id)
        jd = get_jd(jd_id)
        if jd and jd['user_id'] == user_id:
            s1 = get_score(c1_id, jd_id)
            s2 = get_score(c2_id, jd_id)

    return render_template('analysis/compare.html',
                           jds=jds, candidates=candidates, jd=jd,
                           c1=c1, c2=c2, s1=s1, s2=s2,
                           c1_id=c1_id, c2_id=c2_id, jd_id=jd_id)