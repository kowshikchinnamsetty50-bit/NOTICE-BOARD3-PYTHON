# PowerShell Launcher for Notice Board Organizer
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Starting CampusPulse: Notice Board Organizer" -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

$pythonCandidates = @(
    "streamlit",
    "python",
    "py",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python314\python.exe",
    "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python314\Scripts\streamlit.exe"
)

if (Get-Command streamlit -ErrorAction SilentlyContinue) {
    streamlit run app.py
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    python -m streamlit run app.py
} elseif (Test-Path "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python314\python.exe") {
    & "C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run app.py
} else {
    Write-Host "Could not automatically locate Python. Please run: python -m streamlit run app.py" -ForegroundColor Red
}
