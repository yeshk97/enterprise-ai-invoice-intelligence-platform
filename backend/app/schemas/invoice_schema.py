from typing import Any

from pydantic import BaseModel


class InvoiceUploadResponse(BaseModel):
    """
    Response schema for invoice upload API.
    """

    status: str
    message: str
    original_file_name: str
    stored_file_name: str
    source_type: str
    saved_path: str
    extracted_text_preview: str
    extracted_text_length: int
    ai_extracted_fields: dict[str, Any]
    security_flags: list[str]
    invoice_status: str
    review_reasons: list[str]
    parsed_total_amount: str