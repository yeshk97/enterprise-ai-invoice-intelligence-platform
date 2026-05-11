# AI Product Lifecycle v1

## Project Name

Enterprise AI Invoice Intelligence Platform

---

## Purpose

This document explains how the Enterprise AI Invoice Intelligence Platform follows both traditional Software Development Life Cycle (SDLC) and modern AI Product Lifecycle practices.

The goal is to build the project like a real enterprise AI product, not just a demo.

---

## 1. Why AI Product Lifecycle Matters

Traditional software products are usually built using:

```text
Requirements → Design → Development → Testing → Deployment → Maintenance

AI products need additional steps because AI behavior is probabilistic, data-dependent, and must be evaluated continuously.

AI systems require:

Data understanding
Prompt design
Model selection
Retrieval design
Evaluation datasets
Human feedback
Monitoring
Token and cost tracking
Guardrails
Continuous improvement
2. Traditional SDLC Mapping
2.1 Requirements

In this phase, we define:

Product vision
Problem statement
Business requirements
Functional requirements
User stories
Acceptance criteria

Project artifacts:

docs/01_product_vision.md
docs/02_problem_statement.md
docs/03_brd.md
docs/04_frd.md
docs/05_user_stories.md
docs/06_acceptance_criteria.md
2.2 Design

In this phase, we design:

System architecture
Database schema
API structure
AI architecture
Security architecture
Deployment architecture

Project artifacts:

architecture/system_architecture_v1.md
architecture/database_design_v1.md
architecture/production_architecture_v1.md
2.3 Development

In this phase, we build:

FastAPI backend
Streamlit frontend
Invoice upload
Database models
Business rules
AI extraction
RAG
Agents
Dashboards
2.4 Testing

In this phase, we test:

APIs
Business rules
Database operations
AI extraction
RAG answers
Prompt injection handling
User workflows
2.5 Deployment

In this phase, we prepare:

Docker containers
CI/CD pipeline
Cloud deployment
Load balancer
Environment variables
Secrets management
2.6 Maintenance

In this phase, we monitor:

Errors
Logs
User feedback
AI failures
Token usage
Cost
Latency
Model quality
3. AI Product Lifecycle Mapping
Phase 1: Problem Scoping
Goal

Clearly define the business problem before choosing AI tools.

In This Project

Problem:

Enterprises receive invoices from multiple sources and manually process them into finance systems, causing delays, errors, duplicate payments, approval bottlenecks, and audit risks.

Output
Clear problem statement
Target users
Business goals
Success metrics
Phase 2: Data Understanding
Goal

Understand what type of data the system will handle.

In This Project

Data types include:

PDF invoices
Scanned invoices
Handwritten invoices
Email attachments
Vendor portal downloads
SaaS exports
ERP exports
Vendor master records
Approval logs
Audit logs
Key Questions
Is the invoice digital or scanned?
Does it contain text or image?
Is the vendor known?
Are required fields present?
Is OCR confidence high or low?
Is the document safe from prompt injection?
Phase 3: Baseline System
Goal

Build a simple working version before adding advanced AI.

In This Project

Initial baseline:

Upload invoice
Select source
Save uploaded file
Store invoice metadata
Display uploaded invoices
Why This Matters

We should not jump directly to agents or advanced RAG. A stable baseline helps us build layer by layer.

Phase 4: AI Approach Selection
Goal

Decide where AI is needed and where normal code is better.

In This Project

Use normal Python rules for deterministic logic:

Amount threshold
Vendor status
Duplicate invoice check
Vendor inactivity > 30 days
Missing PO number
Role-based access

Use AI for unstructured or ambiguous tasks:

Reading messy invoice text
Extracting structured fields
Understanding handwritten/scanned documents
Summarizing reasons
RAG-based question answering
Agentic workflow recommendations
Core Principle
AI extracts and reasons.
Python validates and controls.
Humans approve risky decisions.
Phase 5: Prompt and Context Engineering
Goal

Design high-quality prompts and context carefully.

In This Project

Prompt engineering includes:

Invoice extraction prompt
Validation explanation prompt
RAG answer prompt
Prompt injection guardrail prompt

Context engineering includes:

Selecting only relevant invoice text
Including vendor data when needed
Including business rules when needed
Avoiding unnecessary context
Avoiding secrets in prompts
Keeping token usage low
Why This Matters

Good AI systems do not just send everything to the LLM. They carefully choose what context the model needs.

Phase 6: OCR and Document Intelligence
Goal

Extract text and structure from documents before using LLMs.

In This Project

The pipeline should be:

Invoice PDF/Image
↓
OCR or PDF text extraction
↓
Extracted text, tables, and confidence scores
↓
LLM structured extraction
↓
Pydantic validation
↓
Business rules
↓
Human review if needed
Why This Matters

OCR reduces unnecessary LLM usage and provides confidence scores. LLMs should not be the first tool for every document-processing task.

Phase 7: Structured AI Extraction
Goal

Convert unstructured invoice text into structured data.

In This Project

Expected structured output:

{
  "vendor_name": "FedEx",
  "invoice_number": "INV-1001",
  "invoice_date": "2026-05-01",
  "due_date": "2026-05-30",
  "total_amount": 12500.00,
  "currency": "USD",
  "po_number": "PO-8891"
}
Validation

Structured output should be validated using Pydantic before storing it.

Phase 8: RAG Design
Goal

Allow users to ask questions over invoice data and documents.

In This Project

RAG flow:

User question
↓
Retrieve relevant invoice data / document chunks
↓
Build context
↓
LLM generates answer
↓
Return answer with supporting context
Concepts Covered
Chunking
Chunk overlap
Embeddings
Vector database
Retrieval
Context window
Token optimization
RAG evaluation
Phase 9: GraphRAG Design
Goal

Support relationship-based questions using graph structures.

In This Project

Graph entities:

Vendor
Invoice
User
Source
Business Rule
Risk Flag
Approval

Graph relationships:

Vendor submits Invoice
Invoice triggers Business Rule
Invoice comes from Source
User uploads Invoice
Manager approves Invoice
Invoice has Risk Flag
Example Question
Which vendors repeatedly triggered manager approval and why?

GraphRAG helps answer this because it can follow relationships between vendors, invoices, rules, and approvals.

Phase 10: Agentic AI Design
Goal

Use agents only after the core workflow is stable.

In This Project

Possible agents:

Document Classifier Agent
Extraction Review Agent
Validation Review Agent
Approval Recommendation Agent
Explanation Agent
Important Rule

Agents should not bypass deterministic rules or security controls.

Agents support:

Reasoning
Explanation
Workflow orchestration
Recommendations

Python/backend controls:

Permissions
Database access
Final approvals
Business rules
Security enforcement
Phase 11: Evaluation-Driven Development
Goal

Measure AI quality continuously.

In This Project

Evaluate:

Invoice extraction accuracy
OCR confidence
Vendor validation correctness
Business rule correctness
RAG answer quality
Agent recommendation correctness
Prompt injection detection
Token usage
Cost
Latency
Example

Expected:

{
  "vendor_name": "FedEx",
  "total_amount": 12500.00
}

AI output:

{
  "vendor_name": "FedEx",
  "total_amount": 12500.00
}

Result:

Pass
Phase 12: Security and Guardrails
Goal

Protect the system from unsafe AI behavior.

In This Project

Guardrails include:

Prompt injection detection
No secrets passed to LLM
Input filtering
Output filtering
RBAC enforcement
Tool permission checks
Audit logs
Human approval for high-risk actions
Phase 13: Human-in-the-Loop
Goal

Allow humans to review risky or uncertain AI outputs.

In This Project

Human review is required when:

OCR confidence is low
AI extraction confidence is low
Vendor is unknown
Vendor is inactive or blocked
Invoice amount is high
Vendor inactivity is more than 30 days
Duplicate invoice is detected
Prompt injection is detected
Phase 14: Deployment and Productionization
Goal

Make the system reliable and usable outside local development.

In This Project

Production concepts include:

Docker image
Docker container
CI/CD pipeline
Cloud deployment
Load balancer
Managed database
Object storage
Secrets manager
Monitoring
Phase 15: Monitoring and Continuous Improvement
Goal

Improve the system after deployment.

In This Project

Monitor:

API failures
Processing failures
LLM latency
Token usage
AI cost
Extraction quality
RAG quality
Prompt injection attempts
Human correction rate
Approval turnaround time

Use feedback to improve:

Prompts
Rules
RAG retrieval
Agent workflow
Model selection
UI experience

4. Final Lifecycle Summary

This project follows:

Problem Scoping
→ Requirements
→ Data Understanding
→ System Design
→ Baseline App
→ AI Integration
→ Evaluation
→ Security
→ Human Review
→ Deployment
→ Monitoring
→ Continuous Improvement

## 5. Project Principle

The guiding principle for this project is:

Build a working system first.
Add AI where it creates value.
Measure AI behavior.
Secure the system.
Improve continuously.

## 6. Interview Explanation

I followed a combined SDLC and AI Product Lifecycle approach. I started with the business problem, created product and requirement documents, designed the system architecture, and planned the AI components separately. For AI, I focused on data understanding, structured extraction, RAG, agentic workflows, evaluation, token tracking, guardrails, and human-in-the-loop review. This approach helps make the project production-oriented rather than just a simple AI demo.