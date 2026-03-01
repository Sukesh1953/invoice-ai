from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form, Header
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from PIL import Image
import pytesseract
import fitz  # PyMuPDF

import io
import json
import csv

from api.extractor import (
    clean_text,
    extract_invoice_number,
    extract_invoice_date,
    extract_vendor_name,
    extract_subtotal,
    extract_tax,
    extract_total_amount,
    calculate_confidence
)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# ======================================================
# EXTRACT INVOICE
# ======================================================
@router.post("/extract", response_class=HTMLResponse)
async def api_extract_invoice(request: Request, file: UploadFile = File(...)):

    try:
        contents = await file.read()
        filename = file.filename.lower()

        images = []
        extracted_text = ""
        all_blocks = []

        # ======================================================
        # PDF HANDLING
        # ======================================================
        if filename.endswith(".pdf"):

            pdf_document = fitz.open(stream=contents, filetype="pdf")

            # Try digital extraction first
            for page in pdf_document:
                extracted_text += page.get_text()
                all_blocks.extend(page.get_text("blocks"))

            pdf_document.close()

            # If no text found → scanned PDF → OCR fallback
            if not extracted_text.strip():

                pdf_document = fitz.open(stream=contents, filetype="pdf")

                for page in pdf_document:
                    pix = page.get_pixmap(dpi=300)
                    img = Image.open(io.BytesIO(pix.tobytes()))

                    if img.mode != "RGB":
                        img = img.convert("RGB")

                    images.append(img)

                pdf_document.close()

        # ======================================================
        # IMAGE HANDLING
        # ======================================================
        elif filename.endswith((".png", ".jpg", ".jpeg")):

            image = Image.open(io.BytesIO(contents))

            if image.mode != "RGB":
                image = image.convert("RGB")

            images = [image]

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # ======================================================
        # OCR PROCESSING (If Needed)
        # ======================================================
        if images:
            for image in images:

                # Improve OCR accuracy
                image = image.resize(
                    (image.width * 2, image.height * 2),
                    Image.LANCZOS
                )

                raw_text = pytesseract.image_to_string(
                    image,
                    lang="eng",
                    config="--oem 3 --psm 6"
                )

                extracted_text += raw_text

        # Debug log (remove in production)
        print("========== EXTRACTED TEXT ==========")
        print(extracted_text)

        # ======================================================
        # CLEAN & FIELD EXTRACTION
        # ======================================================
        cleaned_text = clean_text(extracted_text)

        vendor_name = extract_vendor_name(cleaned_text, all_blocks if all_blocks else None)
        invoice_number = extract_invoice_number(cleaned_text)
        invoice_date = extract_invoice_date(cleaned_text)
        subtotal = extract_subtotal(cleaned_text)
        tax = extract_tax(cleaned_text)
        total = extract_total_amount(cleaned_text)

        confidence = calculate_confidence(
            vendor_name,
            invoice_number,
            total,
            invoice_date,
            subtotal,
            tax
        )

        results = [{
            "raw_text": extracted_text,
            "cleaned_text": cleaned_text,
            "extracted_fields": {
                "vendor_name": vendor_name,
                "invoice_number": invoice_number,
                "invoice_date": invoice_date,
                "subtotal": subtotal,
                "tax": tax,
                "total_amount": total,
                "confidence": confidence
            }
        }]

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "results": results
            }
        )

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3>")


# ======================================================
# API JSON ENDPOINT (For SaaS)
# ======================================================
@router.post("/api/extract")
async def api_extract_json(
    file: UploadFile = File(...),
    x_api_key: str = Header(None)
):

    # 🔐 Hardcoded API key (for now)
    SECRET_API_KEY = "supersecret123"

    if x_api_key != SECRET_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")

    contents = await file.read()
    filename = file.filename.lower()

    extracted_text = ""
    all_blocks = []

    if filename.endswith(".pdf"):
        pdf_document = fitz.open(stream=contents, filetype="pdf")

        for page in pdf_document:
            extracted_text += page.get_text()
            all_blocks.extend(page.get_text("blocks"))

        pdf_document.close()
    else:
        raise HTTPException(status_code=400, detail="Only PDF supported")

    cleaned_text = clean_text(extracted_text)

    vendor_name = extract_vendor_name(cleaned_text, all_blocks)
    invoice_number = extract_invoice_number(cleaned_text)
    invoice_date = extract_invoice_date(cleaned_text)
    subtotal = extract_subtotal(cleaned_text)
    tax = extract_tax(cleaned_text)
    total = extract_total_amount(cleaned_text)

    confidence = calculate_confidence(
        vendor_name,
        invoice_number,
        total,
        invoice_date,
        subtotal,
        tax
    )

    return {
        "vendor_name": vendor_name,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "subtotal": subtotal,
        "tax": tax,
        "total_amount": total,
        "confidence": confidence
    }


# ======================================================
# DOWNLOAD CSV
# ======================================================
@router.post("/download-csv")
async def download_csv(data: str = Form(...)):

    json_data = json.loads(data)

    file_like = io.StringIO()
    writer = csv.writer(file_like)

    writer.writerow([
        "Vendor Name",
        "Invoice Number",
        "Invoice Date",
        "Subtotal",
        "Tax",
        "Total",
        "Confidence"
    ])

    for page in json_data:
        fields = page["extracted_fields"]
        writer.writerow([
            fields["vendor_name"],
            fields["invoice_number"],
            fields["invoice_date"],
            fields["subtotal"],
            fields["tax"],
            fields["total_amount"],
            fields["confidence"]
        ])

    file_like.seek(0)

    return StreamingResponse(
        file_like,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=invoice_data.csv"}
    )






