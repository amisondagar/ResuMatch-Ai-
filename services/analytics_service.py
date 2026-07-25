"""
services/analytics_service.py — Analytics Data Service
ResumeMatch.ai

Prepares live data directly from SQLite for the single unified Analytics dashboard.
All data is returned as JSON-serialisable dicts/lists for Plotly.js rendering.
"""

import json
from collections import Counter
from services.db_service import get_db


def get_analytics_data(user_id):
    """
    Fetch and compute all analytics data for a user directly from SQLite.
    """
    db = get_db()

    # ── All candidates ────────────────────────────────────────────────────
    candidates_rows = db.execute(
        "SELECT * FROM candidates WHERE user_id=? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    candidates = [dict(r) for r in candidates_rows]

    # ── All scores ────────────────────────────────────────────────────────
    scores_rows = db.execute(
        """SELECT s.candidate_id, s.overall_score, s.skill_score, s.experience_score,
                  s.education_score, s.keyword_score, s.status, s.matched_skills,
                  c.name, c.parsed_data
           FROM candidates c
           LEFT JOIN scores s ON c.id = s.candidate_id AND s.user_id = c.user_id
           WHERE c.user_id=?""",
        (user_id,)
    ).fetchall()
    scores_list = [dict(r) for r in scores_rows]

    if not candidates:
        return _empty_analytics()

    # ── 1. Top Stat Cards (Computed live from SQLite) ─────────────────────
    total_candidates = len(candidates)
    
    shortlisted_cnt = sum(1 for c in candidates if (c.get('status') or '').lower() == 'shortlisted')
    rejected_cnt    = sum(1 for c in candidates if (c.get('status') or '').lower() == 'rejected')
    pending_cnt     = total_candidates - (shortlisted_cnt + rejected_cnt)

    # Compute average ATS score across candidates
    all_ats_scores = [
        c.get('match_score') or c.get('quality_score') or 0.0
        for c in candidates
    ]
    avg_score = round(sum(all_ats_scores) / len(all_ats_scores), 1) if all_ats_scores else 0.0

    # ── 2. Candidate ATS Score Bar Chart (Sorted Highest to Lowest) ──────
    sorted_candidates = sorted(
        candidates,
        key=lambda x: (x.get('match_score') or x.get('quality_score') or 0.0),
        reverse=True
    )
    
    cand_names = [(c.get('name') or f"Candidate #{c['id']}") for c in sorted_candidates]
    cand_scores = [round(c.get('match_score') or c.get('quality_score') or 0.0, 1) for c in sorted_candidates]
    cand_ids = [c['id'] for c in sorted_candidates]
    cand_statuses = [(c.get('status') or 'Pending').capitalize() for c in sorted_candidates]

    # ── 3. Skills Breakdown Chart per Candidate ───────────────────────────
    cand_skill_scores = []
    for c in sorted_candidates:
        pd = c.get('parsed_data') or {}
        if isinstance(pd, str):
            try: pd = json.loads(pd)
            except Exception: pd = {}
        skill_cnt = len(pd.get('skills') or [])
        # Normalised skill match score (cap at 100%)
        cand_skill_scores.append(min(skill_cnt * 12.5, 100.0))

    # ── 4. Certifications & Top Skills Talent Pool Overview ───────────────
    pool_counter = Counter()
    for c in candidates:
        pd = c.get('parsed_data') or {}
        if isinstance(pd, str):
            try: pd = json.loads(pd)
            except Exception: pd = {}
        for s in (pd.get('skills') or []):
            pool_counter[s] += 1
        for cert in (pd.get('certifications') or []):
            pool_counter[f"Cert: {cert}"] += 1

    top_talent_items = pool_counter.most_common(10)

    # ── 5. Status Donut Data ──────────────────────────────────────────────
    status_labels = ['Shortlisted', 'Rejected', 'Pending']
    status_values = [shortlisted_cnt, rejected_cnt, pending_cnt]

    return {
        'total_candidates': total_candidates,
        'shortlisted':      shortlisted_cnt,
        'rejected':         rejected_cnt,
        'pending':          pending_cnt,
        'avg_score':        avg_score,

        # JSON payloads for Plotly.js charts
        'candidate_scores_json': json.dumps({
            'names':  cand_names,
            'scores': cand_scores,
            'ids':    cand_ids,
            'statuses': cand_statuses
        }),

        'skills_breakdown_json': json.dumps({
            'names':  cand_names,
            'skill_scores': cand_skill_scores,
            'ids':    cand_ids
        }),

        'talent_pool_json': json.dumps({
            'items':  [item[0] for item in top_talent_items],
            'counts': [item[1] for item in top_talent_items]
        }),

        'status_donut_json': json.dumps({
            'labels': status_labels,
            'values': status_values
        })
    }


def _empty_analytics():
    empty_json = json.dumps({'names': [], 'scores': [], 'ids': []})
    return {
        'total_candidates': 0, 'shortlisted': 0, 'rejected': 0, 'pending': 0, 'avg_score': 0.0,
        'candidate_scores_json': empty_json,
        'skills_breakdown_json': json.dumps({'names': [], 'skill_scores': [], 'ids': []}),
        'talent_pool_json': json.dumps({'items': [], 'counts': []}),
        'status_donut_json': json.dumps({'labels': ['Shortlisted', 'Rejected', 'Pending'], 'values': [0, 0, 0]})
    }
