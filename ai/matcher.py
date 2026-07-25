"""
ai/matcher.py — ATS Matching Engine
ResumeMatch.ai

Calculates how well a resume matches a Job Description.

SCORING BREAKDOWN:
  - Skill Match   (40%) — skills in resume vs skills in JD
  - Keyword Match (30%) — JD keywords found in resume text
  - Experience    (20%) — years required vs years candidate has
  - Education     (10%) — degree level match

SEMANTIC SIMILARITY:
  We try to use Sentence Transformers (cosine similarity of embeddings).
  If not installed, we fall back to TF-IDF cosine similarity.

HOW IT WORKS:
  1. Extract skills from both resume and JD
  2. Compare lists to get matched / missing / extra skills
  3. Check JD keywords in resume text
  4. Compare years of experience
  5. Compare education level
  6. Weighted average → overall ATS score

INTERVIEW TIP:
"Traditional ATS tools use pure keyword matching. We add semantic
similarity — understanding that 'built APIs' and 'REST development'
mean the same thing — making our scores more meaningful."
"""

import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ai.extractor import ALL_SKILLS, DEGREE_KEYWORDS, extractor as _extractor

# ─── Sentence Transformers disabled for lightweight TF-IDF fallback ────────
_model = None
SEMANTIC_AVAILABLE = False

# Education level map (higher = better)
EDUCATION_LEVELS = {
    'phd': 6, 'doctorate': 6,
    'master': 5, 'm.tech': 5, 'm.e': 5, 'mba': 5, 'm.sc': 5, 'mca': 5,
    'bachelor': 4, 'b.tech': 4, 'b.e': 4, 'b.sc': 4, 'bca': 4, 'bba': 4,
    'diploma': 3, '12th': 2, 'hsc': 2, '10th': 1, 'ssc': 1, 'matric': 1
}


class ATSMatcher:
    """Calculates ATS compatibility score between a resume and a job description."""

    def find_best_jd_match(self, resume_text, resume_parsed, jds, config_weights=None):
        """
        Screen resume against ALL available Job Descriptions and return the highest-scoring match.
        """
        if not jds:
            return self.match(resume_text, resume_parsed, None, config_weights)

        best_result = None
        best_score = -1.0

        for jd in jds:
            jd_txt = (jd.get('raw_text') or jd.get('requirements') or jd.get('title')) if isinstance(jd, dict) else (getattr(jd, 'raw_text', '') or getattr(jd, 'title', ''))
            res = self.match(resume_text, resume_parsed, jd_txt, config_weights)
            res_score = res.get('overall_score', 0.0)

            jd_id = jd.get('id') if isinstance(jd, dict) else getattr(jd, 'id', None)
            jd_title = jd.get('title') if isinstance(jd, dict) else getattr(jd, 'title', 'General')
            res['jd_id'] = jd_id
            res['jd_title'] = jd_title

            if res_score > best_score:
                best_score = res_score
                best_result = res

        return best_result or self.match(resume_text, resume_parsed, None, config_weights)

    def match(self, resume_text, resume_parsed, jd_text=None, config_weights=None):
        """
        Main matching function.
        Handles both JD-based matching and fallback job-title self-relevance matching.
        """
        try:
            # Weights according to ATS Scoring Formula:
            # Skills (40%), Keywords (30%), Experience (20%), Education (10%)
            weights = config_weights or {
                'skills': 0.40,
                'keywords': 0.30,
                'experience': 0.20,
                'education': 0.10
            }

            resume_skills = set(s.lower() for s in (resume_parsed.get('skills') or []))
            resume_years  = resume_parsed.get('years_exp') or 0
            resume_edu    = self._get_education_level(resume_parsed.get('education') or [])
            job_title     = resume_parsed.get('job_title') or 'Software Developer'

            # ── Check if JD was provided ──────────────────────────────────────
            has_jd = bool(jd_text and jd_text.strip())

            if has_jd:
                # ── Scoring against provided JD ───────────────────────────────
                jd_skills   = self._extract_skills_from_text(jd_text.lower())
                jd_keywords = self._extract_keywords(jd_text)
                jd_years    = self._extract_required_experience(jd_text)
                jd_edu_lvl  = self._extract_required_education(jd_text)

                jd_skills_set  = set(jd_skills)
                matched_skills = sorted(list(resume_skills & jd_skills_set))
                missing_skills = sorted(list(jd_skills_set - resume_skills))
                extra_skills   = sorted(list(resume_skills - jd_skills_set))

                skill_score = (len(matched_skills) / len(jd_skills_set) * 100) if jd_skills_set else 60.0
                keyword_score = self._calc_keyword_score(resume_text.lower(), jd_keywords)
                semantic = self._semantic_similarity(resume_text, jd_text)
                keyword_score = keyword_score * 0.70 + semantic * 100 * 0.30

                experience_score = self._calc_experience_score(resume_years, jd_years)
                education_score  = self._calc_education_score(resume_edu, jd_edu_lvl)

            else:
                # ── Fallback: Score against Resume's Stated Job Title ─────────
                role_skills = self._get_role_expected_skills(job_title)
                role_skills_set = set(role_skills)
                matched_skills  = sorted(list(resume_skills & role_skills_set))
                missing_skills  = sorted(list(role_skills_set - resume_skills))
                extra_skills    = sorted(list(resume_skills - role_skills_set))

                skill_score = (len(matched_skills) / len(role_skills_set) * 100) if role_skills_set else (70.0 if resume_skills else 40.0)
                keyword_score = min(len(resume_skills) * 10, 85.0)
                experience_score = min(resume_years * 20, 100.0) if resume_years > 0 else 60.0
                education_score  = 100.0 if resume_edu >= 4 else (75.0 if resume_edu > 0 else 50.0)
                jd_years = 2
                jd_edu_lvl = 4

            # ── Final Weighted Score Formula (40% skills, 30% keywords, 20% experience, 10% education) ──
            overall = (
                skill_score      * weights.get('skills', 0.40) +
                keyword_score    * weights.get('keywords', 0.30) +
                experience_score * weights.get('experience', 0.20) +
                education_score  * weights.get('education', 0.10)
            )
            overall = round(min(max(overall, 0), 100), 1)

            # FEATURE 2: Candidate status is ALWAYS manual. Defaults to 'pending'.
            status = 'pending'

            # Matched & missing keywords
            matched_keywords = matched_skills[:10]
            missing_keywords = missing_skills[:10]

            # Summary
            summary = self._generate_summary(
                resume_parsed.get('name', 'Candidate'),
                overall, matched_skills, missing_skills,
                resume_years, jd_years
            )
            suggestions = self._generate_suggestions(
                missing_skills, resume_years, jd_years,
                resume_edu, jd_edu_lvl, overall
            )

            return {
                'match_score':       overall,
                'overall_score':     overall,
                'skill_score':       round(skill_score, 1),
                'keyword_score':     round(keyword_score, 1),
                'experience_score':  round(experience_score, 1),
                'education_score':   round(education_score, 1),
                'matched_skills':    matched_skills,
                'missing_skills':    missing_skills,
                'matched_keywords':  matched_keywords,
                'missing_keywords':  missing_keywords,
                'extra_skills':      extra_skills[:15],
                'summary':           summary,
                'suggestions':       suggestions,
                'status':            status,
                'has_jd':            has_jd,
                'job_title':         job_title
            }

        except Exception as e:
            print(f"ATS Scoring error: {e}")
            return {
                'match_score':       0.0,
                'overall_score':     0.0,
                'skill_score':       0.0,
                'keyword_score':     0.0,
                'experience_score':  0.0,
                'education_score':   0.0,
                'matched_skills':    [],
                'missing_skills':    [],
                'matched_keywords':  [],
                'missing_keywords':  [],
                'extra_skills':      [],
                'summary':           f"Score Unavailable: {str(e)}",
                'suggestions':       ["Re-upload file or check text content."],
                'status':            'Score Unavailable',
                'has_jd':            bool(jd_text)
            }

    def _get_role_expected_skills(self, title):
        title_lower = (title or '').lower()
        if 'python' in title_lower or 'backend' in title_lower:
            return ['python', 'flask', 'django', 'sql', 'rest api', 'postgresql', 'docker', 'git']
        if 'frontend' in title_lower or 'web' in title_lower:
            return ['javascript', 'typescript', 'react', 'html', 'css', 'node.js', 'git']
        if 'data' in title_lower or 'machine learning' in title_lower:
            return ['python', 'sql', 'pandas', 'numpy', 'scikit-learn', 'machine learning', 'tableau']
        return ['python', 'java', 'sql', 'git', 'rest api', 'docker', 'linux']

    # ── Skill Extraction from JD ──────────────────────────────────────────

    def _extract_skills_from_text(self, text):
        """Find known skills inside any text."""
        found = set()
        for skill in ALL_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text):
                found.add(skill)
        return found

    # ── Keyword Extraction from JD ────────────────────────────────────────

    def _extract_keywords(self, jd_text):
        """
        Use TF-IDF to find the most important keywords in the JD.
        Returns top 30 keywords.
        """
        try:
            tfidf = TfidfVectorizer(
                stop_words='english',
                max_features=50,
                ngram_range=(1, 2)
            )
            tfidf.fit([jd_text])
            return list(tfidf.vocabulary_.keys())
        except Exception:
            # Fallback: split by words
            words = re.findall(r'\b[a-zA-Z]{4,}\b', jd_text.lower())
            return list(set(words))[:30]

    def _calc_keyword_score(self, resume_text, keywords):
        """Percentage of JD keywords found in resume."""
        if not keywords:
            return 50
        found = sum(1 for k in keywords if k in resume_text)
        return (found / len(keywords)) * 100

    # ── Semantic Similarity ───────────────────────────────────────────────

    def _semantic_similarity(self, text1, text2):
        """
        Cosine similarity between embeddings.
        Uses Sentence Transformers if available, else TF-IDF.
        """
        if SEMANTIC_AVAILABLE and _model:
            try:
                emb1 = _model.encode([text1[:512]])
                emb2 = _model.encode([text2[:512]])
                sim  = cosine_similarity(emb1, emb2)[0][0]
                return float(sim)
            except Exception:
                pass

        # Fallback: TF-IDF cosine similarity
        try:
            tfidf = TfidfVectorizer(stop_words='english')
            matrix = tfidf.fit_transform([text1, text2])
            sim = cosine_similarity(matrix[0:1], matrix[1:2])[0][0]
            return float(sim)
        except Exception:
            return 0.5

    # ── Experience Scoring ────────────────────────────────────────────────

    def _extract_required_experience(self, jd_text):
        """Extract required years of experience from JD."""
        pattern = r'(\d+)\+?\s*(?:to\s*\d+)?\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp)'
        match = re.search(pattern, jd_text, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0

    def _calc_experience_score(self, candidate_years, required_years):
        """Score based on experience gap."""
        if required_years == 0:
            return 75  # No requirement → good default
        if candidate_years >= required_years:
            return 100
        if candidate_years == 0:
            return 20
        ratio = candidate_years / required_years
        return min(ratio * 100, 100)

    # ── Education Scoring ─────────────────────────────────────────────────

    def _extract_required_education(self, jd_text):
        """Find highest education level required in JD."""
        jd_lower = jd_text.lower()
        highest = 0
        for deg, lvl in EDUCATION_LEVELS.items():
            if deg in jd_lower and lvl > highest:
                highest = lvl
        return highest

    def _get_education_level(self, education_list):
        """Get highest education level from candidate's education list."""
        highest = 0
        combined = ' '.join(education_list).lower()
        for deg, lvl in EDUCATION_LEVELS.items():
            if deg in combined and lvl > highest:
                highest = lvl
        return highest

    def _calc_education_score(self, candidate_lvl, required_lvl):
        """Score based on education level."""
        if required_lvl == 0:
            return 75  # No requirement
        if candidate_lvl >= required_lvl:
            return 100
        if candidate_lvl == 0:
            return 30
        return (candidate_lvl / required_lvl) * 100

    # ── Suggestions ───────────────────────────────────────────────────────

    def _generate_suggestions(self, missing_skills, cand_years, req_years,
                               cand_edu, req_edu, score):
        suggestions = []

        if missing_skills:
            top_missing = missing_skills[:5]
            suggestions.append(
                f"Add these missing skills to your resume: "
                f"{', '.join(top_missing)}"
            )

        if req_years > 0 and cand_years < req_years:
            gap = req_years - cand_years
            suggestions.append(
                f"The role requires {req_years} years of experience. "
                f"You have {cand_years}. Highlight freelance, internship, "
                f"or project experience to bridge the {gap}-year gap."
            )

        if req_edu > 0 and cand_edu < req_edu:
            suggestions.append(
                "Consider adding or pursuing higher education qualifications "
                "as this role requires a higher degree level."
            )

        if score < 50:
            suggestions.append(
                "Tailor your resume specifically to this job description. "
                "Mirror the exact keywords and phrases used in the JD."
            )

        if score >= 70:
            suggestions.append(
                "Strong match! Consider reaching out directly to the recruiter "
                "with a personalized cover letter mentioning your top matched skills."
            )

        if not suggestions:
            suggestions.append(
                "Your resume is a decent match. Focus on quantifying "
                "your achievements (e.g. 'Improved performance by 30%')."
            )

        return suggestions

    # ── AI Summary ────────────────────────────────────────────────────────

    def _generate_summary(self, name, score, matched, missing, cand_yrs, req_yrs):
        grade = 'excellent' if score >= 80 else \
                'good' if score >= 60 else \
                'moderate' if score >= 40 else 'low'

        matched_str  = ', '.join(matched[:5]) if matched else 'none found'
        missing_str  = ', '.join(missing[:3]) if missing else 'none'
        exp_str      = f"{cand_yrs} years" if cand_yrs else "not specified"
        req_exp_str  = f"{req_yrs} years required" if req_yrs else "no specific requirement"

        return (
            f"{name} has an {grade} ATS compatibility score of {score}%. "
            f"Key matched skills include: {matched_str}. "
            f"Missing skills: {missing_str}. "
            f"Experience: {exp_str} ({req_exp_str})."
        )


# Module-level instance
matcher = ATSMatcher()
