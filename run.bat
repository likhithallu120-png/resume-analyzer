@echo off
title AI Resume Analyzer & ATS Score Checker
echo ========================================================
echo Starting AI Resume Analyzer & ATS Score Checker...
echo ========================================================

REM Check if Python is in path or in AppData
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    python -m streamlit run app.py
) else (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m streamlit run app.py
)
pause
