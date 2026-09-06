import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response

import db
import pipeline
import report
from rules import get_active_rules

app = FastAPI(title="MetriSure API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "MetriSure API"}


@app.get("/api/dashboard")
def dashboard():
    return db.dashboard_stats()


@app.post("/api/analyze")
async def analyze(file: UploadFile = File(...)):
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        result = pipeline.run_pipeline(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not process image: {e}")

    safe_name = file.filename or "upload.jpg"
    save_path = os.path.join(UPLOAD_DIR, f"{safe_name}")
    try:
        with open(save_path, "wb") as f:
            f.write(image_bytes)
    except Exception:
        pass

    inspection_id = db.save_inspection(result, safe_name)
    result["inspection_id"] = inspection_id
    return result


@app.get("/api/rules")
def rules():
    return {"rules": get_active_rules()}


@app.get("/api/inspections")
def inspections():
    return {"inspections": db.list_inspections()}


@app.get("/api/inspections/{inspection_id}")
def inspection_detail(inspection_id: int):
    insp = db.get_inspection(inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    return insp


@app.get("/api/reports/{inspection_id}")
def get_report(inspection_id: int):
    insp = db.get_inspection(inspection_id)
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")
    insp["ocr_confidence"] = insp.get("ocr_confidence")
    pdf_bytes = report.build_report_pdf(insp)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=inspection_{inspection_id}_report.pdf"},
    )


# Serve the frontend SPA (mounted last so it doesn't shadow /api routes)
FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
