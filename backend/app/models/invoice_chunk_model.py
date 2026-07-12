from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


class InvoiceChunk(Base):
    """
    Stores smaller text chunks created from extracted invoice text.

    One invoice can have many chunks.
    These chunks will later be used for RAG, embeddings, and document-level Q&A.
    """

    __tablename__ = "invoice_chunks"

    id = Column(Integer, primary_key=True, index=True)

    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)

    chunk_index = Column(Integer, nullable=False)

    chunk_text = Column(Text, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice")