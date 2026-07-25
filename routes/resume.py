"""
routes/resume.py — Resume Upload & Management Routes
ResumeMatch.ai

Handles: Upload (single/multi), List, Detail, Delete, Download,
         Bookmark, Notes, Tags
"""

import os
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, session, send_from_directory,
                   jsonify, current_app)
from routes.auth import login_required
from services.db_service import (create_candidate, get_all_candidates,
                                 get_candidate, delete_candidate,
                                 toggle_bookmark, is_bookmarked,
                                 add_note, get_notes, delete_note,
                                 add_tag, get_tags, delete_tag,
                                 add_notification, search_candidates)
from services.resume_parser import parse_resume
from utils.helpers import (allowed_file, secure_unique_filename,
                           compute_file_hash, calculate_quality_score,
                           get_file_size_str)

resume_bp = Blueprint('resume', __name__)


# ── Upload ─────────────────────────────────────────────────────────────────

@resume_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    user_id = session['user_id']

    if request.method == 'POST':
        files = request.files.getlist('resumes')

        if not files or all(f.filename == '' for f in files):
            flash('No files selected. Please choose at least one resume.', 'warning')
            return redirect(url_for('resume.upload'))

        allowed = current_app.config['ALLOWED_EXTENSIONS']
        upload_dir = current_app.config['UPLOAD_FOLDER']
        success_count = 0
        error_count = 0

        # Check for active JD
        from services.db_service import get_jd, get_all_jds, create_score
        from ai.matcher import matcher
        from config import Config

        active_jd_id = session.get('active_jd_id')
        selected_jd_id = active_jd_id
        active_jd = get_jd(active_jd_id) if active_jd_id else None
        if not active_jd:
            all_jds = get_all_jds(user_id)
            active_jd = all_jds[0] if all_jds else None

        jd_text = (active_jd['description'] + ' ' + (active_jd.get('requirements') or '')) if active_jd else None
        jd_id_val = active_jd['id'] if active_jd else None

        existing = get_all_candidates(user_id)
        existing_hashes = set()
        for c in existing:
            h = compute_file_hash(c.get('resume_path', ''))
            if h:
                existing_hashes.add(h)

        for f in files:
            if f.filename == '':
                continue

            if not allowed_file(f.filename, allowed):
                flash(f"'{f.filename}' is not a supported format (PDF/DOCX only).", 'warning')
                error_count += 1
                continue

            safe_name = secure_unique_filename(f.filename)
            filepath = os.path.join(upload_dir, safe_name)
            f.save(filepath)

            file_hash = compute_file_hash(filepath)
            is_dup = 1 if file_hash in existing_hashes else 0
            if file_hash:
                existing_hashes.add(file_hash)

            file_ext = f.filename.rsplit('.', 1)[1].lower()

            try:
                raw_text, parsed_data = parse_resume(filepath, file_ext, f.filename)

                if not raw_text or not raw_text.strip():
                    create_candidate(
                        user_id=user_id,
                        name=f.filename,
                        email='',
                        phone='',
                        filename=safe_name,
                        filepath=filepath,
                        file_type=file_ext,
                        raw_text='',
                        parsed_data={},
                        quality_score=0,
                        is_duplicate=is_dup,
                        status='Failed to Parse',
                        job_title='Unknown',
                        github='',
                        linkedin='',
                        match_score=0,
                        jd_id=None
                    )
                    error_count += 1
                    continue

                quality = calculate_quality_score(parsed_data, raw_text)

                # ── Run ATS Scoring against ALL JDs to find the best match ──
                all_jds = get_all_jds(user_id)
                match_result = matcher.find_best_jd_match(raw_text, parsed_data, all_jds, Config.SCORE_WEIGHTS)
                target_jd_id = match_result.get('jd_id')

                score_val = match_result.get('match_score', 0)
                # FEATURE 2: Candidate status is ALWAYS manual. Defaults strictly to 'Pending'.
                status_val = 'Pending'

                cand_id = create_candidate(
                    user_id=user_id,
                    name=parsed_data.get('name') or 'Candidate',
                    email=parsed_data.get('email') or '',
                    phone=parsed_data.get('phone') or '',
                    filename=safe_name,
                    filepath=filepath,
                    file_type=file_ext,
                    raw_text=raw_text,
                    parsed_data=parsed_data,
                    quality_score=quality,
                    is_duplicate=is_dup,
                    status=status_val,
                    job_title=parsed_data.get('job_title') or 'Software Developer',
                    github=parsed_data.get('github') or '',
                    linkedin=parsed_data.get('linkedin') or '',
                    match_score=score_val,
                    jd_id=target_jd_id
                )

                # Save the score details against target_jd_id
                from ai.question_gen import generate_questions
                matched_skills_list = match_result.get('matched_skills', [])
                missing_skills_list = match_result.get('missing_skills', [])

                target_jd = get_jd(target_jd_id) if target_jd_id else None
                jd_desc = (target_jd.get('description', '') + ' ' + (target_jd.get('requirements') or '')) if target_jd else ''
                questions = generate_questions(matched_skills_list, jd_desc)

                create_score(
                    candidate_id=cand_id,
                    jd_id=target_jd_id,
                    user_id=user_id,
                    overall_score=score_val,
                    skill_score=match_result.get('skill_score', 0),
                    experience_score=match_result.get('experience_score', 0),
                    education_score=match_result.get('education_score', 0),
                    keyword_score=match_result.get('keyword_score', 0),
                    matched_skills=matched_skills_list,
                    missing_skills=missing_skills_list,
                    extra_skills=match_result.get('extra_skills', []),
                    summary=match_result.get('summary', ''),
                    suggestions=match_result.get('suggestions', []),
                    interview_questions=questions,
                    status='pending'
                )

                success_count += 1

            except Exception as e:
                print(f"Error processing resume {f.filename}: {e}")
                create_candidate(
                    user_id=user_id,
                    name=f.filename,
                    email='',
                    phone='',
                    filename=safe_name,
                    filepath=filepath,
                    file_type=file_ext,
                    raw_text='',
                    parsed_data={},
                    quality_score=0,
                    is_duplicate=is_dup,
                    status='Failed to Parse',
                    job_title='Unknown',
                    github='',
                    linkedin='',
                    match_score=0,
                    jd_id=None
                )
                error_count += 1

        if success_count:
            add_notification(user_id, f"Successfully uploaded and screened {success_count} resume(s).", 'success')
            flash(f'Successfully uploaded and screened {success_count} resume(s)!', 'success')
        if error_count:
            flash(f'{error_count} file(s) failed or could not be parsed.', 'warning')

        return redirect(url_for('resume.list_resumes'))

    return render_template('resume/upload.html')


# ── List ───────────────────────────────────────────────────────────────────

@resume_bp.route('/list')
@login_required
def list_resumes():
    user_id = session['user_id']
    search_q = request.args.get('q', '').strip()
    sort_by = request.args.get('sort', 'newest')

    if search_q:
        candidates = search_candidates(user_id, search_q)
    else:
        candidates = get_all_candidates(user_id)

    # Sort
    if sort_by == 'name':
        candidates.sort(key=lambda c: (c.get('name') or '').strip().lower())
    elif sort_by in ('score', 'quality'):
        candidates.sort(key=lambda c: float(c.get('match_score') or c.get('quality_score') or 0), reverse=True)
    elif sort_by == 'status':
        status_order = {'shortlisted': 1, 'interview': 2, 'pending': 3, 'rejected': 4}
        candidates.sort(key=lambda c: status_order.get((c.get('status') or '').lower(), 5))
    else:
        candidates.sort(key=lambda c: c.get('id', 0), reverse=True)

    # Add bookmark info
    for c in candidates:
        c['is_bookmarked'] = is_bookmarked(user_id, c['id'])
        c['file_size'] = get_file_size_str(c.get('resume_path', ''))
        c['tags'] = get_tags(user_id, c['id'])

    return render_template('resume/list.html',
                           candidates=candidates, search_q=search_q, sort_by=sort_by)


# ── Detail ─────────────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>')
@login_required
def detail(candidate_id):
    user_id = session['user_id']
    candidate = get_candidate(candidate_id)

    if not candidate or candidate['user_id'] != user_id:
        flash('Candidate not found.', 'danger')
        return redirect(url_for('resume.list_resumes'))

    notes = get_notes(user_id, candidate_id)
    tags = get_tags(user_id, candidate_id)
    bookmarked = is_bookmarked(user_id, candidate_id)
    file_size = get_file_size_str(candidate.get('resume_path', ''))

    from services.db_service import get_all_jds, get_score, get_jd
    jds = get_all_jds(user_id)
    
    # Get best-fit score details for this candidate
    best_score = get_score(candidate_id, candidate.get('jd_id')) if candidate.get('jd_id') else None
    best_jd = get_jd(candidate.get('jd_id')) if candidate.get('jd_id') else None

    return render_template('resume/detail.html',
                           candidate=candidate, notes=notes, tags=tags,
                           bookmarked=bookmarked, file_size=file_size, jds=jds,
                           best_score=best_score, best_jd=best_jd)


# ── Delete ─────────────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/delete', methods=['POST'])
@login_required
def delete(candidate_id):
    user_id = session['user_id']
    candidate = get_candidate(candidate_id)

    if candidate and candidate['user_id'] == user_id:
        try:
            if os.path.exists(candidate['resume_path']):
                os.remove(candidate['resume_path'])
        except Exception:
            pass
        delete_candidate(candidate_id, user_id)
        flash('Resume deleted successfully.', 'success')
    else:
        flash('Resume not found.', 'danger')

    return redirect(url_for('resume.list_resumes'))


# ── Download ────────────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/download')
@login_required
def download(candidate_id):
    user_id = session['user_id']
    candidate = get_candidate(candidate_id)

    if not candidate or candidate['user_id'] != user_id:
        flash('File not found.', 'danger')
        return redirect(url_for('resume.list_resumes'))

    upload_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_dir,
                               candidate['resume_filename'],
                               as_attachment=True)


# ── Bookmark Toggle ────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/bookmark', methods=['POST'])
@login_required
def bookmark(candidate_id):
    user_id = session['user_id']
    is_bookmarked_now = toggle_bookmark(user_id, candidate_id)
    return jsonify({'bookmarked': is_bookmarked_now})


# ── Notes ──────────────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/notes', methods=['POST'])
@login_required
def add_note_route(candidate_id):
    user_id = session['user_id']
    note_text = request.form.get('note_text', '').strip()

    if note_text:
        add_note(user_id, candidate_id, note_text)
        flash('Note added successfully.', 'success')
    else:
        flash('Note cannot be empty.', 'warning')

    return redirect(url_for('resume.detail', candidate_id=candidate_id))


@resume_bp.route('/notes/<int:note_id>/delete', methods=['POST'])
@login_required
def delete_note_route(note_id):
    delete_note(note_id, session['user_id'])
    flash('Note deleted.', 'info')
    candidate_id = request.form.get('candidate_id')
    if candidate_id:
        return redirect(url_for('resume.detail', candidate_id=candidate_id))
    return redirect(url_for('resume.list_resumes'))


# ── Tags ───────────────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/tags', methods=['POST'])
@login_required
def add_tag_route(candidate_id):
    user_id = session['user_id']
    tag_name = request.form.get('tag_name', '').strip()

    if tag_name:
        add_tag(user_id, candidate_id, tag_name)
        flash(f'Tag "{tag_name}" added.', 'success')
    else:
        flash('Tag name cannot be empty.', 'warning')

    return redirect(url_for('resume.detail', candidate_id=candidate_id))


@resume_bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag_route(tag_id):
    delete_tag(tag_id, session['user_id'])
    candidate_id = request.form.get('candidate_id')
    if candidate_id:
        return redirect(url_for('resume.detail', candidate_id=candidate_id))
    return redirect(url_for('resume.list_resumes'))


# ── Status Update ──────────────────────────────────────────────────────────

@resume_bp.route('/<int:candidate_id>/status', methods=['POST', 'PATCH'])
@login_required
def update_status_route(candidate_id):
    user_id = session['user_id']
    new_status = request.form.get('status') or (request.json.get('status') if request.is_json else None)

    if new_status in ['pending', 'shortlisted', 'rejected', 'interview', 'Pending', 'Shortlisted', 'Rejected']:
        from services.db_service import update_candidate_status
        update_candidate_status(candidate_id, user_id, new_status.lower())
        return jsonify({'ok': True, 'candidate_id': candidate_id, 'status': new_status.lower()})

    return jsonify({'ok': False, 'error': 'Invalid status'}), 400