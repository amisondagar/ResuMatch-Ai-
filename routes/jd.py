"""
routes/jd.py — Job Description Routes
ResumeMatch.ai

Handles: Create JD, List JDs, Edit JD, Delete JD, Upload JD file
"""

import os
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, current_app, jsonify)
from routes.auth import login_required
from services.db_service import (create_jd, get_all_jds, get_jd,
                                 update_jd, delete_jd, add_notification)

jd_bp = Blueprint('jd', __name__)


# ── Create / Paste JD ───────────────────────────────────────────────────────

@jd_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        user_id = session['user_id']

        if request.is_json:
            data = request.get_json() or {}
            raw_text = (data.get('description') or data.get('raw_jd_text') or '').strip()
            user_title = (data.get('title') or '').strip()
            company = (data.get('company') or 'Acme Corp').strip()
        else:
            raw_text = (request.form.get('description') or request.form.get('raw_jd_text') or '').strip()
            user_title = (request.form.get('title') or '').strip()
            company = (request.form.get('company') or 'Acme Corp').strip()

        # Also handle JD file upload if attached
        if 'jd_file' in request.files:
            jd_file = request.files['jd_file']
            if jd_file and jd_file.filename:
                from services.resume_parser import (extract_text_from_pdf,
                                                    extract_text_from_docx)
                ext = jd_file.filename.rsplit('.', 1)[-1].lower()
                tmp_path = os.path.join(
                    current_app.config['UPLOAD_FOLDER'],
                    f"jd_tmp_{user_id}.{ext}"
                )
                jd_file.save(tmp_path)
                if ext == 'pdf':
                    raw_text = extract_text_from_pdf(tmp_path)
                elif ext in ('docx', 'doc'):
                    raw_text = extract_text_from_docx(tmp_path)
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        if not raw_text:
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': False, 'error': 'Please provide a job description.'}), 400
            flash('Please paste or upload a Job Description.', 'danger')
            return render_template('jd/create.html')

        try:
            from ai.matcher import matcher
            from ai.extractor import extractor

            extracted_skills = matcher._extract_skills_from_text(raw_text.lower())
            skills_str = ", ".join(sorted(list(extracted_skills)))

            title = user_title
            if not title:
                extracted_title = extractor._extract_job_title(raw_text)
                title = extracted_title if extracted_title != 'Software Professional' else raw_text.split('\n')[0][:40]

            requirements = f"Key Skills Required: {skills_str if skills_str else 'General Technical Skills'}"

            jd_id = create_jd(user_id, title, company, raw_text, requirements)
            session['active_jd_id'] = jd_id

            # Auto-screen existing candidates against newly added JD and update best-fit JD if new score is higher
            from services.db_service import get_all_candidates, update_candidate_jd, create_score
            from config import Config

            try:
                candidates = get_all_candidates(user_id)
                for c in candidates:
                    p_data = c.get('parsed_data') or {}
                    raw_txt = c.get('raw_text') or ''
                    res = matcher.match(
                        resume_text=raw_txt,
                        resume_parsed=p_data,
                        jd_text=raw_text + ' ' + requirements,
                        config_weights=Config.SCORE_WEIGHTS
                    )
                    new_score = res.get('overall_score', 0)
                    old_score = c.get('match_score') or 0

                    if new_score > old_score or not c.get('jd_id'):
                        current_status = c.get('status') or 'Pending'
                        create_score(
                            candidate_id=c['id'], jd_id=jd_id, user_id=user_id,
                            overall_score=new_score, skill_score=res.get('skill_score', 0),
                            experience_score=res.get('experience_score', 0), education_score=res.get('education_score', 0),
                            keyword_score=res.get('keyword_score', 0), matched_skills=res.get('matched_skills', []),
                            missing_skills=res.get('missing_skills', []), extra_skills=[],
                            summary=p_data.get('summary', ''), suggestions=res.get('suggestions', []),
                            interview_questions=[], status=current_status.lower()
                        )
                        update_candidate_jd(c['id'], jd_id, new_score)
            except Exception as rescreen_err:
                print(f"Candidate rescreening note: {rescreen_err}")

            add_notification(user_id, f'Job description "{title}" captured successfully.', 'success')

            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': True, 'jd_id': jd_id, 'title': title, 'company': company, 'message': f'Job description "{title}" created successfully!'})

            flash(f'Job description "{title}" submitted successfully!', 'success')
            return redirect(url_for('jd.view', jd_id=jd_id))
        except Exception as e:
            print(f"Error creating JD: {e}")
            err_msg = f"Failed to create job description: {str(e)}"
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'ok': False, 'error': err_msg}), 400
            flash(err_msg, 'danger')
            return render_template('jd/create.html')

    return render_template('jd/create.html')


# ── List JDs ───────────────────────────────────────────────────────────────

@jd_bp.route('/list')
@login_required
def list_jds():
    user_id = session['user_id']
    jds = get_all_jds(user_id)
    return render_template('jd/list.html', jds=jds)


# ── Edit JD ────────────────────────────────────────────────────────────────

@jd_bp.route('/<int:jd_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(jd_id):
    user_id = session['user_id']
    jd = get_jd(jd_id)

    if not jd or jd['user_id'] != user_id:
        flash('Job description not found.', 'danger')
        return redirect(url_for('jd.list_jds'))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        company = request.form.get('company', '').strip()
        description = request.form.get('description', '').strip()
        requirements = request.form.get('requirements', '').strip()

        if not title or not description:
            flash('Title and description are required.', 'danger')
            return render_template('jd/edit.html', jd=jd)

        update_jd(jd_id, title, company, description, requirements)
        flash('Job description updated!', 'success')
        return redirect(url_for('jd.list_jds'))

    return render_template('jd/edit.html', jd=jd)


# ── Delete JD ──────────────────────────────────────────────────────────────

@jd_bp.route('/<int:jd_id>/delete', methods=['POST'])
@login_required
def delete(jd_id):
    user_id = session['user_id']
    jd = get_jd(jd_id)

    if jd and jd['user_id'] == user_id:
        delete_jd(jd_id, user_id)
        flash('Job description deleted.', 'success')
    else:
        flash('Job description not found.', 'danger')

    return redirect(url_for('jd.list_jds'))


# ── View JD ────────────────────────────────────────────────────────────────

@jd_bp.route('/<int:jd_id>')
@login_required
def view(jd_id):
    user_id = session['user_id']
    jd = get_jd(jd_id)

    if not jd or jd['user_id'] != user_id:
        flash('Job description not found.', 'danger')
        return redirect(url_for('jd.list_jds'))

    from services.db_service import get_scores_for_jd, get_all_candidates
    scores = get_scores_for_jd(jd_id, user_id)
    candidates = get_all_candidates(user_id)

    return render_template('jd/view.html',
                           jd=jd, scores=scores, candidates=candidates)