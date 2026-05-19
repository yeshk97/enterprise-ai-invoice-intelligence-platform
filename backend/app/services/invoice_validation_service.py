from decimal import Decimal, InvalidOperation


TRUSTED_VENDORS = [
    "SuperStore",
    "FedEx",
    "Amazon Business",
    "UPS",
    "Staples",
]


def parse_amount(amount_text: str) -> Decimal | None:
    """
    Convert amount text into Decimal.

    Example:
    "$1,476.32" -> Decimal("1476.32")
    "1,476.32" -> Decimal("1476.32")
    """

    if not amount_text:
        return None

    cleaned_amount = (
        amount_text
        .replace("$", "")
        .replace(",", "")
        .replace("USD", "")
        .strip()
    )

    try:
        return Decimal(cleaned_amount)
    except InvalidOperation:
        return None


def validate_invoice_fields(extracted_fields: dict, security_flags: list[str]) -> dict:
    """
    Validate AI-extracted invoice fields and decide invoice status.

    This function does not use AI.
    It uses deterministic backend rules.
    """

    review_reasons = []
    invoice_status = "Ready for Review"

    vendor_name = extracted_fields.get("vendor_name", "").strip()
    invoice_number = extracted_fields.get("invoice_number", "").strip()
    invoice_date = extracted_fields.get("invoice_date", "").strip()
    due_date = extracted_fields.get("due_date", "").strip()
    total_amount_text = extracted_fields.get("total_amount", "").strip()
    po_number = extracted_fields.get("po_number", "").strip()
    order_id = extracted_fields.get("order_id", "").strip()
    payment_terms = extracted_fields.get("payment_terms", "").strip()

    # Security rule
    if security_flags:
        invoice_status = "Needs Review"
        review_reasons.extend(security_flags)

    # Required finance fields
    if not vendor_name:
        invoice_status = "Needs Review"
        review_reasons.append("Vendor name is missing")

    if not invoice_number:
        invoice_status = "Needs Review"
        review_reasons.append("Invoice number is missing")

    if not invoice_date:
        invoice_status = "Needs Review"
        review_reasons.append("Invoice date is missing")

    if not total_amount_text:
        invoice_status = "Needs Review"
        review_reasons.append("Total amount is missing")

    # Due date/payment terms can be important for AP workflow
    if not due_date:
        invoice_status = "Needs Review"
        review_reasons.append("Due date is missing")

    if not payment_terms:
        invoice_status = "Needs Review"
        review_reasons.append("Payment terms are missing")

    # PO/order reference rule
    if not po_number and not order_id:
        invoice_status = "Needs Review"
        review_reasons.append("Both PO number and order ID are missing")

    if not po_number and order_id:
        review_reasons.append("PO number is missing, but order ID is available")

    # Vendor validation placeholder
    if vendor_name and vendor_name not in TRUSTED_VENDORS:
        invoice_status = "Needs Review"
        review_reasons.append("Vendor is not found in trusted vendor list")

    # Amount validation and manager approval rule
    parsed_amount = parse_amount(total_amount_text)

    if total_amount_text and parsed_amount is None:
        invoice_status = "Needs Review"
        review_reasons.append("Total amount format is invalid")

    if parsed_amount is not None and parsed_amount > Decimal("10000"):
        invoice_status = "Pending Manager Approval"
        review_reasons.append("Invoice amount is greater than $10,000")

    return {
        "invoice_status": invoice_status,
        "review_reasons": review_reasons,
        "parsed_total_amount": str(parsed_amount) if parsed_amount is not None else "",
    }