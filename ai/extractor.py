"""
ai/extractor.py — Resume Information Extractor
ResumeMatch.ai

This module uses NLP (spaCy) and regular expressions to extract
structured information from raw resume text.

EXTRACTED FIELDS:
  name, email, phone, skills, education, experience,
  projects, certifications, languages, achievements

HOW IT WORKS:
  1. Try spaCy NER for name detection
  2. Use regex for email, phone, dates
  3. Use a skills keyword database to find skills
  4. Find education keywords (degree names, universities)
  5. Estimate years of experience from date patterns

INTERVIEW TIP:
"We combine rule-based regex with ML-based NER (Named Entity Recognition)
for robust extraction. Regex handles structured data like emails; spaCy
handles unstructured text like names."
"""

import re
import json

# ─── Enable spaCy for ML Named Entity Recognition (NER) ────────────────────
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
    SPACY_AVAILABLE = True
except Exception:
    nlp = None
    SPACY_AVAILABLE = False


# ─── Master Skills Database ────────────────────────────────────────────────


SKILLS_DB = {
    'programming_languages': [
        'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#',
        'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala', 'r',
        'matlab', 'perl', 'bash', 'shell', 'powershell', 'lua', 'dart',
        'objective-c', 'groovy', 'haskell', 'elixir', 'clojure', 'f#',
        'cobol', 'fortran', 'assembly', 'vba', 'sql'
    ],
    'web_frameworks': [
        'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt.js',
        'flask', 'django', 'fastapi', 'express', 'spring', 'laravel',
        'rails', 'asp.net', '.net', 'node.js', 'nodejs', 'jquery',
        'bootstrap', 'tailwind', 'gatsby', 'remix', 'nestjs', 'hibernate',
        'j2ee', 'apis', 'rest api', 'microservices'
    ],
    'databases': [
        'mysql', 'postgresql', 'sqlite', 'mongodb', 'redis', 'cassandra',
        'oracle', 'sql server', 'dynamodb', 'firebase', 'elasticsearch',
        'neo4j', 'couchdb', 'mariadb', 'supabase', 'cockroachdb'
    ],
    'cloud_devops': [
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
        'jenkins', 'gitlab ci', 'github actions', 'terraform', 'ansible',
        'nginx', 'apache', 'linux', 'unix', 'ci/cd', 'devops',
        'heroku', 'vercel', 'cloudflare'
    ],
    'ai_ml': [
        'machine learning', 'deep learning', 'neural network', 'tensorflow',
        'pytorch', 'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv',
        'nlp', 'natural language processing', 'computer vision',
        'data science', 'data analysis', 'data mining', 'big data',
        'spark', 'hadoop', 'tableau', 'power bi', 'excel', 'matplotlib',
        'seaborn', 'plotly', 'transformers', 'hugging face', 'langchain',
        'llm', 'generative ai', 'rag', 'fine-tuning'
    ],
    'mobile': [
        'android', 'ios', 'react native', 'flutter', 'xamarin',
        'ionic', 'cordova', 'swift', 'kotlin', 'jetpack compose',
        'swiftui', 'objective-c', 'mobile development', 'pos'
    ],
    'tools': [
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence',
        'slack', 'figma', 'adobe xd', 'photoshop', 'illustrator',
        'postman', 'swagger', 'vs code', 'intellij', 'eclipse',
        'visual studio', 'xcode', 'android studio', 'indesign', 'crm'
    ],
    'soft_skills': [
        'leadership', 'communication', 'teamwork', 'problem solving',
        'critical thinking', 'time management', 'adaptability',
        'creativity', 'collaboration', 'presentation', 'mentoring',
        'project management', 'agile', 'scrum', 'kanban', 'testing',
        'software engineering', 'web development', 'architecture'
    ]
}

# Flatten all skills into one searchable set
ALL_SKILLS = []
for category_skills in SKILLS_DB.values():
    ALL_SKILLS.extend(category_skills)

# Degree keywords for education extraction
DEGREE_KEYWORDS = [
    'b.tech', 'b.e', 'b.sc', 'b.com', 'b.a', 'bca', 'bba',
    'm.tech', 'm.e', 'm.sc', 'mca', 'mba', 'm.a',
    'bachelor', 'master', 'phd', 'ph.d', 'doctorate', 'diploma',
    'associate', 'b.s', 'm.s', 'b.eng', 'm.eng',
    '10th', '12th', 'ssc', 'hsc', 'intermediate', 'matric',
    'b.arch', 'b.pharm', 'mbbs', 'llb', 'llm'
]

# Common certifications
CERT_KEYWORDS = [
    'certified', 'certificate', 'certification', 'aws certified',
    'azure certified', 'google certified', 'cisco', 'ccna', 'ccnp',
    'pmp', 'scrum master', 'agile', 'six sigma', 'itil',
    'comptia', 'security+', 'network+', 'a+', 'oracle certified',
    'salesforce', 'tableau', 'google analytics', 'hubspot'
]


# ─── Main Extractor Class ──────────────────────────────────────────────────

class ResumeExtractor:
    """Extracts structured information from raw resume text."""

    def extract(self, text, filename=''):
        """Extract all structured fields from resume text."""
        if not text:
            return self._empty_result()

        text_lower = text.lower()
        name = self._extract_name(text, filename)
        email = self._extract_email(text)
        phone = self._extract_phone(text)
        skills = self._extract_skills(text_lower)
        education = self._extract_education(text)
        experience = self._extract_experience(text)
        job_title = self._extract_job_title(text)
        years_exp = self._estimate_years_experience(text)
        projects = self._extract_projects(text)
        certifications = self._extract_certifications(text)
        languages = self._extract_languages(text_lower)
        achievements = self._extract_achievements(text)
        linkedin = self._extract_linkedin(text)
        github = self._extract_github(text)

        parsed_dict = {
            'name': name, 'email': email, 'phone': phone, 'job_title': job_title,
            'skills': skills, 'education': education, 'experience': experience,
            'years_exp': years_exp, 'projects': projects, 'certifications': certifications,
            'languages': languages, 'achievements': achievements, 'linkedin': linkedin, 'github': github
        }

        summary = self._extract_summary(text, parsed_dict)
        parsed_dict['summary'] = summary
        return parsed_dict

    def _empty_result(self):
        return {
            'name': '', 'email': '', 'phone': '', 'job_title': 'Software Professional',
            'skills': [], 'education': [], 'experience': [], 'years_exp': 0,
            'projects': [], 'certifications': [], 'languages': [],
            'achievements': [], 'linkedin': '', 'github': '', 'summary': ''
        }

    # ── Name ────────────────────────────────────────────────────────────────

    def _extract_name(self, text, filename=''):
        """
        Extract ONLY clean Person Name (First + Surname) using spaCy Person NER,
        header line filtering, and filename fallback. Filters out skill keywords (e.g. Creative Suite).
        """
        if not text:
            text = ''

        stop_words = {
            'creative', 'suite', 'creative suite', 'adobe', 'microsoft', 'office',
            'amazon', 'video', 'graphic', 'employment', 'senior', 'front', 'end',
            'germany', 'associate', 'specialist', 'professional', 'engineer',
            'developer', 'designer', 'resume', 'cv', 'curriculum', 'vitae', 'page',
            'profile', 'summary', 'experience', 'education', 'skills', 'contact',
            'phone', 'email', 'links', 'project', 'projects', 'about', 'manager',
            'lead', 'intern', 'junior', 'architect', 'principal', 'full', 'stack',
            'software', 'web', 'ui/ux', 'ux/ui', 'ui', 'ux', 'tools', 'technical',
            'soft', 'work', 'history', 'academic', 'qualifications', 'certifications'
        }

        def is_name_token(t):
            t_low = t.lower()
            if t_low in stop_words or len(t) < 2 or not t.isalpha():
                return False
            # Check against skill database items
            if t_low in ALL_SKILLS and len(t_low) > 3:
                return False
            return True

        # Step 1: spaCy Person NER on header text
        if SPACY_AVAILABLE and nlp:
            try:
                doc = nlp(text[:400])
                for ent in doc.ents:
                    if ent.label_ == 'PERSON':
                        tokens = [w.strip() for w in ent.text.split() if is_name_token(w)]
                        if 2 <= len(tokens) <= 3:
                            return ' '.join(t.capitalize() for t in tokens)
            except Exception:
                pass

        # Step 2: Search top 5 lines for a strict 2-word Person Name (First Last)
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:5]:
            clean_l = re.split(r'[\(\d\+@]|http|www|\.com|Summary|Profile|Experience|Objective|Phone|Email', line, flags=re.IGNORECASE)[0].strip()
            tokens = [w.strip() for w in clean_l.split() if is_name_token(w)]

            if 2 <= len(tokens) <= 3:
                return ' '.join(t.capitalize() for t in tokens)

        # Step 3: Parse original filename fallback
        if filename:
            clean_fn = re.sub(r'^\d+[\-_]?', '', filename)
            clean_fn = re.sub(r'\.(pdf|docx|doc)$', '', clean_fn, flags=re.IGNORECASE)
            clean_fn = re.sub(r'[\-_]', ' ', clean_fn)
            tokens = [w.strip() for w in clean_fn.split() if is_name_token(w)]
            if 2 <= len(tokens) <= 3:
                return ' '.join(t.capitalize() for t in tokens)

        # Step 4: Fallback to first 2 valid tokens
        if lines:
            tokens = [w.strip() for w in re.sub(r'[^a-zA-Z\s]', ' ', lines[0]).split() if is_name_token(w)]
            if len(tokens) >= 2:
                return f"{tokens[0].capitalize()} {tokens[1].capitalize()}"
            elif len(tokens) == 1:
                return tokens[0].capitalize()

        return 'Candidate'

    # ── Email ────────────────────────────────────────────────────────────────

    def _extract_email(self, text):
        pattern = r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
        matches = re.findall(pattern, text)
        return matches[0] if matches else ''

    # ── Phone ────────────────────────────────────────────────────────────────

    def _extract_phone(self, text):
        patterns = [
            r'\+?\d[\d\s\-().]{9,15}\d',   # International format
            r'\b\d{10}\b',                  # 10-digit
            r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',  # US format
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0].strip()
        return ''

    # ── Skills ───────────────────────────────────────────────────────────────

    def _extract_skills(self, text_lower):
        """Find all known skills present in the resume text."""
        found = set()
        for skill in ALL_SKILLS:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found.add(skill)
        return sorted(list(found))

    # ── Education ────────────────────────────────────────────────────────────

    def _extract_education(self, text):
        education = []
        lines = text.split('\n')
        in_section = False
        section_lines = []
        for line in lines:
            ll = line.lower()
            if any(k in ll for k in ['education', 'academic', 'qualification']):
                in_section = True
            elif in_section and any(k in ll for k in
                                    ['experience', 'project', 'skill', 'certification',
                                     'achievement', 'publication', 'award', 'interest']):
                in_section = False
            if in_section:
                section_lines.append(line.strip())

        search_text = '\n'.join(section_lines) if section_lines else text
        for line in search_text.split('\n'):
            ll = line.lower()
            if any(re.search(r'\b' + re.escape(deg) + r'\b', ll) for deg in DEGREE_KEYWORDS) and line.strip():
                if len(line.strip()) < 120 and '@' not in line:
                    education.append(line.strip())

        return list(dict.fromkeys(education))[:6]

    # ── Experience ───────────────────────────────────────────────────────────

    def _extract_experience(self, text):
        experience = []
        lines = text.split('\n')
        job_title_keywords = [
            'engineer', 'developer', 'analyst', 'manager', 'intern',
            'designer', 'architect', 'consultant', 'specialist', 'lead',
            'director', 'head', 'officer', 'executive', 'associate',
            'coordinator', 'administrator', 'scientist', 'researcher'
        ]
        in_section = False
        for line in lines:
            ll = line.lower()
            if any(k in ll for k in ['experience', 'employment', 'work history', 'career']):
                in_section = True
            elif in_section and any(k in ll for k in
                                    ['education', 'skill', 'project', 'certification',
                                     'achievement', 'language', 'interest']):
                in_section = False

            if in_section and line.strip():
                if any(kw in ll for kw in job_title_keywords):
                    experience.append(line.strip())

        return list(dict.fromkeys(experience))[:8]

    # ── Years of Experience ───────────────────────────────────────────────────

    def _estimate_years_experience(self, text):
        pattern1 = r'(\d+)\+?\s+(?:years?|yrs?)\s+(?:of\s+)?(?:experience|exp)'
        match = re.search(pattern1, text, re.IGNORECASE)
        if match:
            return int(match.group(1))

        year_pattern = r'\b(20\d{2}|19\d{2})\b'
        years = [int(y) for y in re.findall(year_pattern, text)]
        if len(years) >= 2:
            span = max(years) - min(years)
            return max(0, min(span, 30))

        return 0

    # ── Projects ─────────────────────────────────────────────────────────────

    def _extract_projects(self, text):
        projects = []
        lines = text.split('\n')
        in_section = False
        for line in lines:
            ll = line.lower()
            if 'project' in ll and len(line.strip()) < 30:
                in_section = True
            elif in_section and any(k in ll for k in
                                    ['experience', 'education', 'skill', 'certification',
                                     'achievement', 'interest', 'reference']):
                in_section = False

            if in_section and line.strip() and len(line.strip()) > 10:
                projects.append(line.strip())

        return projects[:6]

    # ── Certifications ────────────────────────────────────────────────────────

    def _extract_certifications(self, text):
        certs = []
        lines = text.split('\n')
        for line in lines:
            ll = line.lower()
            if any(k in ll for k in CERT_KEYWORDS) and line.strip():
                certs.append(line.strip())
        return list(dict.fromkeys(certs))[:8]

    # ── Languages ────────────────────────────────────────────────────────────

    def _extract_languages(self, text_lower):
        human_langs = [
            'english', 'hindi', 'tamil', 'telugu', 'kannada', 'malayalam',
            'marathi', 'bengali', 'gujarati', 'punjabi', 'urdu', 'arabic',
            'french', 'german', 'spanish', 'portuguese', 'japanese',
            'chinese', 'mandarin', 'korean', 'russian', 'italian'
        ]
        found = []
        for lang in human_langs:
            if lang in text_lower:
                found.append(lang.capitalize())
        return found

    # ── Achievements ──────────────────────────────────────────────────────────

    def _extract_achievements(self, text):
        achievements = []
        lines = text.split('\n')
        achieve_keywords = [
            'award', 'achievement', 'honour', 'honor', 'winner',
            'ranked', 'first', 'second', 'gold', 'silver', 'scholarship',
            'published', 'patent', 'recognition'
        ]
        for line in lines:
            ll = line.lower()
            if any(k in ll for k in achieve_keywords) and line.strip():
                achievements.append(line.strip())
        return list(dict.fromkeys(achievements))[:6]

    # ── LinkedIn / GitHub ─────────────────────────────────────────────────────

    def _extract_linkedin(self, text):
        pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w\-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else ''

    def _extract_github(self, text):
        pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w\-]+'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(0) if match else ''

    # ── Job Title ─────────────────────────────────────────────────────────────

    def _extract_job_title(self, text):
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        for line in lines[:5]:
            m = re.search(r'\b(ui/ux designer|ux/ui designer|ux designer|ui designer|interaction designer|product designer|graphic designer|software engineer|full stack developer|backend developer|frontend developer|web developer|java developer)\b', line, re.IGNORECASE)
            if m:
                return m.group(0).upper().replace('UX', 'UX').replace('UI', 'UI').title().replace('Ux', 'UX').replace('Ui', 'UI')

        known_titles = [
            'ui/ux designer', 'ux/ui designer', 'ux designer', 'ui designer',
            'interaction designer', 'product designer', 'software engineer',
            'full stack developer', 'backend developer', 'frontend developer',
            'web developer', 'java developer', 'python developer', 'data scientist',
            'devops engineer', 'machine learning engineer', 'cloud architect',
            'product manager', 'system administrator', 'mobile developer', 'qa engineer'
        ]
        for t in known_titles:
            if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE):
                return t.title().replace('Ux', 'UX').replace('Ui', 'UI')

        for line in lines[:5]:
            if any(k in line.lower() for k in ['developer', 'engineer', 'analyst', 'manager', 'architect', 'lead', 'designer']):
                if len(line) < 40 and '@' not in line:
                    return line

        return 'Software Professional'

    # ── Summary ───────────────────────────────────────────────────────────────

    def _extract_summary(self, text, parsed_dict=None):
        """Extract or generate a strict, clean 4-line candidate summary."""
        skills = (parsed_dict.get('skills') if parsed_dict else []) or []
        edu = (parsed_dict.get('education') if parsed_dict else []) or []
        title = (parsed_dict.get('job_title') if parsed_dict else '') or ''
        name = (parsed_dict.get('name') if parsed_dict else '') or 'Candidate'
        years = (parsed_dict.get('years_exp') if parsed_dict else 0) or 0

        # Clean name if duplicated
        name_parts = name.split()
        if len(name_parts) >= 2 and name_parts[0].lower() == name_parts[-1].lower():
            name = ' '.join(name_parts[:-1])

        skills_str = ', '.join(skills[:8]) if skills else 'General Technical Skills'

        lines = []

        # Line 1: Role & Experience
        if title:
            lines.append(f"{name} is a {title} with {years}+ years of experience." if years else f"{name} is a {title}.")
        else:
            lines.append(f"{name} is an experienced technical professional.")

        # Line 2: Skill Keywords
        lines.append(f"Core Technical Skills & Keywords: {skills_str}.")

        # Line 3: Background & Expertise sentence snippet
        summary_snippet = ''
        match = re.search(r'(?:summary|profile|about|objective)\s*[:\-\u2014]?\s*([^\n\r]+)', text, re.IGNORECASE)
        if match:
            raw_p = match.group(1).strip()
            raw_p = re.split(r'\b(?:Experience|Employment|Education|Skills|Work History|Soft Skills|Technical Skills)\b', raw_p, flags=re.IGNORECASE)[0].strip()
            raw_p = re.sub(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', '', raw_p)
            raw_p = re.sub(r'\+?\d[\d\s\-().]{8,}\d', '', raw_p)
            raw_p = ' '.join(raw_p.split())
            if '.' in raw_p:
                summary_snippet = raw_p.split('.')[0].strip() + '.'
            elif len(raw_p) > 20:
                summary_snippet = raw_p[:140].rsplit(' ', 1)[0].rstrip(', ') + '.'

        if summary_snippet and len(summary_snippet) > 15:
            lines.append(summary_snippet)
        else:
            lines.append(f"Experienced in {title.lower() if title else 'software engineering'} with a focus on system architecture, design processes, and product delivery.")

        # Line 4: Education or Domain highlight
        if edu and len(str(edu[0])) > 5:
            clean_edu = str(edu[0])[:90].strip()
            clean_edu = re.sub(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b', '', clean_edu)
            clean_edu = re.sub(r'\+?\d[\d\s\-().]{8,}\d', '', clean_edu).strip()
            lines.append(f"Education: {clean_edu}.")
        else:
            lines.append("Demonstrated academic and practical domain expertise.")

        return "\n".join(lines[:4])


# Module-level instance — import and use directly
extractor = ResumeExtractor()
