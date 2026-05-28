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
    "detect duplicates, and review processed invoices."
)


# ------------------------------------------------------------
# Helper function: fetch invoice history
# ------------------------------------------------------------
def fetch_invoice_history() -> list[dict]:
    """
    Fetch all processed invoices from FastAPI backend.
    """

    try:
        response = requests.get(
            f"{BACKEND_URL}/invoices",
            timeout=30,
        )

        if response.status_code == 200:
            return response.json().get("invoices", [])

        st.error("Failed to fetch invoice history.")
        st.write(response.text)
        return []

    except requests.exceptions.RequestException as error:
        st.error("Could not connect to backend API.")
        st.write(str(error))
        return []


# ------------------------------------------------------------
# Helper function: process one invoice
# ------------------------------------------------------------
def process_single_invoice(uploaded_file, source_type: str) -> dict:
    """
    Send one uploaded invoice PDF to FastAPI backend for processing.
    """

    files = {
        "file": (
            uploaded_file.name,
            uploaded_file.getvalue(),
            "application/pdf",
        )
    }

    data = {
        "source_type": source_type,
    }

    response = requests.post(
        f"{BACKEND_URL}/invoices/upload",
        files=files,
        data=data,
        timeout=120,
    )

    if response.status_code == 200:
        return response.json()

    return {
        "status": "failed",
        "original_file_name": uploaded_file.name,
        "error": response.text,
    }


# ------------------------------------------------------------
# Upload section
# ------------------------------------------------------------
st.header("Upload Invoice")

uploaded_files = st.file_uploader(
    "Choose invoice PDF files",
    type=["pdf"],
    accept_multiple_files=True,
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
    if not uploaded_files:
        st.error("Please upload at least one PDF invoice first.")
    else:
        batch_results = []

        progress_bar = st.progress(0)
        status_placeholder = st.empty()

        total_files = len(uploaded_files)

        for index, uploaded_file in enumerate(uploaded_files, start=1):
            status_placeholder.info(
                f"Processing {index} of {total_files}: {uploaded_file.name}"
            )

            try:
                result = process_single_invoice(
                    uploaded_file=uploaded_file,
                    source_type=source_type,
                )
                batch_results.append(result)

            except requests.exceptions.RequestException as error:
                batch_results.append(
                    {
                        "status": "failed",
                        "original_file_name": uploaded_file.name,
                        "error": str(error),
                    }
                )

            progress_bar.progress(index / total_files)

        status_placeholder.success("Batch processing completed!")

        successful_results = [
            result for result in batch_results if result.get("status") == "success"
        ]
        failed_results = [
            result for result in batch_results if result.get("status") == "failed"
        ]

        st.success(
            f"Processed {len(successful_results)} invoice(s). "
            f"Failed: {len(failed_results)}."
        )

        # ------------------------------------------------------------
        # Batch summary table
        # ------------------------------------------------------------
        st.subheader("Batch Processing Summary")

        summary_rows = []

        for result in batch_results:
            extracted_fields = result.get("ai_extracted_fields", {})

            summary_rows.append(
                {
                    "File Name": result.get("original_file_name"),
                    "Invoice ID": result.get("invoice_id"),
                    "Vendor": extracted_fields.get("vendor_name", ""),
                    "Invoice #": extracted_fields.get("invoice_number", ""),
                    "Amount": extracted_fields.get("total_amount", ""),
                    "Status": result.get("invoice_status", result.get("status")),
                    "Duplicate Type": result.get("duplicate_type", ""),
                    "Duplicate Invoice ID": result.get("duplicate_invoice_id", ""),
                    "Error": result.get("error", ""),
                }
            )

        st.dataframe(
            summary_rows,
            use_container_width=True,
            hide_index=True,
        )

        # ------------------------------------------------------------
        # Detailed result display
        # ------------------------------------------------------------
        st.subheader("Detailed Results")

        for result in batch_results:
            file_name = result.get("original_file_name", "Unknown file")

            with st.expander(f"Result: {file_name}", expanded=False):
                if result.get("status") == "failed":
                    st.error("Processing failed.")
                    st.write(result.get("error", "Unknown error"))
                    continue

                invoice_id = result.get("invoice_id")
                invoice_status = result.get("invoice_status", "Unknown")
                parsed_amount = result.get("parsed_total_amount", "")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Invoice ID", invoice_id)

                with col2:
                    st.metric("Status", invoice_status)

                with col3:
                    st.metric("Parsed Amount", parsed_amount)

                duplicate_type = result.get("duplicate_type")
                duplicate_invoice_id = result.get("duplicate_invoice_id")

                if duplicate_type:
                    st.warning(
                        f"Duplicate detected: {duplicate_type}. "
                        f"Existing invoice ID: {duplicate_invoice_id}"
                    )

                st.markdown("#### Review Reasons")

                review_reasons = result.get("review_reasons", [])

                if review_reasons:
                    for reason in review_reasons:
                        st.warning(reason)
                else:
                    st.success("No review reasons found.")

                st.markdown("#### AI Extracted Fields")
                st.json(result.get("ai_extracted_fields", {}))

                with st.expander("Extracted Text Preview"):
                    st.text_area(
                        "PDF Text Preview",
                        result.get("extracted_text_preview", ""),
                        height=250,
                        key=f"text_preview_{invoice_id}_{file_name}",
                    )

                with st.expander("Saved Invoice Metadata"):
                    st.json(
                        {
                            "invoice_id": result.get("invoice_id"),
                            "original_file_name": result.get("original_file_name"),
                            "stored_file_name": result.get("stored_file_name"),
                            "source_type": result.get("source_type"),
                            "saved_path": result.get("saved_path"),
                            "duplicate_type": result.get("duplicate_type"),
                            "duplicate_invoice_id": result.get("duplicate_invoice_id"),
                            "parsed_total_amount": result.get("parsed_total_amount"),
                        }
                    )


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
    1
    for invoice in invoices
    if invoice.get("invoice_status") == "Pending Manager Approval"
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