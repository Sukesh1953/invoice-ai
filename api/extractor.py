import re


# -------------------------
# TEXT CLEANING
# -------------------------
def clean_text(text: str) -> str:
    return " ".join(text.split())


# -------------------------
# BASIC FIELD EXTRACTION
# -------------------------
import re

def extract_vendor_name(text):
    try:
        # Try to get first meaningful line
        lines = text.split("\n")

        for line in lines:
            line = line.strip()

            # Skip empty or invoice-related lines
            if not line:
                continue
            if "invoice" in line.lower():
                continue
            if "bill to" in line.lower():
                continue
            if len(line) < 3:
                continue

            # Remove unwanted trailing parts
            cleaned = re.split(r"invoice|bill to|date|#", line, flags=re.IGNORECASE)[0]

            cleaned = cleaned.strip()

            # Basic sanity filter
            if len(cleaned.split()) <= 6:
                return cleaned

        return "Vendor Not Found"

    except:
        return "Vendor Not Found"


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




