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