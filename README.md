# 🎯 ResumeMatch.ai — AI-Powered Resume Screening

> **Smart Resume Screening Powered by Artificial Intelligence**

ResumeMatch.ai automatically reads, parses, scores, and ranks resumes against a Job Description — helping HR recruiters shortlist top candidates in seconds.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 📤 Resume Upload | Single/bulk PDF & DOCX upload with drag & drop |
| 🧠 AI Parsing | spaCy + regex extracts name, email, skills, education, experience |
| 🎯 ATS Scoring | Weighted match: Skills 40% + Keywords 30% + Experience 20% + Education 10% |
| 🏆 Candidate Ranking | Auto-ranked by ATS score with medal icons |
| 📊 Analytics | 7 interactive Plotly charts |
| 📄 Reports | PDF + CSV export |
| 💬 Interview Questions | AI-generated per candidate |
| ⚖️ Compare | Side-by-side candidate comparison |
| 🔖 Bookmarks/Notes/Tags | Recruiter workflow tools |
| 🌙 Dark/Light Mode | Toggle anywhere |
| 🔐 Auth | Register, Login, bcrypt passwords |

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (auto-created)
- **AI**: spaCy, Sentence Transformers, scikit-learn
- **Parsing**: pdfplumber, PyPDF2, python-docx
- **Auth**: bcrypt
- **Reports**: fpdf2, pandas
- **Charts**: Plotly.js
- **Frontend**: HTML5, CSS3 (Glassmorphism), Vanilla JS

---

## ⚡ Quick Start

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download spaCy Model

```bash
python -m spacy download en_core_web_sm
```

### 3. Run the Application

```bash
python app.py
```

### 4. Open in Browser

```
http://127.0.0.1:5000
```

---

## 📁 Project Structure

```
ResumeMatch.ai/
├── app.py              # Flask app entry point
├── config.py           # All configuration settings
├── requirements.txt    # Python dependencies
├── database/           # SQLite database (auto-created)
├── uploads/            # Uploaded resumes
├── reports/            # Generated PDF/CSV reports
├── ai/                 # AI modules
│   ├── extractor.py    # Resume info extraction (NLP)
│   ├── matcher.py      # ATS matching engine
│   └── question_gen.py # Interview question generator
├── services/           # Business logic
│   ├── db_service.py   # All database operations
│   ├── resume_parser.py# PDF/DOCX text extraction
│   ├── ats_engine.py   # ATS scoring (calls matcher)
│   ├── report_service.py     # PDF/CSV generation
│   └── analytics_service.py  # Analytics data
├── routes/             # Flask blueprints
│   ├── auth.py         # Login/Register/Profile
│   ├── dashboard.py    # Dashboard
│   ├── resume.py       # Resume management
│   ├── jd.py           # Job descriptions
│   ├── analysis.py     # AI analysis
│   ├── reports.py      # Report downloads
│   └── analytics.py    # Analytics charts
├── utils/              # Helpers
│   ├── helpers.py      # File utils, scoring utils
│   └── validators.py   # Input validation
├── static/             # CSS, JS, assets
│   ├── css/style.css   # Main stylesheet
│   └── js/             # main.js, upload.js, charts.js
└── templates/          # Jinja2 HTML templates
    ├── base.html        # Base layout
    ├── landing.html     # Landing page
    ├── auth/            # Login, Register, Password
    ├── dashboard/       # Dashboard, Profile, Bookmarks
    ├── resume/          # Upload, List, Detail
    ├── jd/              # Create, List, Edit, View JD
    ├── analysis/        # Run, Result, Ranking, Compare
    ├── analytics/       # Analytics charts
    ├── reports/         # Reports page
    └── errors/          # 404, 500 pages
```

---

## 🔌 API Routes

| Method | Route | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/auth/login` | Login page |
| POST | `/auth/login` | Process login |
| GET | `/auth/register` | Register page |
| POST | `/auth/register` | Create account |
| GET | `/dashboard/` | Dashboard |
| GET | `/resume/upload` | Upload page |
| POST | `/resume/upload` | Process uploads |
| GET | `/resume/list` | Candidate list |
| GET | `/resume/<id>` | Candidate detail |
| POST | `/resume/<id>/delete` | Delete resume |
| GET | `/resume/<id>/download` | Download file |
| POST | `/resume/<id>/bookmark` | Toggle bookmark (AJAX) |
| GET | `/jd/create` | Create JD page |
| POST | `/jd/create` | Save JD |
| GET | `/jd/list` | JD list |
| GET | `/analysis/run` | Run analysis page |
| POST | `/analysis/run` | Run single analysis |
| POST | `/analysis/bulk` | Bulk analyze all candidates |
| GET | `/analysis/result` | View ATS result |
| GET | `/analysis/ranking` | Ranked candidate list |
| GET | `/analysis/compare` | Compare two candidates |
| POST | `/analysis/status/<id>` | Update status (AJAX) |
| GET | `/analytics/` | Analytics charts |
| GET | `/reports/` | Reports page |
| GET | `/reports/candidate/<id>/pdf` | Download candidate PDF |
| GET | `/reports/ranking/<jd_id>/pdf` | Download ranking PDF |
| GET | `/reports/export/csv` | Download CSV |

---

## 🧠 ATS Scoring Algorithm

```
Overall ATS Score = 
  Skills Match     × 0.40   (40%)
  Keyword Match    × 0.30   (30%)
  Experience Match × 0.20   (20%)
  Education Match  × 0.10   (10%)
```

**Skills Match**: Resume skills intersected with JD skills ÷ total JD skills × 100

**Keyword Match**: TF-IDF keyword presence + Semantic similarity (Sentence Transformers)

**Experience Match**: Candidate years ÷ required years × 100 (capped at 100)

**Education Match**: Degree level score (PhD=6, Master=5, Bachelor=4, Diploma=3, 12th=2, 10th=1)

---

## 🎓 Presentation Guide (College Project)

### Slide 1: Problem
"HR recruiters receive 200+ resumes per job posting. Manual screening takes 3-5 days."

### Slide 2: Solution
"ResumeMatch.ai uses AI to automatically read, parse, and score resumes against job descriptions in seconds."

### Slide 3: Tech Stack
Show the tech stack table above.

### Slide 4: Architecture
Explain the 3-layer architecture: Routes → Services → Database.

### Slide 5: AI Algorithm
Show the ATS scoring formula. Explain NLP, TF-IDF, semantic similarity.

### Slide 6: Demo
Live demo: Upload a resume → Create JD → Run Analysis → Show score → Download PDF.

### Slide 7: Results
Show the Analytics dashboard with charts.

---

## 🚀 Deployment

### Local Development
```bash
python app.py
```

### Production (PythonAnywhere / Render / Railway)
1. Push code to GitHub
2. Connect to PythonAnywhere / Render
3. Set `SECRET_KEY` environment variable
4. Run `pip install -r requirements.txt`
5. Run `python -m spacy download en_core_web_sm`
6. Start with gunicorn: `gunicorn app:create_app()`

---

## 🔐 Default Setup

- No default users — register your own account
- Database auto-creates on first run
- All data stored locally in `database/resumematch.db`

---

## 📧 Credits

Built with ❤️ using Flask, spaCy, Sentence Transformers, and Plotly.

**ResumeMatch.ai** — Smart Resume Screening Powered by Artificial Intelligence
