from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
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


# ----------------------------------------
# EXTRACT INVOICE
# ----------------------------------------
@router.post("/extract-invoice", response_class=HTMLResponse)
async def extract_invoice(request: Request, file: UploadFile = File(...)):
    try:
        contents = await file.read()
        filename = file.filename.lower()

        results = []
        images = []
        extracted_text = ""

        # ----------------------------------------
        # PDF Handling
        # ----------------------------------------
        if filename.endswith(".pdf"):

            # Try direct text extraction first (Digital PDF)
            pdf_document = fitz.open(stream=contents, filetype="pdf")

            for page in pdf_document:
                extracted_text += page.get_text()

            pdf_document.close()

            # If digital PDF contains text
            if extracted_text.strip():
                pass  # We already have extracted_text

            else:
                # Scanned PDF → fallback to OCR
                images = convert_from_bytes(contents)
                if not extracted_text.strip():
                    pdf_document = fitz.open(stream=contents, filetype="pdf")
                    for page in pdf_document:
                        pix = page.get_pixmap(dpi=300)
                        img = Image.open(io.BytesIO(pix.tobytes()))
                        images.append(img)

                    pdf_document.close()

        # ----------------------------------------
        # Image Handling
        # ----------------------------------------
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(io.BytesIO(contents))

            if image.mode != "RGB":
                image = image.convert("RGB")

            images = [image]

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        # ----------------------------------------
        # OCR Processing (if needed)
        # ----------------------------------------
        if images:
            for image in images:

                # Resize for better OCR accuracy
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

        # ----------------------------------------
        # Clean & Extract Fields
        # ----------------------------------------
        cleaned_text = clean_text(extracted_text)

        vendor_name = extract_vendor_name(cleaned_text)
        invoice_number = extract_invoice_number(cleaned_text)
        invoice_date = extract_invoice_date(cleaned_text)
        subtotal = extract_subtotal(cleaned_text)
        tax = extract_tax(cleaned_text)
        total = extract_total_amount(cleaned_text)
        confidence = calculate_confidence(subtotal, tax, total)

        extracted_fields = {
            "vendor_name": vendor_name,
            "invoice_number": invoice_number,
            "invoice_date": invoice_date,
            "subtotal": subtotal,
            "tax": tax,
            "total_amount": total,
            "confidence": confidence
        }

        results.append({
            "raw_text": extracted_text,
            "cleaned_text": cleaned_text,
            "extracted_fields": extracted_fields
        })

        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "results": results
            }
        )

    except Exception as e:
        return HTMLResponse(content=f"<h3>Error: {str(e)}</h3>")


# ----------------------------------------
# DOWNLOAD JSON
# ----------------------------------------
@router.post("/download-json")
async def download_json(data: str = Form(...)):
    json_data = json.loads(data)

    file_like = io.StringIO()
    json.dump(json_data, file_like, indent=4)
    file_like.seek(0)

    return StreamingResponse(
        file_like,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=invoice_data.json"}
    )


# ----------------------------------------
# DOWNLOAD CSV
# ----------------------------------------
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






