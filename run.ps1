Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting AI Resume Analyzer & ATS Score Checker..." -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan

$pythonExe = "python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    $pythonExe = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
}

& $pythonExe -m streamlit run app.py
