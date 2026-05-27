import requests
import streamlit as st


# ------------------------------------------------------------
# Backend API configuration
# ------------------------------------------------------------
BACKEND_URL = "http://127.0.0.1:8000"


# ------------------------------------------------------------
# Streamlit page configuration
# ------------------------------------------------------------
st.set_page_config(
    page_title="Enterprise AI Invoice Intelligence Platform",
    page_icon="🧾",
    layout="wide",
)


st.title("🧾 Enterprise AI Invoice Intelligence Platform")
st.caption(
    "Upload invoice PDFs, extract invoice fields using AI, validate business rules, "
    "and review processed invoices."
)


# ------------------------------------------------------------
# Helper function to fetch invoice history
# ------------------------------------------------------------
def fetch_invoice_history():
    """
    Fetch processed invoice history from FastAPI backend.
    """

    response = requests.get(
        f"{BACKEND_URL}/invoices",
        timeout=30,
    )

    if response.status_code == 200:
        return response.json().get("invoices", [])

    return []


# ------------------------------------------------------------
# Upload section
# ------------------------------------------------------------
st.header("Upload Invoice")

uploaded_file = st.file_uploader(
    "Choose an invoice PDF",
    type=["pdf"],
)

source_type = st.selectbox(
    "Select invoice source",
    [
        "Manual Upload",
        "Email",
        "Vendor Portal",
        "SaaS Tool",
        "ERP Export",
    ],
)

if st.button("Process Invoice", type="primary"):
    if uploaded_file is None:
        st.error("Please upload a PDF invoice first.")
    else:
        with st.spinner("Processing invoice with AI..."):
            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    "application/pdf",
                )
            }

            data = {
                "source_type": source_type
            }

            response = requests.post(
                f"{BACKEND_URL}/invoices/upload",
                files=files,
                data=data,
                timeout=120,
            )

        if response.status_code == 200:
            result = response.json()

            st.success("Invoice processed successfully!")

            status = result.get("invoice_status", "Unknown")
            parsed_amount = result.get("parsed_total_amount", "")
            invoice_id = result.get("invoice_id", "")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Invoice ID", invoice_id)

            with col2:
                st.metric("Status", status)

            with col3:
                st.metric("Parsed Amount", parsed_amount)

            st.subheader("Review Reasons")
            review_reasons = result.get("review_reasons", [])

            if review_reasons:
                for reason in review_reasons:
                    st.warning(reason)
            else:
                st.success("No review reasons found.")

            st.subheader("AI Extracted Fields")
            st.json(result.get("ai_extracted_fields", {}))

            with st.expander("Extracted Text Preview"):
                st.text_area(
                    "PDF Text Preview",
                    result.get("extracted_text_preview", ""),
                    height=250,
                )

            with st.expander("Saved Invoice Metadata"):
                st.json(
                    {
                        "invoice_id": result.get("invoice_id"),
                        "original_file_name": result.get("original_file_name"),
                        "stored_file_name": result.get("stored_file_name"),
                        "source_type": result.get("source_type"),
                        "saved_path": result.get("saved_path"),
                        "parsed_total_amount": result.get("parsed_total_amount"),
                    }
                )

        else:
            st.error("Invoice processing failed.")
            st.write(response.text)


# ------------------------------------------------------------
# Invoice history section
# ------------------------------------------------------------
st.divider()
st.header("Processed Invoice History")

invoices = fetch_invoice_history()

total_invoices = len(invoices)
needs_review_count = sum(
    1 for invoice in invoices if invoice.get("invoice_status") == "Needs Review"
)
manager_approval_count = sum(
    1 for invoice in invoices if invoice.get("invoice_status") == "Pending Manager Approval"
)

metric_col1, metric_col2, metric_col3 = st.columns(3)

with metric_col1:
    st.metric("Total Invoices", total_invoices)

with metric_col2:
    st.metric("Needs Review", needs_review_count)

with metric_col3:
    st.metric("Pending Manager Approval", manager_approval_count)


if st.button("Refresh Invoice History"):
    invoices = fetch_invoice_history()


if invoices:
    display_rows = []

    for invoice in invoices:
        display_rows.append(
            {
                "ID": invoice.get("id"),
                "Vendor": invoice.get("vendor_name"),
                "Invoice #": invoice.get("invoice_number"),
                "Date": invoice.get("invoice_date"),
                "Amount": invoice.get("total_amount"),
                "Status": invoice.get("invoice_status"),
                "Source": invoice.get("source_type"),
                "Created At": invoice.get("created_at"),
            }
        )

    st.dataframe(
        display_rows,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No invoices found yet.")