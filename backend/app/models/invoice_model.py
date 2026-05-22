from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.app.db.database import Base


class Invoice(Base):
    """
    Invoice database model.

    This class represents the invoices table in SQLite.

    Each object of this class becomes one row in the invoices table.
    """

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)

    # File information
    original_file_name = Column(String, nullable=False)
    stored_file_name = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    saved_path = Column(String, nullable=False)

    # Extracted invoice fields
    vendor_name = Column(String, nullable=True)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    total_amount = Column(String, nullable=True)
    currency = Column(String, nullable=True)
    po_number = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    payment_terms = Column(String, nullable=True)

    # Processing results
    invoice_status = Column(String, nullable=False)
    review_reasons = Column(Text, nullable=True)
    parsed_total_amount = Column(String, nullable=True)

    # Audit timestamp
    created_at = Column(DateTime, default=datetime.utcnow)