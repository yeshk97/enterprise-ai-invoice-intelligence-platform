from typing import Any

from pydantic import BaseModel


class InvoiceUploadResponse(BaseModel):
    """
    Response schema for invoice upload API.
    """

    status: str
    message: str
    invoice_id: int
    original_file_name: str
    stored_file_name: str
    source_type: str
    saved_path: str
    extracted_text_preview: str
    extracted_text_length: int
    ai_extracted_fields: dict[str, Any]
    security_flags: list[str]
    duplicate_type: str
    duplicate_invoice_id: int | None
    invoice_status: str
    review_reasons: list[str]
    parsed_total_amount: str


class InvoiceReviewUpdateRequest(BaseModel):
    """
    Request schema for updating invoice fields during human review.
    """

    vendor_name: str | None = None
    invoice_number: str | None = None
    invoice_date: str | None = None
    due_date: str | None = None
    total_amount: str | None = None
    currency: str | None = None
    po_number: str | None = None
    order_id: str | None = None
    payment_terms: str | None = None


class InvoiceActionRequest(BaseModel):
    """
    Request schema for approve/reject actions.
    """

    comments: str | None = None

class AskSQLRequest(BaseModel):
    """
    Request schema for AskSQL natural language questions.
    """

    question: str