from pathlib import Path
import shutil
from uuid import uuid4

import fitz
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from backend.app.schemas.invoice_schema import InvoiceUploadResponse
from backend.app.services.gemini_invoice_extraction_service import (
    extract_invoice_fields_with_gemini,
)
from backend.app.services.invoice_validation_service import validate_invoice_fields
from backend.app.services.security_guardrail_service import detect_prompt_injection


# ------------------------------------------------------------
# Create FastAPI application instance
# ------------------------------------------------------------
app = FastAPI(
    title="Enterprise AI Invoice Intelligence Platform",
    description="Backend API for invoice intake, AI extraction, validation, RAG, agents, and workflow automation.",
    version="0.1.0",
)


# ------------------------------------------------------------
# Upload folder configuration
# ------------------------------------------------------------
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# PDF text extraction helper
# ------------------------------------------------------------
def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from a digital PDF using PyMuPDF.

    This works best when the PDF has selectable text.
    Scanned or handwritten PDFs may need OCR later.
    """

    extracted_text = ""

    with fitz.open(file_path) as document:
        for page in document:
            extracted_text += page.get_text()

    return extracted_text.strip()


# ------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------
@app.get("/")
def root():
    """
    Root endpoint.
    """

    return {
        "message": "Welcome to the Enterprise AI Invoice Intelligence Platform API"
    }


# ------------------------------------------------------------
# Health check endpoint
# ------------------------------------------------------------
@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """

    return {
        "status": "success",
        "message": "Enterprise AI Invoice Intelligence Platform backend is running",
    }


# ------------------------------------------------------------
# Invoice upload endpoint
# ------------------------------------------------------------
@app.post("/invoices/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    source_type: str = Form(...),
):
    """
    Upload invoice endpoint.

    This endpoint:
    - accepts only PDF files
    - creates a unique stored filename
    - saves the file locally
    - extracts text from the PDF
    - scans for prompt injection
    - sends extracted text to Gemini
    - validates extracted fields
    - returns upload confirmation and invoice status
    """

    # Validate file type.
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed for invoice upload.",
        )

    # Preserve original filename.
    original_filename = file.filename

    # Extract file extension.
    file_extension = Path(original_filename).suffix

    # Create unique stored filename.
    unique_filename = (
        f"{Path(original_filename).stem}_{uuid4().hex[:8]}{file_extension}"
    )

    # Build final save path.
    file_path = UPLOAD_DIR / unique_filename

    # Save uploaded file to local storage.
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from the saved PDF.
    extracted_text = extract_text_from_pdf(file_path)

    # Return only first 1000 characters as preview.
    preview_text = extracted_text[:1000]

    # Scan extracted invoice text for possible prompt injection.
    security_flags = detect_prompt_injection(extracted_text)

    # Send extracted text to Gemini for structured invoice field extraction.
    ai_extracted_fields = extract_invoice_fields_with_gemini(extracted_text)

    # Validate extracted fields and apply business rules.
    validation_result = validate_invoice_fields(
        extracted_fields=ai_extracted_fields,
        security_flags=security_flags,
    )

    # Return response back to user/Postman/frontend.
    return {
        "status": "success",
        "message": "Invoice uploaded successfully",
        "original_file_name": original_filename,
        "stored_file_name": unique_filename,
        "source_type": source_type,
        "saved_path": str(file_path),
        "extracted_text_preview": preview_text,
        "extracted_text_length": len(extracted_text),
        "ai_extracted_fields": ai_extracted_fields,
        "security_flags": security_flags,
        "invoice_status": validation_result["invoice_status"],
        "review_reasons": validation_result["review_reasons"],
        "parsed_total_amount": validation_result["parsed_total_amount"],
    }