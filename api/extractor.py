import re


# -------------------------
# TEXT CLEANING
# -------------------------
def clean_text(text: str) -> str:
    return " ".join(text.split())


# -------------------------
# BASIC FIELD EXTRACTION
# -------------------------
def extract_vendor_name(text: str) -> str:
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    invalid_keywords = [
        "invoice",
        "invoice #",
        "bill",
        "date",
        "gst",
        "total",
        "subtotal",
        "tax",
        "amount",
        "balance",
        "due"
    ]

    for line in lines[:15]:  # Only inspect top section of invoice
        lower = line.lower()

        # Skip unwanted keywords
        if any(keyword in lower for keyword in invalid_keywords):
            continue

        # Skip lines that are mostly numbers
        digit_ratio = sum(c.isdigit() for c in line) / max(len(line), 1)
        if digit_ratio > 0.4:
            continue

        # Skip very short lines
        if len(line) < 4:
            continue

        return line

    return "Not Found"


def extract_invoice_number(text: str):
    match = re.search(
        r'Invoice\s*#?:?\s*([A-Z0-9\-]+)',
        text,
        re.IGNORECASE
    )
    return match.group(1) if match else None


def extract_invoice_date(text: str):
    match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
    return match.group(1) if match else None


# -------------------------
# FINANCIAL EXTRACTION
# -------------------------
def extract_subtotal(text):
    match = re.search(
        r'\bSubtotal\b\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
        text,
        re.IGNORECASE
    )
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def extract_tax(text):
    match = re.search(
        r'\bTax\b.*?\$?([\d,]+(?:\.\d{2})?)',
        text,
        re.IGNORECASE
    )
    if match:
        return float(match.group(1).replace(",", ""))
    return None


def extract_total_amount(text):
    patterns = [
        r'\bTotal\b\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
        r'\bGrand Total\b\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
        r'\bAmount Due\b\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
        r'\bBalance Due\b\s*:?\s*\$?([\d,]+(?:\.\d{2})?)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1).replace(",", ""))

    return None


# -------------------------
# CONFIDENCE LOGIC
# -------------------------
def calculate_confidence(subtotal, tax, total):
    if subtotal and tax and total:
        if abs((subtotal + tax) - total) < 1:
            return "HIGH"
        else:
            return "MEDIUM"

    if total:
        return "LOW"

    return "FAILED"




