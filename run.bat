@echo off
REM MetriSure -- one-command launcher (Windows)
cd /d "%~dp0backend"

where tesseract >nul 2>nul
if %errorlevel% neq 0 (
    echo Tesseract OCR was not found on PATH.
    echo Download and install it from: https://github.com/UB-Mannheim/tesseract/wiki
    echo Then re-run this script.
    pause
    exit /b 1
)

echo Installing Python dependencies...
pip install -r requirements.txt --quiet

echo.
echo Starting MetriSure at http://localhost:8000
echo Open that URL in your browser. Press Ctrl+C to stop.
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000
