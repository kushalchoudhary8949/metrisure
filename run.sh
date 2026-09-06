#!/usr/bin/env bash
# MetriSure — one-command launcher (Mac/Linux)
# Installs dependencies (first run only) and starts the app at http://localhost:8000
set -e
cd "$(dirname "$0")/backend"

if ! command -v tesseract >/dev/null 2>&1; then
  echo "Tesseract OCR is not installed."
  echo "  Ubuntu/Debian: sudo apt-get install -y tesseract-ocr"
  echo "  macOS (Homebrew): brew install tesseract"
  exit 1
fi

echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "Starting MetriSure at http://localhost:8000"
echo "Open that URL in your browser. Press Ctrl+C to stop."
echo ""
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
