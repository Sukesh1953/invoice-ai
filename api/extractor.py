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
        lines = text.split("\n")

        # Take only top 10 lines (most vendor names are here)
        top_lines = lines[:10]

        for line in top_lines:
            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            # Skip unwanted lines
            if any(keyword in lower for keyword in [
                "invoice",
                "bill to",
                "ship to",
                "date",
                "subtotal",
                "total",
                "tax"
            ]):
                continue

            # Skip numeric-heavy lines
            if sum(c.isdigit() for c in line) > 3:
                continue

            # Remove anything after invoice keyword
            cleaned = re.split(r"invoice|#", line, flags=re.IGNORECASE)[0].strip()

            # Must contain at least 2 words
            if len(cleaned.split()) >= 2:
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
    score = 0

    if subtotal and total:
        score += 40

    if tax is not None:
        score += 20

    # Arithmetic validation
    if subtotal and total:
        try:
            calculated = subtotal + (tax if tax else 0)
            if abs(calculated - total) < 1:
                score += 40
        except:
            pass

    if score >= 80:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "LOW"




