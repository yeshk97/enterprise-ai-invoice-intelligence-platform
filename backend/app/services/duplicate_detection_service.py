import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.invoice_model import Invoice


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA256 hash for uploaded file.

    This helps detect the exact same PDF file even if the file name changes.
    """

    sha256_hash = hashlib.sha256()

    with file_path.open("rb") as file:
        for byte_block in iter(lambda: file.read(4096), b""):
            sha256_hash.update(byte_block)

    return sha256_hash.hexdigest()


def find_exact_file_duplicate(db: Session, file_hash: str) -> Invoice | None:
    """
    Check whether the exact same file was already uploaded.
    """

    if not file_hash:
        return None

    return db.query(Invoice).filter(Invoice.file_hash == file_hash).first()


def find_business_duplicate(db: Session, extracted_fields: dict) -> Invoice | None:
    """
    Check possible duplicate invoice using business fields.

    This catches cases where the same invoice arrives from different sources
    or with a different file name.
    """

    vendor_name = extracted_fields.get("vendor_name", "").strip()
    invoice_number = extracted_fields.get("invoice_number", "").strip()
    invoice_date = extracted_fields.get("invoice_date", "").strip()
    total_amount = extracted_fields.get("total_amount", "").strip()

    if not vendor_name or not invoice_number or not total_amount:
        return None

    query = db.query(Invoice).filter(
        Invoice.vendor_name == vendor_name,
        Invoice.invoice_number == invoice_number,
        Invoice.total_amount == total_amount,
    )

    if invoice_date:
        query = query.filter(Invoice.invoice_date == invoice_date)

    return query.first()