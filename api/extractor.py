import re


# -------------------------
# TEXT CLEANING
# -------------------------
def clean_text(text: str) -> str:
    return " ".join(text.split())


# -------------------------
# BASIC FIELD EXTRACTION
# -------------------------
def extract_vendor_name(text, blocks=None):
    # ----- Layer 1: Keyword Search -----
    keywords = ["vendor:", "supplier:", "from:", "bill from:"]

    for line in text.split("\n")[:15]:
        lower = line.lower()
        for key in keywords:
            if key in lower:
                return line.split(":")[-1].strip()

    # ----- Layer 2: Layout-Based (Top Blocks) -----
    if blocks:
        # Sort blocks by vertical position (top first)
        blocks_sorted = sorted(blocks, key=lambda b: b[1])

        for block in blocks_sorted[:5]:  # top 5 blocks
            block_text = block[4].strip()

            if len(block_text.split()) >= 2 and len(block_text) > 5:
                if not any(word in block_text.lower() for word in
                           ["invoice", "bill", "date", "tax", "total"]):
                    return block_text

    # ----- Layer 3: Fallback -----
    for line in text.split("\n")[:10]:
        clean = line.strip()
        if len(clean.split()) >= 2 and len(clean) > 5:
            return clean

    return "Vendor Not Found"


import re

def extract_invoice_number(text):
    patterns = [
        r"invoice\s*(number|no|#)\s*[:\-]?\s*([A-Za-z0-9\-]+)",
        r"\b[A-Z]{2,}-\d{3,}\b"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(match.lastindex)

    return None


def extract_invoice_date(text):
    patterns = [
        r"\b\d{4}-\d{2}-\d{2}\b",        # 2026-02-26
        r"\b\d{2}/\d{2}/\d{4}\b",        # 26/02/2026
        r"\b\d{2}-\d{2}-\d{4}\b"         # 26-02-2026
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group()

    return None


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


import re

def extract_total_amount(text):

    # Priority patterns (most specific first)
    patterns = [
        r"grand\s*total[:\s]*₹?\$?\s?([\d,]+\.\d{2})",
        r"total\s*amount[:\s]*₹?\$?\s?([\d,]+\.\d{2})",
        r"total\s*payable[:\s]*₹?\$?\s?([\d,]+\.\d{2})",
        r"amount\s*due[:\s]*₹?\$?\s?([\d,]+\.\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).replace(",", "")

    # Fallback: match standalone "Total" but NOT "Subtotal"
    fallback_pattern = r"(?<!sub)\btotal\b[:\s]*₹?\$?\s?([\d,]+\.\d{2})"
    match = re.search(fallback_pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", "")

    return None


# -------------------------
# CONFIDENCE LOGIC
# -------------------------
def calculate_confidence(vendor, invoice_number, total, date, subtotal, tax):
    score = 0

    # Critical fields (high weight)
    if vendor and vendor != "Vendor Not Found":
        score += 30

    if invoice_number:
        score += 25

    if total and float(total) > 0:
        score += 25

    if date:
        score += 10

    # Secondary fields
    if subtotal:
        score += 5

    if tax is not None:
        score += 5

    if score >= 80:
        return "HIGH"
    elif score >= 50:
        return "MEDIUM"
    else:
        return "LOW"




