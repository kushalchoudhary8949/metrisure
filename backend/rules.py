"""
Versioned Legal Metrology compliance rules.
These mirror the mandatory declarations under the Legal Metrology
(Packaged Commodities) Rules, 2011 (India) for demonstration purposes.
NOTE: for a real deployment this table must be populated from the
official Department of Consumer Affairs Legal Metrology notifications.
The rule engine is intentionally pure/deterministic and never calls an LLM.
"""

REVIEW_THRESHOLD = 0.70  # OCR confidence below this -> send field to human review, never auto-fail

RULES = [
    {
        "rule_code": "LM001",
        "version": "CURRENT",
        "field": "manufacturer",
        "label": "Name & address of manufacturer/packer/importer",
        "condition": "required",
        "severity": "HIGH",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Manufacturer/packer/importer name & address not detected on the label.",
    },
    {
        "rule_code": "LM002",
        "version": "CURRENT",
        "field": "product_name",
        "label": "Common / generic name of the commodity",
        "condition": "required",
        "severity": "MEDIUM",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Common/generic product name not detected on the label.",
    },
    {
        "rule_code": "LM003",
        "version": "CURRENT",
        "field": "net_quantity",
        "label": "Net quantity in standard units",
        "condition": "required_pattern",
        "pattern": r"\d+(\.\d+)?\s?(g|kg|ml|l|litre|liter|gm|gram|kilogram)",
        "severity": "HIGH",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Net quantity missing or not expressed in standard units (g/kg/ml/l).",
    },
    {
        "rule_code": "LM004",
        "version": "CURRENT",
        "field": "mrp",
        "label": "Maximum Retail Price (MRP), inclusive of all taxes",
        "condition": "required_pattern",
        "pattern": r"(rs\.?|inr|₹)\s?\d+(\.\d{1,2})?",
        "severity": "HIGH",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "MRP (inclusive of all taxes) not detected on the label.",
    },
    {
        "rule_code": "LM005",
        "version": "CURRENT",
        "field": "manufacturing_date",
        "label": "Month & year of manufacture/packing/import",
        "condition": "required_pattern",
        "pattern": r"(\d{1,2}[/\-])?\d{4}|\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s?\d{2,4}",
        "severity": "MEDIUM",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Month & year of manufacture/packing not detected on the label.",
    },
    {
        "rule_code": "LM006",
        "version": "CURRENT",
        "field": "consumer_care",
        "label": "Consumer care / customer support details",
        "condition": "required",
        "severity": "MEDIUM",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Consumer care contact (phone/email/address) not detected on the label.",
    },
    {
        "rule_code": "LM007",
        "version": "CURRENT",
        "field": "country_of_origin",
        "label": "Country of origin (mandatory for imported goods)",
        "condition": "required",
        "severity": "HIGH",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Country of origin not detected on the label.",
    },
    {
        "rule_code": "LM008",
        "version": "CURRENT",
        "field": "unit_sale_price",
        "label": "Unit sale price (price per standard unit, e.g. per kg/litre)",
        "condition": "required",
        "severity": "LOW",
        "applicability": "ALL",
        "effective_from": "2011-01-01",
        "effective_to": None,
        "message": "Unit sale price (price per kg/litre) not detected on the label.",
    },
]

SEVERITY_WEIGHT = {"HIGH": 25, "MEDIUM": 12, "LOW": 6}


def get_active_rules():
    return [r for r in RULES if r["version"] == "CURRENT"]
