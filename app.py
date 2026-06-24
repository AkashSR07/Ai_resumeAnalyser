import os
import re
from io import BytesIO

import PyPDF2
import streamlit as st
from google import genai
from google.genai import types


# A practical seed list for common technical and professional skills.
# Users can extend this list as their hiring domain grows.
SKILL_KEYWORDS = {
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "sql",
    "nosql",
    "html",
    "css",
    "react",
    "angular",
    "vue",
    "node.js",
    "django",
    "flask",
    "fastapi",
    "spring boot",
    "streamlit",
    "pandas",
    "numpy",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "machine learning",
    "deep learning",
    "nlp",
    "computer vision",
    "data analysis",
    "data visualization",
    "power bi",
    "tableau",
    "excel",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "git",
    "github",
    "ci/cd",
    "linux",
    "rest api",
    "graphql",
    "microservices",
    "mongodb",
    "postgresql",
    "mysql",
    "redis",
    "spark",
    "hadoop",
    "airflow",
    "devops",
    "agile",
    "scrum",
    "jira",
    "communication",
    "leadership",
    "problem solving",
    "project management",
}


st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon=":page_facing_up:",
    layout="wide",
    initial_sidebar_state="expanded",
)


def load_css() -> None:
    """Apply lightweight custom CSS for a cleaner Streamlit interface."""
    st.markdown(
        """
        <style>
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                max-width: 1180px;
            }

            .hero {
                padding: 1.4rem 1.6rem;
                border-radius: 14px;
                background: linear-gradient(135deg, #101828 0%, #175cd3 100%);
                color: white;
                margin-bottom: 1.2rem;
            }

            .hero h1 {
                margin: 0;
                font-size: 2.2rem;
                letter-spacing: 0;
            }

            .hero p {
                margin: .45rem 0 0;
                color: #e0e7ff;
                font-size: 1rem;
            }

            .metric-card {
                padding: 1rem;
                border: 1px solid #e4e7ec;
                border-radius: 10px;
                background: #ffffff;
                box-shadow: 0 1px 2px rgba(16, 24, 40, 0.06);
            }

            .skill-pill {
                display: inline-block;
                padding: .35rem .6rem;
                margin: .2rem .25rem .2rem 0;
                border-radius: 999px;
                background: #eef4ff;
                color: #1849a9;
                border: 1px solid #c7d7fe;
                font-size: .9rem;
            }

            .missing-pill {
                display: inline-block;
                padding: .35rem .6rem;
                margin: .2rem .25rem .2rem 0;
                border-radius: 999px;
                background: #fff1f3;
                color: #c01048;
                border: 1px solid #ffcdd9;
                font-size: .9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def normalize_text(text: str) -> str:
    """Normalize text to make skill matching consistent."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_text_from_pdf(uploaded_file) -> str:
    """Extract readable text from an uploaded PDF resume."""
    try:
        pdf_bytes = BytesIO(uploaded_file.read())
        reader = PyPDF2.PdfReader(pdf_bytes)
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    except Exception as exc:
        st.error(f"Could not extract text from the PDF: {exc}")
        return ""


def skill_pattern(skill: str) -> str:
    """Build a regex pattern that handles symbols and word boundaries."""
    escaped = re.escape(skill)
    return rf"(?<![a-zA-Z0-9]){escaped}(?![a-zA-Z0-9])"


def extract_skills(text: str) -> set[str]:
    """Find known skills inside a block of text."""
    normalized = normalize_text(text)
    found_skills = set()

    for skill in SKILL_KEYWORDS:
        if re.search(skill_pattern(skill), normalized):
            found_skills.add(skill)

    return found_skills


def calculate_match(resume_skills: set[str], job_skills: set[str]) -> tuple[int, set[str], set[str]]:
    """Calculate match percentage and identify matching and missing skills."""
    if not job_skills:
        return 0, set(), set()

    matched_skills = resume_skills.intersection(job_skills)
    missing_skills = job_skills.difference(resume_skills)
    match_percentage = round((len(matched_skills) / len(job_skills)) * 100)

    return match_percentage, matched_skills, missing_skills


def infer_experience_level(resume_text: str) -> tuple[str, float]:
    """Estimate experience level from common resume signals."""
    normalized = normalize_text(resume_text)
    years_found = [float(value) for value in re.findall(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", normalized)]
    max_years = max(years_found) if years_found else 0.0

    if any(word in normalized for word in ["intern", "internship", "fresher", "recent graduate", "student"]):
        if max_years >= 2:
            return "Entry-level", max_years
        return "Fresher", max_years

    if max_years >= 3:
        return "Experienced", max_years
    if max_years >= 1:
        return "Entry-level", max_years
    return "Fresher", max_years


def estimate_salary_range(
    experience_level: str,
    match_percentage: int,
    resume_skills: set[str],
) -> tuple[str, str]:
    """Estimate a simple salary band in INR LPA for students and early-career candidates."""
    skill_bonus = 0.5 if len(resume_skills) >= 10 else 0.0
    match_bonus = 0.5 if match_percentage >= 70 else 0.0

    if experience_level == "Experienced":
        minimum = 6.0 + skill_bonus + match_bonus
        upper = minimum + 6.0
    elif experience_level == "Entry-level":
        minimum = 3.0 + skill_bonus + match_bonus
        upper = minimum + 3.5
    else:
        minimum = 2.5 + skill_bonus + match_bonus
        upper = minimum + 2.5

    return f"₹{minimum:.1f} LPA", f"₹{upper:.1f} LPA"


def summarize_job_description(job_description: str) -> str:
    """Create a short plain-language summary of the job description."""
    sentences = re.split(r"(?<=[.!?])\s+", job_description.strip())
    headline = " ".join(sentences[:2]).strip()
    return headline or "Job description summary unavailable."


def build_resume_action_plan(
    resume_skills: set[str],
    matched_skills: set[str],
    missing_skills: set[str],
    job_description: str,
) -> list[str]:
    """Create practical resume-editing suggestions for students."""
    actions = []

    if missing_skills:
        skill_list = ", ".join(sorted(missing_skills)[:6])
        actions.append(
            f"Add the most relevant missing keywords naturally in your skills and project sections: {skill_list}."
        )

    if matched_skills:
        actions.append(
            f"Move matched strengths like {', '.join(sorted(matched_skills)[:4])} higher on the page, especially in your summary and top skills section."
        )

    if "project" not in normalize_text(job_description):
        actions.append(
            "Add 1-2 project bullets that show impact, tools used, and measurable results."
        )
    else:
        actions.append(
            "Rewrite project bullets with action verbs, tools, and measurable outcomes to match the job language."
        )

    if len(resume_skills) < 6:
        actions.append(
            "Your resume currently has few detected skills, so add a dedicated skills section and tighten the wording in project descriptions."
        )

    actions.append(
        "Keep the resume to one page if you are a student or recent graduate."
    )

    return actions


def build_keyword_gap_notes(
    resume_skills: set[str],
    job_skills: set[str],
    missing_skills: set[str],
) -> tuple[list[str], list[str]]:
    """Split job keywords into matched and missing groups for quick scanning."""
    matched = sorted(job_skills.intersection(resume_skills))
    missing = sorted(missing_skills)
    return matched, missing


def build_ats_tips(match_percentage: int, missing_skills: set[str]) -> list[str]:
    """Generate simple ATS-friendly resume tips."""
    tips = [
        "Use a simple resume layout with standard headings like Summary, Skills, Projects, and Education.",
        "Repeat the job title or role name naturally in your summary if it matches your background.",
        "Use exact keyword spellings from the job description where they truly apply.",
        "Keep bullet points short, specific, and action-focused.",
    ]

    if match_percentage < 50:
        tips.append("Add more role-specific keywords in your projects and internship experience.")

    if missing_skills:
        tips.append(
            "Do not keyword-stuff; place missing skills only where you can honestly discuss them in projects or coursework."
        )

    return tips


def build_summary_draft(
    resume_skills: set[str],
    matched_skills: set[str],
    missing_skills: set[str],
    match_percentage: int,
) -> str:
    """Create a short downloadable summary draft for students."""
    top_strengths = ", ".join(sorted(matched_skills)[:4]) or "relevant technical and problem-solving skills"
    growth_areas = ", ".join(sorted(missing_skills)[:3]) or "job-specific tools and platforms"
    skill_count = len(resume_skills)

    return (
        "Professional Summary Draft\n"
        "--------------------------\n"
        f"Motivated student or early-career candidate with hands-on experience in {top_strengths}. "
        f"Focused on building practical projects, learning quickly, and improving alignment with roles that value {growth_areas}. "
        f"Current resume match score is {match_percentage}%, with {skill_count} detected skills highlighted for improvement.\n\n"
        "Edit this draft so it reflects your real projects, coursework, and achievements."
    )


def build_section_text(title: str, items: list[str]) -> str:
    """Format a list of items as a simple plain-text section."""
    lines = [title, "-" * len(title)]
    lines.extend(f"- {item}" for item in items)
    return "\n".join(lines)


def build_salary_note(
    experience_level: str,
    minimum_salary: str,
    upper_salary: str,
    match_percentage: int,
) -> str:
    """Create a short note explaining the estimate."""
    return (
        f"Estimated salary band for this resume: {minimum_salary} to {upper_salary} per year "
        f"based on an inferred {experience_level.lower()} profile and a {match_percentage}% skill match. "
        "Treat this as a starting point for negotiation, not a fixed market quote."
    )


def format_friendly_gemini_error(error_text: str) -> str:
    """Turn raw Gemini/API failures into a student-friendly message."""
    lowered = error_text.lower()
    if "permission_denied" in lowered or "denied access" in lowered:
        return (
            "Gemini is not available for this key or project right now. "
            "Your resume analysis still works, but AI recommendations need a valid Gemini-enabled project."
        )
    if "api key not valid" in lowered or "api_key_invalid" in lowered:
        return (
            "The Gemini API key is invalid. Replace it with a fresh valid key to enable AI recommendations."
        )
    if "not found" in lowered or "models/" in lowered:
        return (
            "The selected Gemini model is not available for this key. "
            "Try a newer Gemini-enabled project or keep using the built-in resume suggestions."
        )
    return (
        "Gemini recommendations are unavailable right now. "
        "You can still use the score, missing skills, and resume action plan below."
    )


def get_gemini_api_key() -> str:
    """Read Gemini API key from Streamlit secrets or environment variables."""
    try:
        return st.secrets.get("GEMINI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def generate_recommendations(
    resume_text: str,
    job_description: str,
    match_percentage: int,
    missing_skills: set[str],
) -> str:
    """Generate resume improvement recommendations using Gemini."""
    api_key = get_gemini_api_key()
    if not api_key:
        return format_friendly_gemini_error("Gemini API key is not configured.")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(api_version="v1"),
    )

    prompt = f"""
    You are an expert resume reviewer and hiring assistant.

    Resume text:
    {resume_text[:6000]}

    Job description:
    {job_description[:4000]}

    Current matching percentage: {match_percentage}%
    Missing skills: {", ".join(sorted(missing_skills)) or "None detected"}

    Give concise, practical recommendations to improve this resume for the job.
    Include:
    1. Skills to add or strengthen
    2. Resume bullet improvements
    3. Keyword optimization ideas
    4. A short action plan
    """

    # Ask the SDK which base models are actually available for this key,
    # then choose the first text-generation model that looks usable.
    available_models = []
    try:
        available_models = list(client.models.list())
    except Exception as exc:
        return format_friendly_gemini_error(str(exc))

    candidate_models = []
    for model in available_models:
        model_name = getattr(model, "name", "") or ""
        supported_actions = getattr(model, "supported_actions", None) or []
        if "generateContent" in supported_actions and "gemini" in model_name:
            candidate_models.append(model_name.removeprefix("models/"))

    # Prefer the newest common text models if the list does not reveal a usable one.
    # Keep the list free of legacy models so we do not fall back to v1beta-only names.
    fallback_models = ["gemini-2.5-flash", "gemini-2.0-flash"]
    for model_name in fallback_models:
        if model_name not in candidate_models:
            candidate_models.append(model_name)

    if not candidate_models:
        model_names = ", ".join(
            (getattr(model, "name", "") or "").removeprefix("models/")
            for model in available_models
        )
        return format_friendly_gemini_error(
            "No usable Gemini text models were returned. "
            f"Available models: {model_names or 'none'}"
        )

    last_error = None
    for model_name in candidate_models:
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            text = getattr(response, "text", None)
            if text:
                return text
        except Exception as exc:
            last_error = exc

    return format_friendly_gemini_error(str(last_error or "Unknown Gemini error"))


def render_skill_pills(skills: set[str], css_class: str) -> None:
    """Render skill names as compact pills."""
    if not skills:
        st.write("None found")
        return

    pills = "".join(
        f'<span class="{css_class}">{skill}</span>' for skill in sorted(skills)
    )
    st.markdown(pills, unsafe_allow_html=True)


def main() -> None:
    load_css()

    st.markdown(
        """
        <div class="hero">
            <h1>AI Resume Analyzer</h1>
            <p>Upload a resume, paste a job description, and get a focused match analysis with AI recommendations.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Inputs")
        uploaded_resume = st.file_uploader("Upload resume PDF", type=["pdf"])
        analyze_button = st.button("Analyze Resume", type="primary", use_container_width=True)

        st.divider()
        st.caption("Gemini setup")
        if get_gemini_api_key():
            st.success("Gemini API key detected")
        else:
            st.warning("Set GEMINI_API_KEY for AI recommendations")

    job_description = st.text_area(
        "Paste job description",
        height=260,
        placeholder="Paste the target job description here...",
    )

    if analyze_button:
        if uploaded_resume is None:
            st.warning("Please upload a resume PDF.")
            return

        if not job_description.strip():
            st.warning("Please paste a job description.")
            return

        with st.spinner("Reading resume and comparing skills..."):
            resume_text = extract_text_from_pdf(uploaded_resume)

            if not resume_text:
                st.error("No text could be extracted from this PDF.")
                return

            resume_skills = extract_skills(resume_text)
            job_skills = extract_skills(job_description)
            match_percentage, matched_skills, missing_skills = calculate_match(
                resume_skills,
                job_skills,
            )
            action_plan = build_resume_action_plan(
                resume_skills,
                matched_skills,
                missing_skills,
                job_description,
            )
            experience_level, estimated_years = infer_experience_level(resume_text)
            minimum_salary, upper_salary = estimate_salary_range(
                experience_level,
                match_percentage,
                resume_skills,
            )
            salary_note = build_salary_note(
                experience_level,
                minimum_salary,
                upper_salary,
                match_percentage,
            )
            job_snapshot = summarize_job_description(job_description)
            matched_job_keywords, missing_job_keywords = build_keyword_gap_notes(
                resume_skills,
                job_skills,
                missing_skills,
            )
            ats_tips = build_ats_tips(match_percentage, missing_skills)
            summary_draft = build_summary_draft(
                resume_skills,
                matched_skills,
                missing_skills,
                match_percentage,
            )

        metric_cols = st.columns(4)
        metric_cols[0].metric("Match", f"{match_percentage}%")
        metric_cols[1].metric("Resume Skills", len(resume_skills))
        metric_cols[2].metric("Job Skills", len(job_skills))
        metric_cols[3].metric("Missing Skills", len(missing_skills))

        st.progress(match_percentage / 100)

        tab_summary, tab_skills, tab_resume, tab_ai = st.tabs(
            ["Summary", "Skills", "Extracted Resume Text", "AI Recommendations"]
        )

        with tab_summary:
            st.subheader("Fit Summary")
            if match_percentage >= 75:
                st.success("Strong match. The resume already reflects many job requirements.")
            elif match_percentage >= 45:
                st.info("Moderate match. A few targeted updates could improve alignment.")
            else:
                st.warning("Low match. The resume needs stronger keyword and skill alignment.")

            st.subheader("Job Snapshot")
            st.write(job_snapshot)

            st.write(
                "The score is based on skills detected in both the resume and job description. "
                "Use the missing skills list to guide resume updates and interview preparation."
            )

            st.subheader("Resume Level and Pay Estimate")
            st.write(
                f"Detected level: **{experience_level}**"
                + (f" (`~{estimated_years:.1f}` years inferred)" if estimated_years else "")
            )
            st.write(salary_note)

            st.subheader("Resume Action Plan")
            for item in action_plan:
                st.write(f"- {item}")

            st.subheader("ATS Tips")
            for tip in ats_tips:
                st.write(f"- {tip}")

            st.download_button(
                "Download Summary Draft",
                data=summary_draft + f"\n\n{salary_note}\n\nJob Snapshot:\n{job_snapshot}\n",
                file_name="resume_summary_draft.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with tab_skills:
            left_col, right_col = st.columns(2)

            with left_col:
                st.subheader("Matched Skills")
                render_skill_pills(matched_skills, "skill-pill")

            with right_col:
                st.subheader("Missing Skills")
                render_skill_pills(missing_skills, "missing-pill")

            st.subheader("All Resume Skills Detected")
            render_skill_pills(resume_skills, "skill-pill")

            st.subheader("Keyword Gap View")
            gap_left, gap_right = st.columns(2)
            with gap_left:
                st.markdown("**Matched keywords from the job description**")
                if matched_job_keywords:
                    st.write(", ".join(matched_job_keywords))
                else:
                    st.write("None detected yet")
            with gap_right:
                st.markdown("**Missing keywords from the job description**")
                if missing_job_keywords:
                    st.write(", ".join(missing_job_keywords))
                else:
                    st.write("None missing")

        with tab_resume:
            st.subheader("Extracted Text")
            st.text_area("Resume text", resume_text, height=420)

        with tab_ai:
            st.subheader("Gemini Recommendations")
            with st.spinner("Generating recommendations with Gemini..."):
                recommendations = generate_recommendations(
                    resume_text,
                    job_description,
                    match_percentage,
                    missing_skills,
                )
            if recommendations.startswith("Gemini recommendations are unavailable"):
                st.info(recommendations)
            elif recommendations.startswith("The Gemini API key is invalid") or recommendations.startswith("Gemini is not available"):
                st.warning(recommendations)
            else:
                st.markdown(recommendations)

            st.subheader("Quick Edit Starter")
            starter_text = build_section_text("Resume upgrade checklist", action_plan[:])
            st.download_button(
                "Download Edit Checklist",
                data=starter_text,
                file_name="resume_edit_checklist.txt",
                mime="text/plain",
                use_container_width=True,
            )
    else:
        st.info("Upload a resume PDF, paste a job description, then click Analyze Resume.")


if __name__ == "__main__":
    main()
