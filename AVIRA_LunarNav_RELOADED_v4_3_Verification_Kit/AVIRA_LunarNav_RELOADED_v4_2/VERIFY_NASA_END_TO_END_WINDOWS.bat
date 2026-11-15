@echo off
setlocal
cd /d "%~dp0"
if not exist NASA_EVIDENCE mkdir NASA_EVIDENCE
set LOG=NASA_EVIDENCE\WINDOWS_VERIFICATION_LOG.txt
(
 echo AVIRA LunarNav NASA End-to-End Verification
 echo Run date: %DATE% %TIME%
 echo ==================================================
 echo [1] Python version
 python --version
 echo [2] Install dependencies
 python -m pip install -r requirements.txt
 echo [3] Automated tests
 python -m pytest -q
 echo [4] Live NASA/JPL Horizons capture (NO SYNTHETIC FALLBACK)
 python CAPTURE_NASA_DATA.py --date 2026-11-15 --days 2 --step-hours 2 --output NASA_EVIDENCE
 if errorlevel 1 (
  echo NASA_CAPTURE_FAILED: Do NOT present synthetic results as NASA data.
 ) else (
  echo [5] Generate NASA-driven 3D interactive scene
  python BUILD_NASA_3D_RESULTS.py --evidence NASA_EVIDENCE --output NASA_EVIDENCE\NASA_LIVE_3D_COMPARISON.html
  if errorlevel 1 echo NASA_3D_BUILD_FAILED
 )
 echo [6] Finished. Inspect the NASA_EVIDENCE folder and the log.
) > "%LOG%" 2>&1
type "%LOG%"
echo.
echo Output folder: %CD%\NASA_EVIDENCE
pause
