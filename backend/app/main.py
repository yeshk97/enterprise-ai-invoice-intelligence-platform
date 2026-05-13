from pathlib import Path
import shutil
from uuid import uuid4
import fitz  # PyMuPDF

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from backend.app.schemas.invoice_schema import InvoiceUploadResponse


# ------------------------------------------------------------
# Create FastAPI application instance
# ------------------------------------------------------------
# This "app" object is the main backend application.
# Uvicorn will use this app object to run the API server.
app = FastAPI(
    title="Enterprise AI Invoice Intelligence Platform",
    description="Backend API for invoice intake, AI extraction, validation, RAG, agents, and workflow automation.",
    version="0.1.0",
)


# ------------------------------------------------------------
# Upload folder configuration
# ------------------------------------------------------------
# Path is from Python's built-in pathlib library.
# It helps us work with file/folder paths in a clean way.
#
# During local development, uploaded invoice files will be stored here:
# data/uploads
#
# Later in production, this can be replaced with cloud storage like AWS S3.
UPLOAD_DIR = Path("data/uploads")


# Create the upload folder if it does not already exist.
#
# parents=True  -> create parent folders if needed
# exist_ok=True -> do not throw an error if the folder already exists
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Root endpoint
# ------------------------------------------------------------
@app.get("/")
def root():
    """
    Root endpoint.

    This confirms the backend API is reachable.
    Example:
    GET http://127.0.0.1:8000/
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

    This confirms that the backend service is running.

    In production, health check endpoints are used by:
    - load balancers
    - cloud platforms
    - monitoring tools
    - CI/CD deployment checks
    """

    return {
        "status": "success",
        "message": "Enterprise AI Invoice Intelligence Platform backend is running"
    }
def extract_text_from_pdf(file_path: Path) -> str:
    """
    Extract text from a digital PDF using PyMuPDF.

    This works best when the PDF has selectable text.
    Scanned/handwritten PDFs may need OCR later.
    """

    extracted_text = ""

    with fitz.open(file_path) as document:
        for page in document:
            extracted_text += page.get_text()

    return extracted_text.strip()
@app.post("/invoices/upload", response_model=InvoiceUploadResponse)
async def upload_invoice(
    file: UploadFile = File(...),
    source_type: str = Form(...),
):
    """
    Upload invoice endpoint.

    This endpoint receives:
    1. invoice file
    2. invoice source type

    For now, this endpoint:
    - accepts only PDF files
    - creates a unique stored filename
    - saves the file locally
    - returns upload confirmation
    """

    # Validate file type.
    # For MVP, we only allow PDF invoices.
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed for invoice upload."
        )

    # Preserve original filename for tracking.
    original_filename = file.filename

    # Extract file extension, such as ".pdf".
    file_extension = Path(original_filename).suffix

    # Create a unique filename to avoid overwriting existing files.
    # Example:
    # original: invoice.pdf
    # stored: invoice_7f3a2c9b.pdf
    unique_filename = f"{Path(original_filename).stem}_{uuid4().hex[:8]}{file_extension}"

    # Build the final save path.
    file_path = UPLOAD_DIR / unique_filename

    # Save uploaded file to local storage.
    # Save uploaded file to local storage.
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text from the saved PDF.
    # For now, this works best for digital PDFs with selectable text.
    extracted_text = extract_text_from_pdf(file_path)

    # Return only first 1000 characters as preview to avoid huge API response.
    preview_text = extracted_text[:1000]

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
    }