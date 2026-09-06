"""
MetriSure pipeline: image -> OpenCV preprocessing -> OCR -> field extraction
-> deterministic rule engine -> compliance result.

Design principle (per project brief): OCR/heuristics only EXTRACT information.
The rule engine, not any model, DECIDES compliance.
"""
import re
import cv2
import numpy as np
import pytesseract
from rules import get_active_rules, SEVERITY_WEIGHT, REVIEW_THRESHOLD

FIELD_PATTERNS = {
    "net_quantity": r"(net\s?(qty|quantity|weight|wt)\.?\s*[:\-]?\s*)?(\d+(\.\d+)?\s?(g|kg|ml|l|litre|liter|gm|gram|kilogram)\b)",
    "mrp": r"(mrp[:\-]?\s*)?(rs\.?|inr|₹)\s?\d+(\.\d{1,2})?",
    "manufacturing_date": r"(mfg|mfd|manufactured|packed|pkd)[.:\s]*(date)?[:\-\s]*((\d{1,2}[/\-])?\d{4}|(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s?\d{2,4})",
    "best_before": r"(best\s?before|use\s?by|exp(iry)?)[.:\s]*((\d{1,2}[/\-])?\d{4}|\d+\s?(months|days|years))",
    "consumer_care": r"(consumer\s?care|customer\s?care|helpline|toll[\s\-]?free|contact\s?us)[^\n]{0,60}",
    "country_of_origin": r"(country\s?of\s?origin|made\s?in|origin)[:\-\s]*([a-z\s]{3,20})",
    "unit_sale_price": r"(unit\s?sale\s?price|price\s?per|rate\s?per)[^\n]{0,30}",
    "manufacturer": r"(mfg\.?\s?by|manufactured\s?by|marketed\s?by|packed\s?by|packer)[:\-\s]*([^\n]{4,80})",
    "importer": r"(imported\s?by)[:\-\s]*([^\n]{4,80})",
}


def preprocess_image(image_bytes: bytes):
    """OpenCV preprocessing: decode, grayscale, denoise, contrast (CLAHE), deskew."""
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    # Resize (upsample small images for better OCR)
    h, w = img.shape[:2]
    if max(h, w) < 1200:
        scale = 1200 / max(h, w)
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    # Contrast enhancement (CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    gray = clahe.apply(gray)

    # Adaptive threshold to sharpen text
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 11
    )

    # Deskew based on minAreaRect of text pixels
    coords = np.column_stack(np.where(thresh < 255))
    angle = 0.0
    if len(coords) > 50:
        rect_angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + rect_angle) if rect_angle < -45 else -rect_angle
        if abs(angle) > 0.5 and abs(angle) < 15:
            (hh, ww) = thresh.shape[:2]
            M = cv2.getRotationMatrix2D((ww // 2, hh // 2), angle, 1.0)
            thresh = cv2.warpAffine(
                thresh, M, (ww, hh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
            )
        else:
            angle = 0.0

    return thresh, {"resized": True, "denoised": True, "contrast_enhanced": True,
                     "deskew_angle_deg": round(float(angle), 2)}


def run_ocr(preprocessed_img):
    """Run Tesseract OCR, reconstruct line-structured text, and compute avg confidence."""
    config = "--oem 3 --psm 6"
    data = pytesseract.image_to_data(
        preprocessed_img, config=config, output_type=pytesseract.Output.DICT
    )
    n = len(data["text"])
    lines_map = {}
    confs = []
    for i in range(n):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except (ValueError, TypeError):
            conf = -1
        if not text or conf < 0:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        lines_map.setdefault(key, []).append(text)
        confs.append(conf)

    full_text = "\n".join(" ".join(words) for words in lines_map.values())
    avg_conf = (sum(confs) / len(confs) / 100.0) if confs else 0.0
    words = [w for ws in lines_map.values() for w in ws]
    return full_text, avg_conf, words, confs


def extract_fields(raw_text: str, avg_conf: float):
    """Regex-based structured field extraction + normalization from OCR text."""
    text_lower = raw_text.lower()
    fields = {}

    for field, pattern in FIELD_PATTERNS.items():
        m = re.search(pattern, text_lower, re.IGNORECASE)
        if m:
            value = m.group(0).strip(" :-\t")
            # per-field confidence: blend OCR avg confidence with a small penalty
            # for very short / ambiguous matches
            length_bonus = min(len(value) / 20.0, 1.0)
            conf = round(min(0.99, max(0.35, avg_conf * (0.7 + 0.3 * length_bonus))), 2)
            fields[field] = {"value": value, "confidence": conf}
        else:
            fields[field] = {"value": None, "confidence": 0.0}

    # product_name: best-effort - first plausible line of text that isn't a matched field
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    if not lines:
        lines = [w for w in raw_text.split(" ") if len(w) > 3]
    product_guess = None
    for l in lines:
        low = l.lower()
        if len(l) > 3 and not any(k in low for k in
                                   ["mfg", "mrp", "rs.", "net", "care", "origin", "best before", "exp"]):
            product_guess = l
            break
    fields["product_name"] = {
        "value": product_guess,
        "confidence": round(min(0.95, max(0.3, avg_conf)), 2) if product_guess else 0.0,
    }

    return fields


def evaluate_rules(fields: dict):
    """Deterministic rule engine: never invents law, only applies stored rules."""
    active_rules = get_active_rules()
    results = []
    penalty = 0
    review_flag = False
    critical_failure = False

    for rule in active_rules:
        field_data = fields.get(rule["field"], {"value": None, "confidence": 0.0})
        value = field_data["value"]
        conf = field_data["confidence"]

        if value is None or value == "":
            outcome = "FAIL"
        elif conf < REVIEW_THRESHOLD:
            outcome = "REVIEW"
        else:
            if rule["condition"] == "required_pattern":
                outcome = "PASS" if re.search(rule["pattern"], value, re.IGNORECASE) else "FAIL"
            else:
                outcome = "PASS"

        entry = {
            "rule_code": rule["rule_code"],
            "field": rule["field"],
            "label": rule["label"],
            "severity": rule["severity"],
            "outcome": outcome,
            "extracted_value": value,
            "confidence": conf,
            "message": (
                None if outcome == "PASS"
                else rule["message"] if outcome == "FAIL"
                else f"Detected but OCR confidence ({round(conf*100)}%) is below the review "
                     f"threshold — officer must verify \"{value}\" manually before this is accepted."
            ),
        }
        results.append(entry)

        if outcome == "FAIL":
            penalty += SEVERITY_WEIGHT[rule["severity"]]
            if rule["severity"] == "HIGH":
                critical_failure = True
        elif outcome == "REVIEW":
            penalty += SEVERITY_WEIGHT[rule["severity"]] * 0.35
            review_flag = True

    score = max(0, round(100 - penalty))

    if critical_failure:
        status = "NON_COMPLIANT"
    elif review_flag:
        status = "REVIEW_REQUIRED"
    else:
        status = "COMPLIANT"

    return {
        "score": score,
        "status": status,
        "rule_results": results,
    }


def run_pipeline(image_bytes: bytes):
    """Full pipeline entry point used by the API."""
    preprocessed, prep_meta = preprocess_image(image_bytes)
    raw_text, avg_conf, words, confs = run_ocr(preprocessed)
    fields = extract_fields(raw_text, avg_conf)
    evaluation = evaluate_rules(fields)

    return {
        "preprocessing": prep_meta,
        "ocr_avg_confidence": round(avg_conf, 2),
        "raw_text": raw_text,
        "fields": fields,
        "score": evaluation["score"],
        "status": evaluation["status"],
        "rule_results": evaluation["rule_results"],
    }
