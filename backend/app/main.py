import json
from pathlib import Path
import shutil
from uuid import uuid4

from datetime import datetime

import fitz
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile

from sqlalchemy.orm import Session
from sqlalchemy import text

from backend.app.models.invoice_chunk_model import InvoiceChunk

from backend.app.db.database import Base, engine, get_db
from backend.app.models.invoice_model import Invoice
from backend.app.schemas.invoice_schema import (
    AskSQLRequest,
    InvoiceActionRequest,
    InvoiceReviewUpdateRequest,
    InvoiceUploadResponse,
)
from backend.app.services.sql_guardrail_service import validate_read_only_sql
from backend.app.services.text_to_sql_service import generate_sql_from_question
from backend.app.services.gemini_invoice_extraction_service import (
    extract_invoice_fields_with_gemini,
)
from backend.app.services.invoice_validation_service import validate_invoice_fields
from backend.app.services.security_guardrail_service import detect_prompt_injection

from backend.app.services.duplicate_detection_service import (
    calculate_file_hash,
    find_business_duplicate,
    find_exact_file_duplicate,
)


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
# Create database tables
# ------------------------------------------------------------
Base.metadata.create_all(bind=engine)


# ------------------------------------------------------------
# PDF text extraction helper
# ------------------------------------------------------------
def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from a digital PDF using PyMuPDF.
    """

    extracted_text = ""

    with fitz.open(file_path) as document:
        for page in document:
            extracted_text += page.get_text()

    return extracted_text.strip()

@app.get("/invoices")
def get_invoices(db: Session = Depends(get_db)):
    """
    Get all processed invoices from the database.

    This endpoint helps verify that uploaded invoice results
    are being stored and can be retrieved later.
    """

    invoices = db.query(Invoice).order_by(Invoice.id.desc()).all()

    return {
        "status": "success",
        "count": len(invoices),
        "invoices": [invoice_to_dict(invoice) for invoice in invoices],
    }
@app.get("/invoices/{invoice_id}")
def get_invoice_by_id(
    invoice_id: int,
    db: Session = Depends(get_db),
):
    """
    Get one processed invoice by invoice ID.
    """

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    return {
        "status": "success",
        "invoice": invoice_to_dict(invoice),
    }

@app.post("/ask-sql")
def ask_sql(
    request: AskSQLRequest,
    db: Session = Depends(get_db),
):
    """
    AskSQL endpoint.

    Converts a natural language question into a safe read-only SQL query,
    validates the generated SQL, executes it, and returns database rows.

    Security rule:
    - Only SELECT queries are allowed.
    - No INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, or PRAGMA.
    """

    # Step 1: Ask Gemini to generate SQL from the user's question.
    generated_sql = generate_sql_from_question(request.question)

    # Step 2: Validate that SQL is safe and read-only.
    is_safe, safe_sql_or_reason = validate_read_only_sql(generated_sql)

    if not is_safe:
        return {
            "status": "blocked",
            "question": request.question,
            "generated_sql": generated_sql,
            "reason": safe_sql_or_reason,
            "rows": [],
        }

    safe_sql = safe_sql_or_reason

    # Step 3: Execute only the validated SQL.
    result = db.execute(text(safe_sql))

    rows = [
        dict(row._mapping)
        for row in result.fetchall()
    ]

    return {
        "status": "success",
        "question": request.question,
        "generated_sql": safe_sql,
        "row_count": len(rows),
        "rows": rows,
    }

@app.patch("/invoices/{invoice_id}/review")
def review_invoice(
    invoice_id: int,
    review_data: InvoiceReviewUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Update invoice fields after human review.

    This is used when a finance analyst corrects missing or wrong fields.
    """

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    update_data = review_data.model_dump(exclude_unset=True)

    for field_name, field_value in update_data.items():
        setattr(invoice, field_name, field_value)

    invoice.reviewed_at = datetime.utcnow()

    # Basic status recalculation after human review.
    if invoice.total_amount and invoice.parsed_total_amount:
        try:
            amount_value = float(str(invoice.parsed_total_amount).replace(",", ""))
            if amount_value > 10000:
                invoice.invoice_status = "Pending Manager Approval"
            else:
                invoice.invoice_status = "Ready for Approval"
        except ValueError:
            invoice.invoice_status = "Needs Review"
    else:
        invoice.invoice_status = "Needs Review"

    invoice.review_reasons = "[]"

    db.commit()
    db.refresh(invoice)

    return {
        "status": "success",
        "message": "Invoice reviewed and updated successfully",
        "invoice": invoice_to_dict(invoice),
    }

@app.patch("/invoices/{invoice_id}/approve")
def approve_invoice(
    invoice_id: int,
    action_data: InvoiceActionRequest,
    db: Session = Depends(get_db),
):
    """
    Approve an invoice after review or manager approval.
    """

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    invoice.invoice_status = "Approved"
    invoice.approval_comments = action_data.comments
    invoice.approved_at = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return {
        "status": "success",
        "message": "Invoice approved successfully",
        "invoice": invoice_to_dict(invoice),
    }

@app.patch("/invoices/{invoice_id}/reject")
def reject_invoice(
    invoice_id: int,
    action_data: InvoiceActionRequest,
    db: Session = Depends(get_db),
):
    """
    Reject an invoice with optional comments.
    """

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(
            status_code=404,
            detail="Invoice not found",
        )

    invoice.invoice_status = "Rejected"
    invoice.approval_comments = action_data.comments
    invoice.rejected_at = datetime.utcnow()

    db.commit()
    db.refresh(invoice)

    return {
        "status": "success",
        "message": "Invoice rejected successfully",
        "invoice": invoice_to_dict(invoice),
    }


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

def invoice_to_dict(invoice: Invoice) -> dict:
    """
    Convert an Invoice database object into a dictionary.

    This helps us return clean JSON responses from database records.
    """

    return {
        "id": invoice.id,
        "original_file_name": invoice.original_file_name,
        "stored_file_name": invoice.stored_file_name,
        "source_type": invoice.source_type,
        "saved_path": invoice.saved_path,
        "extracted_text_length": len(invoice.extracted_text) if invoice.extracted_text else 0,
        "extracted_text_preview": invoice.extracted_text[:500] if invoice.extracted_text else "",
        "vendor_name": invoice.vendor_name,
        "invoice_number": invoice.invoice_number,
        "invoice_date": invoice.invoice_date,
        "due_date": invoice.due_date,
        "total_amount": invoice.total_amount,
        "currency": invoice.currency,
        "po_number": invoice.po_number,
        "order_id": invoice.order_id,
        "payment_terms": invoice.payment_terms,
        "invoice_status": invoice.invoice_status,
        "review_reasons": json.loads(invoice.review_reasons)
        if invoice.review_reasons
        else [],
        "parsed_total_amount": invoice.parsed_total_amount,
                "approval_comments": invoice.approval_comments,
        "reviewed_at": invoice.reviewed_at.isoformat() if invoice.reviewed_at else None,
        "approved_at": invoice.approved_at.isoformat() if invoice.approved_at else None,
        "rejected_at": invoice.rejected_at.isoformat() if invoice.rejected_at else None,
        "created_at": invoice.created_at.isoformat() if invoice.created_at else None,
    }
# ------------------------------------------------------------
# Invoice upload endpoint
# ------------------------------------------------------------
@app.post("/invoices/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    source_type: str = Form(...),
    db: Session = Depends(get_db),
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
    - saves processed invoice data into SQLite
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

    # Calculate file hash for exact duplicate detection.
    file_hash = calculate_file_hash(file_path)

    # Check if the exact same PDF file was already uploaded before.
    exact_duplicate = find_exact_file_duplicate(db, file_hash)

    # Extract text from the saved PDF.
    extracted_text = extract_text_from_pdf(file_path)

    # Return only first 1000 characters as preview.
    preview_text = extracted_text[:1000]

    # Scan extracted invoice text for possible prompt injection.
    security_flags = detect_prompt_injection(extracted_text)

    # Send extracted text to Gemini for structured invoice field extraction.
    ai_extracted_fields = extract_invoice_fields_with_gemini(extracted_text)

    # Check for business duplicate using extracted invoice fields.
    business_duplicate = find_business_duplicate(db, ai_extracted_fields)

    duplicate_flags = []
    duplicate_type = ""
    duplicate_invoice_id = None

    if exact_duplicate:
        duplicate_type = "exact_file_duplicate"
        duplicate_invoice_id = exact_duplicate.id
        duplicate_flags.append(
            f"Exact duplicate file detected with existing invoice ID {exact_duplicate.id}"
        )

    elif business_duplicate:
        duplicate_type = "business_duplicate"
        duplicate_invoice_id = business_duplicate.id
        duplicate_flags.append(
            f"Possible duplicate invoice detected with existing invoice ID {business_duplicate.id}"
        )

    all_security_and_duplicate_flags = security_flags + duplicate_flags

    validation_result = validate_invoice_fields(
    extracted_fields=ai_extracted_fields,
    security_flags=all_security_and_duplicate_flags,
    )

    # Save processed invoice result into SQLite database.
    invoice_record = Invoice(
        original_file_name=original_filename,
        stored_file_name=unique_filename,
        source_type=source_type,
        saved_path=str(file_path),
        file_hash=file_hash,
        vendor_name=ai_extracted_fields.get("vendor_name", ""),
        invoice_number=ai_extracted_fields.get("invoice_number", ""),
        invoice_date=ai_extracted_fields.get("invoice_date", ""),
        due_date=ai_extracted_fields.get("due_date", ""),
        total_amount=ai_extracted_fields.get("total_amount", ""),
        currency=ai_extracted_fields.get("currency", ""),
        po_number=ai_extracted_fields.get("po_number", ""),
        order_id=ai_extracted_fields.get("order_id", ""),
        payment_terms=ai_extracted_fields.get("payment_terms", ""),
        invoice_status=validation_result["invoice_status"],
        review_reasons=json.dumps(validation_result["review_reasons"]),
        parsed_total_amount=validation_result["parsed_total_amount"],
        extracted_text=extracted_text,
    )

    db.add(invoice_record)
    db.commit()
    db.refresh(invoice_record)

    # Return response back to user/Postman/frontend.
    return {
        "status": "success",
        "message": "Invoice uploaded successfully",
        "invoice_id": invoice_record.id,
        "original_file_name": original_filename,
        "stored_file_name": unique_filename,
        "source_type": source_type,
        "saved_path": str(file_path),
        "extracted_text_preview": preview_text,
        "extracted_text_length": len(extracted_text),
        "ai_extracted_fields": ai_extracted_fields,
        "security_flags": all_security_and_duplicate_flags,
        "duplicate_type": duplicate_type,
        "duplicate_invoice_id": duplicate_invoice_id,
        "invoice_status": validation_result["invoice_status"],
        "review_reasons": validation_result["review_reasons"],
        "parsed_total_amount": validation_result["parsed_total_amount"],
    }