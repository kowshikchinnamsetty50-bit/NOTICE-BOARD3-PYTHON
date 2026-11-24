@echo off
echo ========================================================
echo   Starting CampusPulse: Notice Board Organizer
echo ========================================================
echo.

REM Try direct streamlit command first, then python -m streamlit
where streamlit >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    streamlit run app.py
) else (
    echo 'streamlit' not found directly in PATH. Attempting Python module execution...
    py -m streamlit run app.py 2>nul || python -m streamlit run app.py 2>nul || "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python314\python.exe" -m streamlit run app.py
)

pause
