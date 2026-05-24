import requests
import streamlit as st


# FastAPI backend URL
BACKEND_URL = "http://127.0.0.1:8000"


st.set_page_config(
    page_title="Enterprise AI Invoice Intelligence Platform",
    page_icon="🧾",
    layout="wide",
)


st.title("🧾 Enterprise AI Invoice Intelligence Platform")
st.write(
    "Upload invoice PDFs, extract invoice fields using AI, validate business rules, "
    "and review processed invoices."
)


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

if st.button("Process Invoice"):
    if uploaded_file is None:
        st.error("Please upload a PDF invoice first.")
    else:
        with st.spinner("Processing invoice..."):
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

            st.subheader("Invoice Status")
            st.write(result.get("invoice_status"))

            st.subheader("Review Reasons")
            review_reasons = result.get("review_reasons", [])
            if review_reasons:
                for reason in review_reasons:
                    st.warning(reason)
            else:
                st.success("No review reasons found.")

            st.subheader("AI Extracted Fields")
            st.json(result.get("ai_extracted_fields", {}))

            st.subheader("Extracted Text Preview")
            st.text_area(
                "PDF Text Preview",
                result.get("extracted_text_preview", ""),
                height=250,
            )

            st.subheader("Saved Invoice Metadata")
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

if st.button("Refresh Invoice History"):
    response = requests.get(
        f"{BACKEND_URL}/invoices",
        timeout=30,
    )

    if response.status_code == 200:
        data = response.json()
        invoices = data.get("invoices", [])

        st.write(f"Total invoices: {data.get('count', 0)}")

        if invoices:
            st.dataframe(invoices)
        else:
            st.info("No invoices found yet.")
    else:
        st.error("Failed to fetch invoice history.")
        st.write(response.text)