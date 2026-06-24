

# AI Resume Analyzer

A Streamlit application that analyzes a PDF resume against a target job description, calculates a skill match percentage, highlights missing skills, offers ATS tips, generates AI recommendations, and suggests a salary range to help students improve resumes faster.

## Features

- Upload resume PDF
- Extract resume text from PDF
- Paste a target job description
- Detect resume and job-description skills
- Calculate matching percentage
- Display matched and missing skills
- Generate AI recommendations with Gemini
- ATS-style resume tips
- Keyword gap view
- Downloadable summary draft and edit checklist
- Job snapshot and salary estimate
- Modern Streamlit UI

## Project Structure

```text
AI-Resume-Analyzer/
├── app.py
├── requirements.txt
├── README.md
└── assets/
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Configure Gemini API key.

Option A: environment variable

```bash
export GEMINI_API_KEY="your_gemini_api_key"
```

Option B: Streamlit secrets

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
```

4. Run the app.

```bash
streamlit run app.py
```

## Notes

The skill matcher uses a curated keyword list inside `app.py`. You can expand `SKILL_KEYWORDS` to better match a specific domain, role, or hiring process.
