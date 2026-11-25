"""
AI Resume Analyzer & ATS Score Checker
A modern Streamlit application powered by Google Gemini API (google-genai) and pypdf.
"""

import os
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

# Load environment variables from .env file if available
load_dotenv()

from resume_parser import extract_text_from_pdf, analyze_resume_structure
from gemini_analyzer import (
    get_gemini_client,
    analyze_ats_fit,
    rewrite_bullet_points,
    generate_skill_roadmap,
    generate_cover_letter_and_outreach,
    generate_interview_prep,
)
from sample_data import SAMPLE_RESUMES, SAMPLE_JOB_DESCRIPTIONS

# Page Configuration
st.set_page_config(
    page_title="AI Resume Analyzer & ATS Score Checker",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown(
    """
    <style>
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        color: #ffffff;
        margin-bottom: 12px;
    }
    .score-badge {
        font-size: 2.4rem;
        font-weight: 800;
        letter-spacing: -1px;
    }
    .badge-high { color: #10b981; }
    .badge-medium { color: #f59e0b; }
    .badge-low { color: #ef4444; }

    /* Pill Badges */
    .pill-matched {
        display: inline-block;
        background-color: #064e3b;
        color: #6ee7b7;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 3px;
        border: 1px solid #059669;
    }
    .pill-missing {
        display: inline-block;
        background-color: #450a0a;
        color: #fca5a5;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        margin: 3px;
        border: 1px solid #dc2626;
    }
    .pill-section {
        display: inline-block;
        background-color: #1e1b4b;
        color: #c7d2fe;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.82rem;
        margin: 3px;
    }

    /* Comparison Box */
    .rewrite-box {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .rewrite-original {
        color: #94a3b8;
        font-style: italic;
        padding-left: 10px;
        border-left: 3px solid #ef4444;
        margin-bottom: 8px;
    }
    .rewrite-improved {
        color: #f8fafc;
        font-weight: 600;
        padding-left: 10px;
        border-left: 3px solid #10b981;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""
if "ats_results" not in st.session_state:
    st.session_state.ats_results = None
if "rewrite_results" not in st.session_state:
    st.session_state.rewrite_results = None
if "roadmap_results" not in st.session_state:
    st.session_state.roadmap_results = None
if "outreach_results" not in st.session_state:
    st.session_state.outreach_results = None
if "interview_results" not in st.session_state:
    st.session_state.interview_results = None
if "structure_results" not in st.session_state:
    st.session_state.structure_results = None
if "selected_sample_role" not in st.session_state:
    st.session_state.selected_sample_role = list(SAMPLE_JOB_DESCRIPTIONS.keys())[0]

# --- SIDEBAR CONFIGURATION ---
api_key = os.environ.get("GEMINI_API_KEY", "").strip()
selected_model = "gemini-3.5-flash"

with st.sidebar:
    st.markdown("## 🎯 ATS Control Center")
    if api_key:
        st.success("🟢 AI Engine Online & Ready")
    else:
        st.warning("⚠️ AI API Key not configured in environment.")

    st.divider()

    # Quick Sample Loader
    st.subheader("⚡ 1-Click Demo Profiles")
    st.caption("Instantly test the analyzer with pre-loaded profiles:")

    sample_choice = st.selectbox(
        "Select Demo Profile",
        options=list(SAMPLE_RESUMES.keys()),
        index=0,
    )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("Load Demo", use_container_width=True):
            st.session_state.resume_text = SAMPLE_RESUMES[sample_choice]
            # Match corresponding JD
            jd_keys = list(SAMPLE_JOB_DESCRIPTIONS.keys())
            matched_jd_key = jd_keys[0]
            if "Data Scientist" in sample_choice:
                matched_jd_key = jd_keys[1]
            elif "Product Manager" in sample_choice:
                matched_jd_key = jd_keys[2]

            st.session_state.job_description = SAMPLE_JOB_DESCRIPTIONS[matched_jd_key]
            st.session_state.structure_results = analyze_resume_structure(st.session_state.resume_text, num_pages=1)
            # Clear previous results on demo switch
            st.session_state.ats_results = None
            st.session_state.rewrite_results = None
            st.session_state.roadmap_results = None
            st.session_state.outreach_results = None
            st.session_state.interview_results = None
            st.success("Loaded demo data!")
            st.rerun()

    with col_btn2:
        if st.button("Clear All", use_container_width=True):
            st.session_state.resume_text = ""
            st.session_state.job_description = ""
            st.session_state.ats_results = None
            st.session_state.rewrite_results = None
            st.session_state.roadmap_results = None
            st.session_state.outreach_results = None
            st.session_state.interview_results = None
            st.session_state.structure_results = None
            st.rerun()

    st.divider()
    st.markdown(
        """
        **💡 How ATS Systems Work:**
        - ATS systems scan for **exact keyword matches** from the Job Description.
        - Unstructured formatting, graphics, or tables often cause extraction failures.
        - Recruiters filter candidates whose match score falls below 75-80%.
        """
    )


# --- MAIN HEADER ---
st.title("🎯 AI Resume Analyzer & ATS Score Checker")
st.markdown(
    "Evaluate your resume against real job descriptions using **Google Gemini** & **pypdf**. "
    "Get actionable keyword gaps, recruiter-vetted bullet point rewrites, upskilling paths, and interview prep."
)

# --- INPUT SECTION (2 COLUMNS) ---
col_resume, col_jd = st.columns(2, gap="medium")

with col_resume:
    st.subheader("1. Candidate Resume")
    resume_tab_pdf, resume_tab_text = st.tabs(["📁 Upload PDF (pypdf)", "📝 Paste Text Directly"])

    with resume_tab_pdf:
        uploaded_pdf = st.file_uploader(
            "Upload your Resume in PDF format",
            type=["pdf"],
            help="Extracted using pypdf to simulate how standard Applicant Tracking Systems parse PDF documents.",
        )

        if uploaded_pdf is not None:
            with st.spinner("Extracting text via pypdf..."):
                pdf_res = extract_text_from_pdf(uploaded_pdf)
                if pdf_res["success"]:
                    st.session_state.resume_text = pdf_res["cleaned_text"]
                    st.session_state.structure_results = analyze_resume_structure(
                        st.session_state.resume_text,
                        num_pages=pdf_res["num_pages"],
                    )
                    st.success(
                        f"✅ Extracted {pdf_res['num_pages']} page(s) | {st.session_state.structure_results['word_count']} words"
                    )
                    if pdf_res["is_scanned"]:
                        st.warning("⚠️ Warning: Extracted text is very short. This PDF might be an image-only scan.")
                else:
                    st.error(f"Error parsing PDF: {pdf_res['error']}")

    with resume_tab_text:
        text_val = st.text_area(
            "Or edit / paste resume text here:",
            value=st.session_state.resume_text,
            height=280,
            placeholder="Paste your plain-text resume here...",
        )
        if text_val != st.session_state.resume_text:
            st.session_state.resume_text = text_val
            if text_val.strip():
                st.session_state.structure_results = analyze_resume_structure(text_val)

    # Resume Stats Pill Row
    if st.session_state.resume_text.strip():
        struct = st.session_state.structure_results or analyze_resume_structure(st.session_state.resume_text)
        stat_c1, stat_c2, stat_c3 = st.columns(3)
        stat_c1.metric("Word Count", struct["word_count"])
        stat_c2.metric("Reading Time", f"{struct['estimated_read_time_min']} min")
        stat_c3.metric("Bullet Points", struct["bullet_count"])

with col_jd:
    st.subheader("2. Target Job Description")
    jd_tab_custom, jd_tab_presets = st.tabs(["📋 Paste Job Description", "🏢 Choose Standard Role"])

    with jd_tab_custom:
        jd_val = st.text_area(
            "Paste target job description:",
            value=st.session_state.job_description,
            height=280,
            placeholder="Paste the job requirements, responsibilities, and qualifications...",
        )
        if jd_val != st.session_state.job_description:
            st.session_state.job_description = jd_val

    with jd_tab_presets:
        preset_role = st.selectbox(
            "Select a target role template:",
            options=list(SAMPLE_JOB_DESCRIPTIONS.keys()),
        )
        if st.button("Apply Selected Job Description", use_container_width=True):
            st.session_state.job_description = SAMPLE_JOB_DESCRIPTIONS[preset_role]
            st.rerun()


# --- ACTION BUTTON ---
st.markdown("---")
analyze_btn = st.button(
    "⚡ Analyze Resume against Job Description",
    type="primary",
    use_container_width=True,
    disabled=not (st.session_state.resume_text.strip() and st.session_state.job_description.strip()),
)

if analyze_btn:
    if not api_key:
        st.error("❌ AI API Key is not configured in the environment.")
    else:
        try:
            with st.status("🔍 Analyzing Resume with AI Engine...", expanded=True) as status:
                st.write("Initializing AI Client...")
                client = get_gemini_client(api_key)

                st.write("Computing ATS Match Score & extracting keyword gaps...")
                st.session_state.ats_results = analyze_ats_fit(
                    client=client,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.job_description,
                    model=selected_model,
                )

                st.write("Rewriting resume bullet points with XYZ / STAR formulas...")
                st.session_state.rewrite_results = rewrite_bullet_points(
                    client=client,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.job_description,
                    model=selected_model,
                )

                st.write("Generating upskilling roadmap & portfolio project recommendations...")
                st.session_state.roadmap_results = generate_skill_roadmap(
                    client=client,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.job_description,
                    model=selected_model,
                )

                st.write("Generating tailored interview preparation questions...")
                st.session_state.interview_results = generate_interview_prep(
                    client=client,
                    resume_text=st.session_state.resume_text,
                    job_description=st.session_state.job_description,
                    model=selected_model,
                )

                status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
                st.rerun()
        except Exception as e:
            st.error(f"Analysis failed: {str(e)}")


# --- RESULTS DASHBOARD ---
if st.session_state.ats_results is not None:
    ats = st.session_state.ats_results
    score = ats.get("overall_match_score", 0)

    # Score coloring
    if score >= 80:
        badge_class = "badge-high"
        verdict_color = "green"
    elif score >= 60:
        badge_class = "badge-medium"
        verdict_color = "orange"
    else:
        badge_class = "badge-low"
        verdict_color = "red"

    st.markdown("## 📊 Comprehensive ATS Evaluation Report")

    # Top Metric Banner
    top_c1, top_c2, top_c3, top_c4 = st.columns([1.2, 1, 1, 1.4])
    with top_c1:
        st.markdown(
            f"""
            <div class="metric-card" style="text-align: center;">
                <div style="font-size: 0.9rem; text-transform: uppercase; color: #94a3b8;">ATS Match Score</div>
                <div class="score-badge {badge_class}">{score}%</div>
                <div style="font-weight: 600; font-size: 1rem;">{ats.get('verdict', 'Evaluated')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    categories = ats.get("category_scores", {})
    with top_c2:
        st.metric("Keywords Match", f"{categories.get('keyword_match', 0)}%")
        st.metric("Skills Alignment", f"{categories.get('skills_alignment', 0)}%")
    with top_c3:
        st.metric("Experience Match", f"{categories.get('experience_relevance', 0)}%")
        st.metric("Quantified Impact", f"{categories.get('quantified_impact', 0)}%")
    with top_c4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div style="font-size: 0.85rem; color: #94a3b8; font-weight: 600; margin-bottom: 6px;">RECRUITER SUMMARY</div>
                <div style="font-size: 0.92rem; line-height: 1.4;">{ats.get('summary_verdict', 'No summary available.')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Detailed Tabs
    tab_overview, tab_keywords, tab_rewrites, tab_roadmap, tab_interview, tab_outreach, tab_structure = st.tabs(
        [
            "📈 ATS Scorecard",
            "🔍 Keyword Gap Analysis",
            "✍️ Bullet Point Optimizer",
            "🗺️ 30-60-90 Day Roadmap",
            "🎯 Tailored Interview Prep",
            "✉️ Cover Letter & Outreach",
            "📑 Structural Format Check",
        ]
    )

    # 1. OVERVIEW TAB
    with tab_overview:
        col_st, col_risk = st.columns(2, gap="large")
        with col_st:
            st.markdown("### 🌟 Key Candidate Strengths")
            for s in ats.get("top_strengths", []):
                st.markdown(f"- ✅ **{s}**")

            st.markdown("### ⚡ Quick Wins (Immediate Edits)")
            for qw in ats.get("quick_wins", []):
                st.markdown(f"- 🚀 **{qw}**")

        with col_risk:
            st.markdown("### ⚠️ ATS Risk Factors & Red Flags")
            risks = ats.get("ats_risk_factors", [])
            if risks:
                for r in risks:
                    st.markdown(f"- ⚠️ **{r}**")
            else:
                st.success("No critical ATS risk factors detected!")

            st.markdown("### 📊 Category Score Breakdown")
            for cat_name, cat_val in categories.items():
                label = cat_name.replace("_", " ").title()
                st.write(f"**{label}**: {cat_val}%")
                st.progress(cat_val / 100.0)

    # 2. KEYWORDS & SKILLS GAP
    with tab_keywords:
        st.markdown("### 🔑 Critical ATS Filter Keywords Missing")
        crit_keys = ats.get("critical_ats_keywords_missing", [])
        if crit_keys:
            crit_cols = st.columns(min(len(crit_keys), 3) or 1)
            for idx, k_info in enumerate(crit_keys):
                with crit_cols[idx % 3]:
                    st.error(
                        f"**{k_info.get('keyword', '')}**\n\n"
                        f"*Priority:* `{k_info.get('importance', 'High')}`\n\n"
                        f"{k_info.get('context_in_jd', '')}"
                    )
        else:
            st.success("No critical keyword omissions found!")

        col_hard, col_soft = st.columns(2, gap="medium")
        with col_hard:
            st.markdown("#### 🛠️ Hard Skills & Technologies")
            st.markdown("**Matched Skills:**")
            matched_hard = ats.get("matched_hard_skills", [])
            if matched_hard:
                html_pills = "".join([f'<span class="pill-matched">✓ {s}</span>' for s in matched_hard])
                st.markdown(html_pills, unsafe_allow_html=True)
            else:
                st.write("None detected.")

            st.markdown("<br>**Missing Skills:**", unsafe_allow_html=True)
            missing_hard = ats.get("missing_hard_skills", [])
            if missing_hard:
                html_pills = "".join([f'<span class="pill-missing">✕ {s}</span>' for s in missing_hard])
                st.markdown(html_pills, unsafe_allow_html=True)
            else:
                st.success("All primary hard skills matched!")

        with col_soft:
            st.markdown("#### 🤝 Soft Skills & Leadership")
            st.markdown("**Matched Competencies:**")
            matched_soft = ats.get("matched_soft_skills", [])
            if matched_soft:
                html_pills = "".join([f'<span class="pill-matched">✓ {s}</span>' for s in matched_soft])
                st.markdown(html_pills, unsafe_allow_html=True)
            else:
                st.write("None detected.")

            st.markdown("<br>**Missing Competencies:**", unsafe_allow_html=True)
            missing_soft = ats.get("missing_soft_skills", [])
            if missing_soft:
                html_pills = "".join([f'<span class="pill-missing">✕ {s}</span>' for s in missing_soft])
                st.markdown(html_pills, unsafe_allow_html=True)
            else:
                st.success("All primary soft skills matched!")

    # 3. BULLET POINT OPTIMIZER (XYZ / STAR)
    with tab_rewrites:
        rewrites = st.session_state.rewrite_results
        if rewrites:
            st.markdown("### 🏆 AI-Optimized Professional Summary")
            st.info(rewrites.get("tailored_summary", ""))

            st.markdown(f"**Recommended Target Headline:** `{rewrites.get('tailored_headline', '')}`")
            st.markdown("---")
            st.markdown("### ✍️ High-Impact Bullet Point Rewrites (Google XYZ Formula)")
            st.caption("Accomplished [X] as measured by [Y], by doing [Z] — tailored with target keywords.")

            for i, item in enumerate(rewrites.get("bullet_rewrites", [])):
                st.markdown(
                    f"""
                    <div class="rewrite-box">
                        <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">
                            EXAMPLE #{i+1} • IMPACT AREA: {item.get('impact_focus', 'General')}
                        </div>
                        <div class="rewrite-original">
                            <strong>Before (Original):</strong> {item.get('original', '')}
                        </div>
                        <div style="font-size: 0.82rem; color: #f59e0b; margin: 6px 0 6px 10px;">
                            <strong>Recruiter Critique:</strong> {item.get('critique', '')}
                        </div>
                        <div class="rewrite-improved">
                            <strong>After (Optimized with Metrics & Keywords):</strong><br>
                            {item.get('improved', '')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Run analysis to view bullet point optimizations.")

    # 4. UPSKILLING ROADMAP
    with tab_roadmap:
        roadmap = st.session_state.roadmap_results
        if roadmap:
            st.markdown("### 📈 Readiness & Upskilling Roadmap")
            st.write(roadmap.get("readiness_summary", ""))

            st.markdown("#### 🗓️ 30-60-90 Day Upskilling Plan")
            c30, c60, c90 = st.columns(3)
            with c30:
                st.markdown("##### 📍 First 30 Days (Foundations)")
                for g in roadmap.get("roadmap_30_60_90", {}).get("days_30", []):
                    st.markdown(f"- {g}")
            with c60:
                st.markdown("##### 📍 Next 60 Days (Core Projects)")
                for g in roadmap.get("roadmap_30_60_90", {}).get("days_60", []):
                    st.markdown(f"- {g}")
            with c90:
                st.markdown("##### 📍 90 Days (Interview Readiness)")
                for g in roadmap.get("roadmap_30_60_90", {}).get("days_90", []):
                    st.markdown(f"- {g}")

            st.markdown("---")
            st.markdown("#### 💡 Resume-Boosting Portfolio Project Ideas")
            for proj in roadmap.get("portfolio_project_ideas", []):
                with st.expander(f"🚀 {proj.get('title', 'Project')}", expanded=True):
                    st.write(proj.get("description", ""))
                    st.markdown(f"**Tech Stack:** `{', '.join(proj.get('tech_stack', []))}`")
                    st.markdown(f"**Demonstrates Competencies:** `{', '.join(proj.get('demonstrates_skills', []))}`")

    # 5. TAILORED INTERVIEW PREP
    with tab_interview:
        interview = st.session_state.interview_results
        if interview:
            col_tech, col_behav = st.columns(2, gap="medium")
            with col_tech:
                st.markdown("### 💻 Tailored Technical Questions")
                for idx, tq in enumerate(interview.get("technical_questions", [])):
                    with st.expander(f"Q{idx+1}: {tq.get('question', '')}", expanded=(idx == 0)):
                        st.caption(f"**Interviewer Focus:** {tq.get('interviewer_intent', '')}")
                        st.markdown("**Key Talking Points to Include:**")
                        for pt in tq.get("key_talking_points", []):
                            st.markdown(f"- {pt}")

            with col_behav:
                st.markdown("### 🗣️ Behavioral & Situational Questions (STAR)")
                for idx, bq in enumerate(interview.get("behavioral_questions", [])):
                    with st.expander(f"Q{idx+1}: {bq.get('question', '')}", expanded=(idx == 0)):
                        st.caption(f"**Competency Tested:** {bq.get('interviewer_intent', '')}")
                        guidance = bq.get("star_guidance", {})
                        st.markdown(
                            f"""
                            - **Situation / Task:** {guidance.get('situation_task', '')}
                            - **Action to Highlight:** {guidance.get('action', '')}
                            - **Measurable Result:** {guidance.get('result', '')}
                            """
                        )

    # 6. COVER LETTER & OUTREACH GENERATOR
    with tab_outreach:
        st.markdown("### ✉️ AI Cover Letter & LinkedIn Outreach")
        col_gen1, col_gen2 = st.columns(2)
        with col_gen1:
            cand_name = st.text_input("Candidate Name", value="Alex Chen")
        with col_gen2:
            target_company = st.text_input("Target Company Name", value="Hiring Team")

        if st.button("Generate Tailored Cover Letter & Outreach", type="secondary"):
            try:
                with st.spinner("Generating application materials with AI..."):
                    client = get_gemini_client(api_key)
                    st.session_state.outreach_results = generate_cover_letter_and_outreach(
                        client=client,
                        resume_text=st.session_state.resume_text,
                        job_description=st.session_state.job_description,
                        candidate_name=cand_name,
                        company_name=target_company,
                        model=selected_model,
                    )
                    st.rerun()
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")

        outreach = st.session_state.outreach_results
        if outreach:
            st.markdown("#### 📄 Cover Letter")
            st.text_area("Cover Letter Text", value=outreach.get("cover_letter", ""), height=250)

            st.markdown("#### 💼 LinkedIn / InMail Message")
            st.info(outreach.get("linkedin_outreach", ""))

            st.markdown("#### ⏱️ 5-Day Application Follow-up Email")
            fup = outreach.get("followup_email", {})
            st.write(f"**Subject:** `{fup.get('subject', '')}`")
            st.write(fup.get("body", ""))

    # 7. STRUCTURAL FORMAT CHECK
    with tab_structure:
        st.markdown("### 📑 ATS Parsing & Structural Health Check")
        struct = st.session_state.structure_results or analyze_resume_structure(st.session_state.resume_text)

        c_s1, c_s2 = st.columns(2)
        with c_s1:
            st.markdown(f"#### Format Score: `{struct['format_score']}/100`")
            st.progress(struct["format_score"] / 100.0)

            st.markdown("##### Detected Contact Details:")
            contacts = struct.get("contact_info", {})
            st.write(f"- **Email(s):** {', '.join(contacts.get('emails', [])) or '⚠️ None detected'}")
            st.write(f"- **Phone(s):** {', '.join(contacts.get('phones', [])) or '⚠️ None detected'}")
            st.write(f"- **LinkedIn:** {', '.join(contacts.get('linkedin', [])) or 'None detected'}")
            st.write(f"- **GitHub:** {', '.join(contacts.get('github', [])) or 'None detected'}")

        with c_s2:
            st.markdown("##### Standard Section Headers:")
            found_sec = struct.get("found_sections", [])
            missing_sec = struct.get("missing_sections", [])

            st.markdown("**Present Sections:**")
            st.markdown("".join([f'<span class="pill-section">✓ {s}</span>' for s in found_sec]), unsafe_allow_html=True)

            if missing_sec:
                st.markdown("<br>**Missing Standard Headers:**", unsafe_allow_html=True)
                st.markdown("".join([f'<span class="pill-missing">✕ {s}</span>' for s in missing_sec]), unsafe_allow_html=True)

        if struct.get("issues"):
            st.markdown("##### ⚠️ Structural ATS Warnings:")
            for iss in struct["issues"]:
                st.markdown(f"- {iss}")

    # --- DOWNLOAD REPORT BUTTON ---
    st.markdown("---")
    report_md = f"""# AI Resume ATS Evaluation Report

**Date:** {datetime.now().strftime("%B %d, %Y - %I:%M %p")}
**Target Job Match Score:** {score}% ({ats.get('verdict', 'Evaluated')})

## Recruiter Verdict
{ats.get('summary_verdict', '')}

## Category Breakdown
- Keyword Match: {categories.get('keyword_match', 0)}%
- Skills Alignment: {categories.get('skills_alignment', 0)}%
- Experience Relevance: {categories.get('experience_relevance', 0)}%
- Quantified Impact: {categories.get('quantified_impact', 0)}%

## Critical Missing Keywords
{chr(10).join([f"- **{k.get('keyword', '')}** ({k.get('importance', 'High')}): {k.get('context_in_jd', '')}" for k in ats.get('critical_ats_keywords_missing', [])])}

## Matched Hard Skills
{', '.join(ats.get('matched_hard_skills', []))}

## Missing Hard Skills
{', '.join(ats.get('missing_hard_skills', []))}

## Top Strengths
{chr(10).join([f"- {s}" for s in ats.get('top_strengths', [])])}

## Actionable Quick Wins
{chr(10).join([f"- {qw}" for qw in ats.get('quick_wins', [])])}
"""
    st.download_button(
        label="📥 Download Full ATS Evaluation Report (.md)",
        data=report_md,
        file_name="ATS_Resume_Evaluation_Report.md",
        mime="text/markdown",
        use_container_width=True,
    )
