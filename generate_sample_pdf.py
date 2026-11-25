"""
Generates valid sample PDF resumes for testing pypdf text extraction.
"""

import os

def create_simple_pdf(filename: str, title: str, lines: list):
    """
    Creates a standard valid PDF file with raw text streams without external heavy dependencies.
    """
    stream_content = "BT\n/F1 10 Tf\n50 750 Td\n14 TL\n"
    stream_content += f"/F1 16 Tf ({title}) Tj\n/F1 10 Tf\nT*\nT*\n"
    for line in lines:
        escaped_line = (
            line.replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )
        stream_content += f"({escaped_line}) Tj T*\n"
    stream_content += "ET\n"

    stream_bytes = stream_content.encode("latin-1", "replace")
    stream_len = len(stream_bytes)

    objects = []
    # 1: Catalog
    objects.append("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages
    objects.append("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    # 3: Page
    objects.append("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
    # 4: Contents
    objects.append(f"4 0 obj\n<< /Length {stream_len} >>\nstream\n{stream_content}endstream\nendobj\n")
    # 5: Font
    objects.append("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    pdf_body = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(pdf_body.encode("latin-1")))
        pdf_body += obj

    xref_offset = len(pdf_body.encode("latin-1"))
    pdf_body += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n"
    for off in offsets[1:]:
        pdf_body += f"{off:010d} 00000 n \n"

    pdf_body += f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"

    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(pdf_body.encode("latin-1"))
    print(f"Generated sample PDF: {filename}")

if __name__ == "__main__":
    lines = [
        "San Francisco, CA | alex.chen@email.com | (555) 234-5678",
        "LinkedIn: linkedin.com/in/alexchen-dev | GitHub: github.com/alexchen-code",
        "",
        "PROFESSIONAL SUMMARY",
        "Full Stack Software Engineer with 4+ years of experience designing scalable microservices,",
        "distributed systems, and AI-enabled web applications. Proficient in Python, TypeScript,",
        "React, FastAPI, Docker, and PostgreSQL. Reduced search latency by 42%.",
        "",
        "CORE SKILLS",
        "Languages: Python, TypeScript, JavaScript, SQL, Go",
        "Frameworks: React, Next.js, FastAPI, Flask, Node.js, PyTorch",
        "Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, CI/CD, Redis, PostgreSQL",
        "AI: Gemini API, LangChain, RAG Pipelines, Vector DBs, Prompt Engineering",
        "",
        "PROFESSIONAL EXPERIENCE",
        "Senior Full Stack Engineer | Apex Cloud Solutions (2022 - Present)",
        "- Architected AI search system with FastAPI and Vector DBs, reducing latency by 42%.",
        "- Led migration from Node.js monolith to Python Docker microservices serving 10k req/sec.",
        "- Optimized PostgreSQL queries and Redis caching, cutting CPU utilization by 28%.",
        "",
        "Software Engineer | NexaTech Systems (2020 - 2022)",
        "- Developed RESTful APIs in Python (FastAPI/Django) and Stripe payments ($3.5M volume).",
        "- Built interactive management dashboards with React and Redux.",
        "",
        "EDUCATION",
        "Bachelor of Science in Computer Science | University of Texas at Austin (GPA: 3.82)",
        "",
        "CERTIFICATIONS",
        "- AWS Certified Solutions Architect (2023)",
    ]
    out_path = os.path.join(os.path.dirname(__file__), "sample_resumes", "alex_chen_resume.pdf")
    create_simple_pdf(out_path, "ALEX CHEN - RESUME", lines)
