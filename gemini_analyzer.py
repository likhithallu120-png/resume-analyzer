"""
Gemini AI Resume Analyzer Engine
Uses the official Google GenAI SDK (google-genai) to perform ATS scoring,
gap analysis, bullet point rewrites, cover letter generation, and interview preparation.
"""

import os
import json
import re
from typing import Dict, Any, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


def get_gemini_client(api_key: Optional[str] = None) -> Any:
    """
    Initializes and returns a google-genai Client.
    Prioritizes passed api_key, falls back to GEMINI_API_KEY environment variable.
    """
    if genai is None:
        raise ImportError(
            "The 'google-genai' package is not installed. Run 'pip install google-genai'."
        )

    resolved_key = (api_key or "").strip() or os.environ.get("GEMINI_API_KEY", "").strip()
    if not resolved_key:
        raise ValueError(
            "Gemini API key is required. Please enter your API key in the sidebar or set GEMINI_API_KEY."
        )

    return genai.Client(api_key=resolved_key)


def _clean_json_response(raw_text: str) -> Dict[str, Any]:
    """
    Cleans markdown formatting and parses JSON safely.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"```$", "", cleaned, flags=re.MULTILINE).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to locate the outermost JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        raise ValueError(f"Could not parse response into structured JSON:\n{raw_text[:500]}")


def _generate_with_fallback(client: Any, requested_model: str, contents: Any, config: Any) -> Any:
    """
    Generates content using the requested model, with automatic fallback to high-availability
    models if experiencing spikes in demand (503), rate limits (429), or model deprecation (404).
    """
    candidate_models = [requested_model]
    for backup in ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.1-flash-lite"]:
        if backup not in candidate_models:
            candidate_models.append(backup)

    last_error = None
    for model_name in candidate_models:
        try:
            return client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
        except Exception as e:
            last_error = e
            err_str = str(e).lower()
            if any(keyword in err_str for keyword in ["503", "429", "404", "unavailable", "high demand", "resource_exhausted", "not_found"]):
                continue
            raise e
    raise last_error


def analyze_ats_fit(
    client: Any,
    resume_text: str,
    job_description: str,
    model: str = "gemini-3.5-flash",
) -> Dict[str, Any]:
    """
    Evaluates ATS score match, missing keywords, hard/soft skill breakdown, and risk factors.
    Returns structured dictionary.
    """
    system_instruction = (
        "You are an executive ATS (Applicant Tracking System) specialist, Senior Technical Recruiter, "
        "and Hiring Manager. Analyze the provided candidate resume against the target job description. "
        "Be rigorous, realistic, and highly constructive. You must return your evaluation strictly in valid JSON format."
    )

    prompt = f"""
TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME TEXT:
{resume_text}

Perform a rigorous ATS evaluation and return ONLY a single valid JSON object with the following schema:
{{
  "overall_match_score": <integer between 0 and 100>,
  "verdict": "<High Match (80-100%) | Moderate Match (60-79%) | Low Match (<60%)>",
  "summary_verdict": "<2-3 sentence executive recruiter verdict>",
  "category_scores": {{
    "keyword_match": <integer 0-100>,
    "skills_alignment": <integer 0-100>,
    "experience_relevance": <integer 0-100>,
    "education_credentials": <integer 0-100>,
    "quantified_impact": <integer 0-100>
  }},
  "matched_hard_skills": ["<skill1>", "<skill2>"],
  "missing_hard_skills": ["<skill1>", "<skill2>"],
  "matched_soft_skills": ["<skill1>", "<skill2>"],
  "missing_soft_skills": ["<skill1>", "<skill2>"],
  "critical_ats_keywords_missing": [
    {{
      "keyword": "<keyword or technology>",
      "importance": "<High | Critical | Medium>",
      "context_in_jd": "<where or why it matters in JD>"
    }}
  ],
  "top_strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "ats_risk_factors": ["<risk or red flag 1>", "<risk 2>"],
  "quick_wins": ["<immediate high-impact tweak 1>", "<tweak 2>", "<tweak 3>"]
}}
"""

    config = (
        types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2,
            response_mime_type="application/json",
        )
        if types
        else None
    )

    response = _generate_with_fallback(client, model, prompt, config)
    return _clean_json_response(response.text)


def rewrite_bullet_points(
    client: Any,
    resume_text: str,
    job_description: str,
    model: str = "gemini-3.5-flash",
) -> Dict[str, Any]:
    """
    Identifies weak or unquantified resume bullet points and rewrites them using
    the Google XYZ (Accomplished [X] as measured by [Y], by doing [Z]) and STAR frameworks.
    """
    system_instruction = (
        "You are an elite career coach and resume writer. Transform passive, generic resume bullet points "
        "into impactful, quantifiable, metric-driven achievements tailored specifically to the target role. "
        "Return strictly valid JSON."
    )

    prompt = f"""
TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME TEXT:
{resume_text}

Identify 4-5 weak, vague, or under-quantified bullet points from the resume. Rewrite each using strong action verbs,
the XYZ formula (Accomplished [X] as measured by [Y], by doing [Z]), and relevant keywords from the job description.
Also provide an optimized, punchy 3-line Professional Summary tailored to this exact role.

Return ONLY a valid JSON object matching:
{{
  "tailored_summary": "<compelling, keyword-rich 3-4 sentence professional summary>",
  "bullet_rewrites": [
    {{
      "original": "<original weak line from resume>",
      "critique": "<why it was weak: e.g. lacks metrics, passive tone, missing tool>",
      "improved": "<rewritten bullet with metrics, active verb, and target keyword>",
      "impact_focus": "<e.g., Efficiency / Revenue / Scalability / Leadership>"
    }}
  ],
  "tailored_headline": "<modern LinkedIn / Resume title header tailored to this job>"
}}
"""

    config = (
        types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json",
        )
        if types
        else None
    )

    response = _generate_with_fallback(client, model, prompt, config)
    return _clean_json_response(response.text)


def generate_skill_roadmap(
    client: Any,
    resume_text: str,
    job_description: str,
    model: str = "gemini-3.5-flash",
) -> Dict[str, Any]:
    """
    Analyzes qualification gaps and generates a prioritized learning roadmap and portfolio project ideas.
    """
    system_instruction = (
        "You are a Senior Engineering Director and Career Mentor. Generate an actionable, step-by-step "
        "upskilling roadmap and hands-on portfolio projects to bridge gaps between candidate resume and target role. "
        "Return strictly valid JSON."
    )

    prompt = f"""
TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME TEXT:
{resume_text}

Compare the candidate's current capabilities with the job description. Formulate a 30-60-90 day upskilling roadmap
and 2 portfolio project ideas that would prove competence in missing skills.

Return ONLY a valid JSON object:
{{
  "readiness_summary": "<brief overview of current candidate readiness for this role>",
  "priority_skills_to_learn": [
    {{
      "skill": "<skill name>",
      "why_needed": "<explanation of requirement>",
      "estimated_learning_hours": <number>,
      "recommended_resources": ["<course or doc 1>", "<cert or tutorial 2>"]
    }}
  ],
  "roadmap_30_60_90": {{
    "days_30": ["<core foundation goal 1>", "<goal 2>"],
    "days_60": ["<intermediate project / tool goal 1>", "<goal 2>"],
    "days_90": ["<advanced integration / interview readiness goal 1>", "<goal 2>"]
  }},
  "portfolio_project_ideas": [
    {{
      "title": "<Project Title>",
      "description": "<What to build and why it impresses recruiters>",
      "tech_stack": ["<Tech 1>", "<Tech 2>", "<Tech 3>"],
      "demonstrates_skills": ["<Skill 1>", "<Skill 2>"]
    }}
  ]
}}
"""

    config = (
        types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json",
        )
        if types
        else None
    )

    response = _generate_with_fallback(client, model, prompt, config)
    return _clean_json_response(response.text)


def generate_cover_letter_and_outreach(
    client: Any,
    resume_text: str,
    job_description: str,
    candidate_name: str = "Applicant",
    company_name: str = "Hiring Team",
    model: str = "gemini-3.5-flash",
) -> Dict[str, Any]:
    """
    Generates a tailored ATS-friendly cover letter and a concise LinkedIn / cold outreach message.
    """
    system_instruction = (
        "You are an executive communications expert and professional resume copywriter. "
        "Draft tailored, authentic, high-impact job application materials that avoid corporate clichés. "
        "Return strictly valid JSON."
    )

    prompt = f"""
CANDIDATE NAME: {candidate_name}
TARGET COMPANY: {company_name}

TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Draft:
1. A tailored, high-converting Cover Letter (around 250-350 words, structured: Hook, Core Value & Metrics, Cultural / Mission Fit, Call to Action).
2. A concise LinkedIn Connection / Recruiter InMail message (under 100 words).
3. A Follow-up Email (sent 5 days after applying).

Return ONLY valid JSON:
{{
  "cover_letter": "<full text of cover letter with markdown formatting>",
  "linkedin_outreach": "<concise outreach message>",
  "followup_email": {{
    "subject": "<compelling subject line>",
    "body": "<concise polite follow-up message>"
  }}
}}
"""

    config = (
        types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.4,
            response_mime_type="application/json",
        )
        if types
        else None
    )

    response = _generate_with_fallback(client, model, prompt, config)
    return _clean_json_response(response.text)


def generate_interview_prep(
    client: Any,
    resume_text: str,
    job_description: str,
    model: str = "gemini-3.5-flash",
) -> Dict[str, Any]:
    """
    Generates tailored technical and behavioral interview questions and suggested answers
    based on the resume's specific experience and the role's requirements.
    """
    system_instruction = (
        "You are a Bar Raiser and Principal Hiring Manager. Prepare the candidate for interviews "
        "by targeting both their core strengths and their potential vulnerability areas from the resume. "
        "Return strictly valid JSON."
    )

    prompt = f"""
TARGET JOB DESCRIPTION:
{job_description}

CANDIDATE RESUME:
{resume_text}

Generate 4 technical interview questions and 4 behavioral/situational questions specifically tailored to this candidate's background and this role.
For each question, provide what the interviewer is evaluating and a high-scoring sample talking point or response outline.

Return ONLY valid JSON:
{{
  "technical_questions": [
    {{
      "question": "<technical question>",
      "interviewer_intent": "<what skill or depth this probes>",
      "key_talking_points": ["<talking point 1>", "<talking point 2>"]
    }}
  ],
  "behavioral_questions": [
    {{
      "question": "<behavioral question (STAR)>",
      "interviewer_intent": "<what trait or competency this probes>",
      "star_guidance": {{
        "situation_task": "<recommended story from candidate resume>",
        "action": "<what action should be highlighted>",
        "result": "<what quantifiable metric should be emphasized>"
      }}
    }}
  ]
}}
"""

    config = (
        types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            response_mime_type="application/json",
        )
        if types
        else None
    )

    response = _generate_with_fallback(client, model, prompt, config)
    return _clean_json_response(response.text)
