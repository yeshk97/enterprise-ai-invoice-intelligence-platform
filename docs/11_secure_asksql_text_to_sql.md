# Secure AskSQL / Text-to-SQL Module

## Overview

The AskSQL module allows users to ask questions about processed invoice records using natural language.

Instead of manually writing SQL, users can ask questions such as:

- Which invoices need review?
- Which invoices are pending manager approval?
- List duplicate invoices.
- Show invoices from a specific vendor.

The system converts the natural language question into a SQL query, validates the SQL for safety, executes only approved read-only queries, and returns the results to the user.

## Architecture

```text
User Question
    ↓
Streamlit Frontend
    ↓
FastAPI /ask-sql Endpoint
    ↓
Gemini LLM Generates Candidate SQL
    ↓
SQL Guardrail Service Validates Query
    ↓
Only Safe SELECT Queries Execute
    ↓
SQLite Database Returns Rows
    ↓
Streamlit Displays SQL + Results