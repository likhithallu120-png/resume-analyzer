"""
Resume Parser Module
Extracts and performs structural analysis on resume documents using pypdf.
"""

import io
import re
from typing import Dict, Any, List, Optional
import pypdf


def extract_text_from_pdf(file_input: Any) -> Dict[str, Any]:
    """
    Extracts text and metadata from a PDF file using pypdf.
    Accepts Streamlit UploadedFile, file-like object, bytes, or file path.
    """
    try:
        if hasattr(file_input, "seek"):
            file_input.seek(0)

        if isinstance(file_input, bytes):
            reader = pypdf.PdfReader(io.BytesIO(file_input))
        elif hasattr(file_input, "read"):
            # Streamlit UploadedFile or file-like object
            reader = pypdf.PdfReader(file_input)
        else:
            # File path string
            reader = pypdf.PdfReader(str(file_input))

        num_pages = len(reader.pages)
        page_texts = []
        raw_text_parts = []

        for idx, page in enumerate(reader.pages):
            extracted = page.extract_text() or ""
            page_texts.append(extracted)
            raw_text_parts.append(f"--- Page {idx + 1} ---\n{extracted}")

        full_text = "\n\n".join(raw_text_parts).strip()
        cleaned_text = "\n\n".join(page_texts).strip()

        # Extract basic PDF metadata if available
        meta = reader.metadata or {}
        metadata = {
            "title": str(meta.get("/Title", "") or ""),
            "author": str(meta.get("/Author", "") or ""),
            "creator": str(meta.get("/Creator", "") or ""),
            "producer": str(meta.get("/Producer", "") or ""),
        }

        is_scanned = len(cleaned_text.replace(" ", "").replace("\n", "")) < 50

        return {
            "success": True,
            "full_text": full_text,
            "cleaned_text": cleaned_text,
            "num_pages": num_pages,
            "metadata": metadata,
            "is_scanned": is_scanned,
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "full_text": "",
            "cleaned_text": "",
            "num_pages": 0,
            "metadata": {},
            "is_scanned": False,
            "error": str(e),
        }


def analyze_resume_structure(text: str, num_pages: int = 1) -> Dict[str, Any]:
    """
    Performs heuristic ATS checks on resume structure, formatting, and sections.
    """
    # Contact Info Regex
    email_regex = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    phone_regex = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    linkedin_regex = r"linkedin\.com/in/[a-zA-Z0-9_-]+"
    github_regex = r"github\.com/[a-zA-Z0-9_-]+"

    emails = list(set(re.findall(email_regex, text, re.IGNORECASE)))
    phones = list(set(re.findall(phone_regex, text)))
    linkedin = list(set(re.findall(linkedin_regex, text, re.IGNORECASE)))
    github = list(set(re.findall(github_regex, text, re.IGNORECASE)))

    # Standard Section Checks
    sections_patterns = {
        "Summary / Profile": r"(?i)\b(summary|professional\s+summary|about\s+me|profile|objective)\b",
        "Experience / Work History": r"(?i)\b(experience|work\s+experience|employment\s+history|professional\s+experience)\b",
        "Education": r"(?i)\b(education|academic\s+background|degrees|qualifications)\b",
        "Skills": r"(?i)\b(skills|technical\s+skills|core\s+competencies|technologies)\b",
        "Projects": r"(?i)\b(projects|personal\s+projects|key\s+projects|portfolio)\b",
        "Certifications / Awards": r"(?i)\b(certifications|certificates|licenses|honors|awards)\b",
    }

    found_sections = {}
    missing_sections = []
    for section_name, pattern in sections_patterns.items():
        match = re.search(pattern, text)
        if match:
            found_sections[section_name] = True
        else:
            missing_sections.append(section_name)

    # Word count and readability
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)
    estimated_read_time_min = round(word_count / 200, 1)

    # Bullet points heuristic
    bullet_matches = re.findall(r"(?:^|\n)\s*[-•*▪–—]\s+", text)
    bullet_count = len(bullet_matches)

    # ATS Formatting Score Heuristics (out of 100)
    score_components = []
    score = 100

    if not emails:
        score -= 15
        score_components.append("Missing or unreadable email address (-15)")
    if not phones:
        score -= 10
        score_components.append("Missing or unreadable phone number (-10)")
    if "Experience / Work History" in missing_sections:
        score -= 25
        score_components.append("Missing standard Experience section header (-25)")
    if "Skills" in missing_sections:
        score -= 20
        score_components.append("Missing Skills section header (-20)")
    if "Education" in missing_sections:
        score -= 15
        score_components.append("Missing Education section header (-15)")
    if word_count < 150:
        score -= 25
        score_components.append("Word count is under 150 words — resume appears too brief (-25)")
    elif word_count > 1200:
        score -= 10
        score_components.append("Word count is over 1200 words — consider condensing (-10)")

    if num_pages > 2:
        score -= 10
        score_components.append("Resume exceeds 2 pages; 1-2 pages is optimal for ATS (-10)")

    score = max(10, min(100, score))

    return {
        "format_score": score,
        "word_count": word_count,
        "estimated_read_time_min": estimated_read_time_min,
        "bullet_count": bullet_count,
        "contact_info": {
            "emails": emails,
            "phones": phones,
            "linkedin": [f"https://{url}" for url in linkedin],
            "github": [f"https://{url}" for url in github],
        },
        "found_sections": list(found_sections.keys()),
        "missing_sections": missing_sections,
        "issues": score_components,
    }
