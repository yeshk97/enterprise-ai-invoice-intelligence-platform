import os

from dotenv import load_dotenv
from google import genai
from sqlalchemy.orm import Session

from backend.app.models.invoice_chunk_model import InvoiceChunk
from backend.app.models.invoice_model import Invoice


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def answer_invoice_question(db: Session, invoice_id: int, question: str) -> dict:
    """
    Answer a question using stored chunks for one invoice.

    This is a simple invoice-level RAG flow:
    invoice_id -> chunks -> context -> Gemini answer.
    """

    if not GEMINI_API_KEY:
        return {
            "status": "error",
            "message": "GEMINI_API_KEY is missing.",
            "invoice_id": invoice_id,
            "answer": "",
            "source_chunks": [],
        }

    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        return {
            "status": "error",
            "message": "Invoice not found.",
            "invoice_id": invoice_id,
            "answer": "",
            "source_chunks": [],
        }

    chunks = (
        db.query(InvoiceChunk)
        .filter(InvoiceChunk.invoice_id == invoice_id)
        .order_by(InvoiceChunk.chunk_index.asc())
        .all()
    )

    if not chunks:
        return {
            "status": "error",
            "message": "No chunks found for this invoice. Please index the invoice first.",
            "invoice_id": invoice_id,
            "answer": "",
            "source_chunks": [],
        }

    context = "\n\n".join(
        [
            f"Chunk {chunk.chunk_index}:\n{chunk.chunk_text}"
            for chunk in chunks
        ]
    )

    prompt = f"""
You are an invoice document assistant.

Answer the user's question using only the invoice context below.

Rules:
- Use only the provided invoice context.
- Do not guess.
- If the answer is not found in the context, say: "I could not find that information in the invoice text."
- Keep the answer concise.
- Mention which chunk supported the answer when possible.

Invoice metadata:
Invoice ID: {invoice.id}
Original file name: {invoice.original_file_name}
Vendor: {invoice.vendor_name}
Invoice number: {invoice.invoice_number}

Invoice context:
{context}

User question:
{question}

Answer:
"""

    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return {
        "status": "success",
        "message": "Invoice question answered successfully.",
        "invoice_id": invoice_id,
        "question": question,
        "answer": response.text.strip(),
        "source_chunks": [
            {
                "chunk_index": chunk.chunk_index,
                "chunk_text": chunk.chunk_text,
            }
            for chunk in chunks
        ],
    }