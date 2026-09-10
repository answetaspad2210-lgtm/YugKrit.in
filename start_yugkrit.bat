@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>&1 || (
    echo Python is not installed or is not on PATH.
    pause
    exit /b 1
)
python -c "import sqlite3, sys; c=sqlite3.connect('yugkrit.db'); sys.exit(0 if c.execute(\"SELECT 1 FROM sqlite_master WHERE type='table' AND name='challenges'\").fetchone() else 1)"
if errorlevel 1 (
    echo Preparing the demo database...
    python database\seed.py || exit /b 1
)
set FLASK_HTTPS=1
start "YugKrit Flask" cmd /k "python app.py"
timeout /t 2 /nobreak >nul
start "" https://127.0.0.1:5000/
