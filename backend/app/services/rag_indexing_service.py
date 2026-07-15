from sqlalchemy.orm import Session

from backend.app.models.invoice_chunk_model import InvoiceChunk
from backend.app.models.invoice_model import Invoice
from backend.app.services.chunking_service import chunk_text


def index_invoice_text(db: Session, invoice_id: int) -> dict:
    """
    Create text chunks for one invoice and store them in invoice_chunks table.

    This is the first RAG indexing step.
    """

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        return {
            "status": "error",
            "message": "Invoice not found",
            "invoice_id": invoice_id,
            "chunks_created": 0,
        }

    if not invoice.extracted_text:
        return {
            "status": "error",
            "message": "Invoice does not have extracted_text saved",
            "invoice_id": invoice_id,
            "chunks_created": 0,
        }

    # Delete existing chunks for this invoice so we do not duplicate them
    db.query(InvoiceChunk).filter(InvoiceChunk.invoice_id == invoice_id).delete()

    chunks = chunk_text(invoice.extracted_text)

    for index, chunk in enumerate(chunks):
        invoice_chunk = InvoiceChunk(
            invoice_id=invoice.id,
            chunk_index=index,
            chunk_text=chunk,
        )
        db.add(invoice_chunk)

    db.commit()

    return {
        "status": "success",
        "message": "Invoice text indexed into chunks successfully",
        "invoice_id": invoice_id,
        "chunks_created": len(chunks),
    }