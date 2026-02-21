# Agentic AI Resume Processing System

An end-to-end **Agentic AI system** that simulates email-based resume
intake, performs structured extraction, validates using RAG, and routes
candidates automatically based on hiring policy.

Built with: - FastAPI - OpenRouter (LLM) - FAISS (Vector Store) -
SQLAlchemy (SQLite) - Async Background Processing

------------------------------------------------------------------------

## 🚀 Overview

This system simulates a real-world recruitment automation workflow:

1.  Webhook Intake -- Receives resume via HTTP POST (simulating email
    attachment forwarding)
2.  Structured Extraction -- Extracts candidate data as JSON
3.  RAG Validation -- Retrieves hiring policy & job requirements from
    vector store
4.  Scoring & Routing -- Computes match score and decision
5.  Persistence & Auditability -- Stores reasoning logs, timestamps, and
    decision
6.  Dashboard UI -- Displays processed candidates

------------------------------------------------------------------------

## 🏗 Architecture

Email Provider (Simulated)\
↓\
Webhook Endpoint (/webhook/resume)\
↓\
Background Agent\
├── LLM Extraction\
├── RAG Retrieval (FAISS)\
├── Skill Matching\
├── Experience Validation\
└── Decision Routing\
↓\
Database (SQLite)\
↓\
Dashboard UI

The system is asynchronous and event-driven.\
Webhook returns immediately with a `task_id`, and processing happens in
the background.

------------------------------------------------------------------------

## 📌 Core Features

### Email Intake Simulation

-   Webhook endpoint accepts resume file
-   Returns task ID immediately
-   Designed to integrate with SendGrid / Mailgun webhooks

### Structured Extraction

Extracts: - Candidate information - Skills - Education - Previous
roles - Experience duration

Handles imperfect resume formatting.

### RAG-Driven Validation

-   Loads hiring policy and job description into FAISS vector store
-   Dynamically retrieves required skills
-   Prevents hardcoded business rules
-   Grounds decision-making in policy documents

### Intelligent Routing

Candidates are routed to: - Shortlisted - Human Review - Rejected

Based on: - Skill alignment - Experience requirement - Critical skill
gaps

### Observability & Reliability

-   Task ID tracking
-   Status polling endpoint
-   Processing latency tracking
-   Structured reasoning logs storage
-   Failure handling with retry logic

### Product-Grade UI

-   Upload page
-   Dashboard view
-   Status filtering
-   CSV export
-   Timestamp display
-   Processing time display

------------------------------------------------------------------------

## 📦 Installation

git clone `<repo-url>`{=html}\
cd resume-agent

python -m venv venv\
venv`\Scripts`{=tex}`\activate  `{=tex}

pip install -r requirements.txt

Set environment variable:

setx OPENROUTER_API_KEY "your_api_key_here"

Run the server:

uvicorn app.main:app --reload

------------------------------------------------------------------------

## 🌐 Usage

### Send Resume via Webhook

POST to:

/webhook/resume

Response:

{ "task_id": "uuid", "status": "processing" }

------------------------------------------------------------------------

### Check Processing Status

GET /tasks/{task_id}

Returns: - Status - Match score - Recommendation - Reasoning logs -
Processing latency - Timestamps

------------------------------------------------------------------------

### View Dashboard

http://127.0.0.1:8000/dashboard

Displays: - Candidate name - Email - Match score - Status -
Recommendation - Timestamp - Processing time

------------------------------------------------------------------------

## 🧠 RAG Knowledge Base

Documents embedded: - Hiring Policy - Agentic AI Engineer Job
Description

Vectorized using FAISS and sentence-transformers.

RAG ensures: - Required skills are dynamically retrieved - Experience
thresholds are validated - Decisions are grounded in policy context

------------------------------------------------------------------------

## 🔍 Decision Logic

High skill match + sufficient experience → Shortlisted\
Moderate skill match → Human Review\
Critical skill missing OR experience gap → Rejected

All decisions are stored with reasoning logs for transparency and
auditability.

------------------------------------------------------------------------

## 🛡 Failure Handling

-   Extraction retry mechanism
-   Tasks marked as failed on exception
-   Errors stored in reasoning logs
-   Webhook designed for safe retries

------------------------------------------------------------------------

## 🎥 Demo Coverage

Screen recording demonstrates: - Three resumes processed - Shortlisted
case - Human Review case - Rejected case - Real-time dashboard updates

------------------------------------------------------------------------

## 🎯 Assessment Coverage

Email intake ✔\
Structured extraction ✔\
RAG validation ✔\
Intelligent routing ✔\
Persistence ✔\
Human review handling ✔\
Error handling ✔

------------------------------------------------------------------------

## 👤 Author

Abdul Latheef Faiq Ahamed\
Software Engineer -- AI & Data Science
