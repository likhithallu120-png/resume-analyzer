"""
Unit tests for Resume Analyzer components.
"""

from resume_parser import extract_text_from_pdf, analyze_resume_structure
from gemini_analyzer import _clean_json_response
from sample_data import SAMPLE_RESUMES, SAMPLE_JOB_DESCRIPTIONS

def test_json_cleaner():
    raw_markdown_json = '```json\n{"overall_match_score": 88, "verdict": "High Match"}\n```'
    parsed = _clean_json_response(raw_markdown_json)
    assert parsed["overall_match_score"] == 88
    assert parsed["verdict"] == "High Match"
    print("✓ _clean_json_response test passed")

def test_pdf_parsing():
    res = extract_text_from_pdf("sample_resumes/alex_chen_resume.pdf")
    assert res["success"] is True
    assert res["num_pages"] >= 1
    assert "Alex Chen" in res["cleaned_text"] or "ALEX CHEN" in res["cleaned_text"]
    print(f"✓ extract_text_from_pdf test passed ({res['num_pages']} pages)")

def test_structure_analysis():
    sample_text = SAMPLE_RESUMES["Full-Stack & AI Engineer"]
    analysis = analyze_resume_structure(sample_text, num_pages=1)
    assert analysis["format_score"] >= 80
    assert len(analysis["contact_info"]["emails"]) >= 1
    assert len(analysis["contact_info"]["phones"]) >= 1
    assert "Experience / Work History" in analysis["found_sections"]
    assert "Skills" in analysis["found_sections"]
    assert "Education" in analysis["found_sections"]
    print(f"✓ analyze_resume_structure test passed (Score: {analysis['format_score']})")

if __name__ == "__main__":
    test_json_cleaner()
    test_pdf_parsing()
    test_structure_analysis()
    print("All unit tests passed successfully!")
