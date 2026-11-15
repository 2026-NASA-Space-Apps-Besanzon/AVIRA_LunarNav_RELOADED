@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
if errorlevel 1 (echo Could not install Python dependencies & pause & exit /b 1)
python CAPTURE_NASA_DATA.py --date 2026-11-15 --days 2 --step-hours 2
if errorlevel 1 (echo NASA LIVE retrieval failed; DO NOT claim NASA data were captured. & pause & exit /b 1)
echo NASA evidence is inside NASA_EVIDENCE folder.
pause
