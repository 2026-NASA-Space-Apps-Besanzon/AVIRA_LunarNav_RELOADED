@echo off
setlocal
cd /d "%~dp0"
py -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
py CAPTURE_NASA_DATA.py --date 2026-11-15 --days 2 --step-hours 2 --output NASA_EVIDENCE
if errorlevel 1 (
 echo NASA download failed. No scientific results were fabricated.
 pause
 exit /b 1
)
py BUILD_NASA_3D_RESULTS.py --evidence NASA_EVIDENCE
if errorlevel 1 exit /b 1
start "" "NASA_EVIDENCE\NASA_LIVE_3D_COMPARISON.html"
echo Raw JPL outputs and analytical CSV files are in NASA_EVIDENCE
pause
