import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "metrisure.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_name TEXT,
        image_filename TEXT,
        score INTEGER,
        status TEXT,
        ocr_confidence REAL,
        raw_text TEXT,
        fields_json TEXT,
        rule_results_json TEXT,
        preprocessing_json TEXT,
        created_at TEXT
    );
    """)
    conn.commit()
    conn.close()


def save_inspection(result: dict, image_filename: str):
    conn = get_conn()
    cur = conn.cursor()
    product_name = None
    if result["fields"].get("product_name", {}).get("value"):
        product_name = result["fields"]["product_name"]["value"]
    cur.execute(
        """INSERT INTO inspections
        (product_name, image_filename, score, status, ocr_confidence, raw_text,
         fields_json, rule_results_json, preprocessing_json, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            product_name or "Unidentified product",
            image_filename,
            result["score"],
            result["status"],
            result["ocr_avg_confidence"],
            result["raw_text"],
            json.dumps(result["fields"]),
            json.dumps(result["rule_results"]),
            json.dumps(result["preprocessing"]),
            datetime.utcnow().isoformat(),
        ),
    )
    conn.commit()
    inspection_id = cur.lastrowid
    conn.close()
    return inspection_id


def list_inspections():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, product_name, score, status, created_at FROM inspections ORDER BY id DESC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_inspection(inspection_id: int):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM inspections WHERE id = ?", (inspection_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    d["fields"] = json.loads(d.pop("fields_json"))
    d["rule_results"] = json.loads(d.pop("rule_results_json"))
    d["preprocessing"] = json.loads(d.pop("preprocessing_json"))
    return d


def dashboard_stats():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM inspections")
    total = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM inspections WHERE status='COMPLIANT'")
    compliant = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM inspections WHERE status='NON_COMPLIANT'")
    non_compliant = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM inspections WHERE status='REVIEW_REQUIRED'")
    review = cur.fetchone()["c"]
    cur.execute("SELECT id, product_name, score, status, created_at FROM inspections ORDER BY id DESC LIMIT 5")
    recent = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "total_scans": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "review_required": review,
        "recent_inspections": recent,
    }
