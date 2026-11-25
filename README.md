# 🎯 AI Resume Analyzer & ATS Score Checker

A modern, full-featured Applicant Tracking System (ATS) optimization and resume analytics application powered by **Streamlit**, **Google Gemini API (`google-genai` SDK)**, and **pypdf**.

---

## ✨ Features

- **📄 Robust PDF Parsing (`pypdf`)**: Extracts raw text, page count, and metadata directly from uploaded PDF resumes without external binary dependencies.
- **📊 ATS Compatibility & Score Card (0–100%)**:
  - Overall ATS match score and recruiter verdict.
  - Granular breakdown: Keyword Match, Skills Alignment, Experience Relevance, and Quantified Impact.
- **🔍 Deep Keyword & Skills Gap Analysis**:
  - Highlights matched vs. missing **Hard Skills** (tools, frameworks, databases).
  - Highlights matched vs. missing **Soft Skills** (leadership, communication, agility).
  - Flags **Critical ATS Filter Keywords** present in the job description but absent from the candidate resume.
- **✍️ High-Impact Bullet Point Rewriter (Google XYZ Formula)**:
  - Critiques weak, vague, or unquantified bullet points.
  - Automatically rewrites them using the formula: *Accomplished [X] as measured by [Y], by doing [Z]*.
  - Generates an executive-ready, 3-sentence professional summary tailored to the target role.
- **🗺️ 30-60-90 Day Upskilling Roadmap**:
  - Strategic learning goals broken into 30, 60, and 90-day sprints.
  - Tailored portfolio project ideas with recommended tech stacks to bridge qualification gaps.
- **🎯 Tailored Interview Preparation**:
  - Generates 4 custom technical interview questions with key talking points to probe experience depth.
  - Generates 4 behavioral questions with situational STAR guidance.
- **✉️ Cover Letter & Outreach Generator**:
  - Full ATS-friendly cover letter.
  - High-converting LinkedIn / InMail outreach message.
  - 5-day post-application follow-up email.
- **📑 Structural Formatting Health Check**:
  - Verifies contact details (Email, Phone, LinkedIn, GitHub).
  - Checks for standard ATS section headers (Experience, Education, Skills, Summary, Projects).
  - Detects potential red flags (unreadable scanned PDFs, word count anomalies, excessive page length).
- **📥 One-Click Export**:
  - Download the complete ATS report as a formatted Markdown (`.md`) file.
- **⚡ 1-Click Demo Profiles**:
  - Preloaded with sample resumes and job descriptions for instant testing without needing an initial upload.

---

## 📁 Project Structure

```
resume_analyzer/
├── app.py                   # Main Streamlit web application
├── gemini_analyzer.py       # Google Gemini API integration (google-genai SDK)
├── resume_parser.py         # PDF text extraction and ATS structural heuristics (pypdf)
├── sample_data.py           # Pre-configured demo resumes and job descriptions
├── generate_sample_pdf.py   # Script to generate sample PDF resume
├── sample_resumes/          # Generated sample PDF files
├── requirements.txt         # Python dependencies
├── .env.example             # Template for API credentials
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- A Google Gemini API Key ([Get a free key at Google AI Studio](https://aistudio.google.com/app/apikey))

### 2. Installation

Clone or navigate to the project directory:
```bash
cd resume_analyzer
```

Create a virtual environment (optional but recommended):
```bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure Gemini API Key

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` and set:
```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
The application automatically and securely loads the API key from your environment upon startup without exposing it in the browser UI.

### 4. Run the Streamlit App

```bash
streamlit run app.py
```
*(On Windows, you can also simply run `.\run.ps1` or double-click `run.bat`).*

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🧪 Testing the Application

1. **Option A: 1-Click Demo**:
   - In the sidebar under **⚡ 1-Click Demo Profiles**, select a demo role (e.g. `Full-Stack & AI Engineer`) and click **Load Demo**.
   - Click the primary **⚡ Analyze Resume against Job Description** button.

2. **Option B: Upload your own PDF**:
   - Upload any `.pdf` resume using the **Upload PDF (pypdf)** tab.
   - Paste a target job description or choose a standard template role.
   - Click **⚡ Analyze Resume against Job Description**.

---

## 🧠 Technologies Used

- **[Streamlit](https://streamlit.io/)**: Modern interactive dashboard interface.
- **[Google GenAI SDK (`google-genai`)](https://github.com/google-gemini/generative-ai-python)**: The official Google Gemini SDK for model inference and structured output.
- **[pypdf](https://pypdf.readthedocs.io/)**: Pure Python PDF parsing and structural analysis.
- **[python-dotenv](https://github.com/theskumar/python-dotenv)**: Environment variable management.
