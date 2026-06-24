import os

from dotenv import load_dotenv
from google import genai


load_dotenv()


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


DATABASE_SCHEMA_DESCRIPTION = """
You are generating SQL for a SQLite database.

Allowed table:

Table: invoices

Columns:
- id: integer
- original_file_name: text
- stored_file_name: text
- source_type: text
- vendor_name: text
- invoice_number: text
- invoice_date: text
- due_date: text
- total_amount: text
- currency: text
- po_number: text
- order_id: text
- payment_terms: text
- invoice_status: text
- review_reasons: text
- parsed_total_amount: text
- created_at: datetime
- approval_comments: text
- reviewed_at: datetime
- approved_at: datetime
- rejected_at: datetime

Important:
- Generate only SELECT queries.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, or any modifying query.
- Query only the invoices table.
- Always include a LIMIT clause.
- Do not use SELECT *.
- Return only the SQL query.
- Do not return markdown.
- Do not return explanation.
"""


def generate_sql_from_question(question: str) -> str:
    """
    Convert a natural language question into a read-only SQL query using Gemini.

    Important:
    Gemini only proposes the SQL.
    The backend still validates the SQL before executing it.
    """

    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is missing. Please add it to your .env file.")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
{DATABASE_SCHEMA_DESCRIPTION}

User question:
{question}

Generate a safe SQLite SELECT query:
"""

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
    )

    return response.text.strip()