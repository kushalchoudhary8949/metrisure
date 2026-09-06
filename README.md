# MetriSure — Legal Metrology Compliance Platform (SIH26034)

A working prototype: React frontend + FastAPI backend + real OpenCV/Tesseract OCR +
a deterministic, versioned rule engine + SQLite + PDF report generation.

## Run it (1 command)

**Prerequisites:** Python 3.9+, and Tesseract OCR installed.
- Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: install from https://github.com/UB-Mannheim/tesseract/wiki

**Mac/Linux:**
```
./run.sh
```

**Windows:**
```
run.bat
```

Then open **http://localhost:8000** in your browser. That's it — one process serves
both the frontend and the API, so there's nothing else to configure.

## Presenting in 15 minutes

1. Open http://localhost:8000 — starts on the **Dashboard**.
2. Go to **Scan product**. Under "Try a demo scenario", click **Compliant label** →
   Run compliance check → shows the live OCR pipeline animate → **100% COMPLIANT**.
3. Go back, click **Missing declarations** → Run → **57% NON-COMPLIANT**, with the
   exact 3 missing fields (country of origin, consumer care, unit price) called out.
4. Go back, click **Low-confidence photo** → Run → **78% REVIEW REQUIRED**, showing
   the human-in-the-loop path with clear "officer must verify" explanations.
5. Open **Rule engine** — show the judges that legal logic is versioned and stored
   separately from the OCR/AI pipeline.
6. Open **Inspection history** — full audit trail.
7. Back on any result, click **Download report** for the PDF.

You can also drag in your own package photo instead of the demo images.

## What's real vs. what's a placeholder

- Real: OpenCV preprocessing, Tesseract OCR, regex-based field extraction, the rule
  engine, SQLite persistence, PDF report generation. Everything in the demo actually runs.
- Simplified for a prototype: SQLite instead of PostgreSQL; regex extraction instead of
  an LLM-based normalizer; the 8 rules are demonstration rules loosely modelled on the
  Legal Metrology (Packaged Commodities) Rules — for production use, populate `backend/rules.py`
  from the official Department of Consumer Affairs notifications (this is called out on
  screen in the app and in `backend/rules.py`).

## Project structure

```
metrisure/
  backend/
    main.py        FastAPI app & routes
    pipeline.py     OpenCV -> OCR -> field extraction -> rule evaluation
    rules.py        Versioned rule definitions
    db.py           SQLite persistence
    report.py       PDF report generation (ReportLab)
    requirements.txt
  frontend/
    index.html      Full React SPA (Dashboard / Scan / Result / History / Rules)
    demo/           Copies of the 3 demo images for one-click loading in the UI
  seed_images/
    generate_demo_labels.py   Regenerates the 3 demo label images if needed
  run.sh / run.bat
```

## Troubleshooting

- **"Tesseract not found"** — install it (see Prerequisites) and make sure it's on PATH.
- **Port 8000 already in use** — edit the port in `run.sh`/`run.bat` and the `API_BASE`
  will still work since the frontend calls `window.location.origin`.
- **Scores look off on your own photos** — the regex field extraction is tuned for
  clear, roughly-horizontal label text; very unusual layouts may need pattern tweaks in
  `backend/pipeline.py`.
