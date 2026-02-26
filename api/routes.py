from fastapi import APIRouter, UploadFile, File, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pdf2image import convert_from_bytes
from PIL import Image
import pytesseract
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

# IMPORTANT (Windows Users)

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

        images = []

        # PDF Handling
        if filename.endswith(".pdf"):
            images = convert_from_bytes(contents)

        # Image Handling
        elif filename.endswith((".png", ".jpg", ".jpeg")):
            image = Image.open(io.BytesIO(contents))

            if image.mode != "RGB":
                image = image.convert("RGB")

            images = [image]

        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        results = []

        for image in images:

            # Resize image for better OCR
            image = image.resize(
                (image.width * 2, image.height * 2),
                Image.LANCZOS
            )

            # OCR
            raw_text = pytesseract.image_to_string(
                image,
                lang="eng",
                config="--oem 3 --psm 6"
            )

            cleaned_text = clean_text(raw_text)

            # Extract fields
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
                "raw_text": raw_text,
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






