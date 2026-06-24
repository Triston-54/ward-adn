@echo off
setlocal EnableExtensions DisableDelayedExpansion

title The Ward — ADN Nursing Study Suite
color 0A
cd /d "%~dp0"

echo.
echo  ========================================================
echo    THE WARD — ADN Nursing Study Suite
echo    New River Community and Technical College
echo  ========================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  [ERROR] Python was not found.
    echo.
    echo  Install Python 3.10 or newer from https://www.python.org/downloads/
    echo  During setup, check "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%V in ('python --version 2^>^&1') do set "PYVER=%%V"
echo  [OK] Python %PYVER%

REM --- Check build dependency (Jinja2) ---
echo  [..] Checking build dependencies...
python -c "import jinja2" >nul 2>&1
if errorlevel 1 (
    color 0E
    echo  [WARN] Jinja2 is not installed.
    echo.
    echo  Installing from requirements-build.txt...
    echo.
    python -m pip install -r requirements-build.txt
    if errorlevel 1 (
        color 0C
        echo.
        echo  [ERROR] Could not install build dependencies.
        echo  Try manually:  pip install -r requirements-build.txt
        echo.
        pause
        exit /b 1
    )
    echo.
    echo  [OK] Build dependencies installed.
) else (
    echo  [OK] Build dependencies ready.
)

REM --- Build static HTML (always — keeps pages in sync with templates) ---
echo.
echo  [..] Building static site...
python scripts/build_static_html.py
if errorlevel 1 (
    color 0C
    echo.
    echo  [ERROR] Static build failed. See messages above.
    echo.
    pause
    exit /b 1
)
echo  [OK] Static site built.

echo.
echo  Starting local server at http://127.0.0.1:8000
echo  Your browser will open automatically when ready.
echo  Keep this window open while you study. Press Ctrl+C to stop.
echo.

REM Wait for the server, then open the browser
start /b "" powershell -NoProfile -WindowStyle Hidden -Command "$u='http://127.0.0.1:8000/';1..30|%%{try{iwr $u -UseBasicParsing -TimeoutSec 2|Out-Null;start $u;break}catch{sleep 1}}"

python -m http.server 8000
set "EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%EXIT_CODE%"=="0" (
    color 0C
    echo  [ERROR] The Ward stopped unexpectedly (exit code %EXIT_CODE%).
) else (
    echo  The Ward has stopped. Goodbye!
)
echo.
pause
exit /b %EXIT_CODE%