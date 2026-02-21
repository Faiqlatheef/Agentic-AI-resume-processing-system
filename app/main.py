import os
import time
import asyncio
import json

from fastapi import FastAPI, UploadFile, File, Request, Header, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from io import StringIO
import csv

from app.pdf_parser import extract_text_from_pdf
from app.extraction import extract_candidate_data
from app.rag import (
    build_vector_store,
    retrieve_context,
    extract_required_skills_from_context
)
from app.matcher import compute_match
from app.router import route_candidate
from app.config import MIN_EXPERIENCE
from app.database import (
    init_db,
    create_task,
    complete_task,
    update_task_failure,
    get_task
)
from app.database import get_task as get_task_from_db
# -----------------------------------
# App Initialization
# -----------------------------------

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

init_db()

# -----------------------------------
# Load RAG Documents at Startup
# -----------------------------------

with open("data/job_description.txt") as f:
    job_doc = f.read()

with open("data/hiring_policy.txt") as f:
    policy_doc = f.read()

documents = [job_doc, policy_doc]
build_vector_store(documents)


# ===================================
# WEBHOOK ENDPOINT (Async Processing)
# ===================================

@app.post("/webhook/resume")
async def resume_webhook(file: UploadFile = File(...), source: str = "external"):

    task_id = create_task(source)

    # Read file BEFORE leaving request lifecycle
    file_bytes = await file.read()
    filename = file.filename

    asyncio.create_task(
        process_resume(task_id, file_bytes, filename)
    )

    return {
        "task_id": task_id,
        "status": "processing"
    }


# ===================================
# BACKGROUND PROCESSOR
# ===================================

async def process_resume(task_id: str, file_bytes: bytes, filename: str):

    start_time = time.time()

    try:
        os.makedirs("temp", exist_ok=True)

        file_path = f"temp/{task_id}_{filename}"

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Extract resume text
        resume_text = extract_text_from_pdf(file_path)

        # Structured extraction
        candidate = extract_candidate_data(resume_text)

        # RAG retrieval
        context_docs = retrieve_context("required skills", documents)
        combined_context = "\n".join(context_docs)
        required_skills = extract_required_skills_from_context(combined_context)

        # Matching logic
        match = compute_match(candidate, required_skills, MIN_EXPERIENCE)

        final_result = route_candidate(
            match,
            candidate.extraction_confidence
        )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        # Structured reasoning logs
        reasoning_logs = {
            "required_skills": required_skills,
            "match_score": final_result.match_score,
            "missing_skills": final_result.critical_skills_missing,
            "confidence": candidate.extraction_confidence,
            "recommendation": final_result.recommendation
        }

        # ✅ COMPLETE TASK (Correct Call)
        complete_task(
            task_id=task_id,
            name=candidate.candidate_name,
            email=candidate.email,
            match_score=final_result.match_score,
            recommendation=final_result.recommendation,
            review_reason=getattr(final_result, "review_reason", ""),
            extracted_data=candidate.dict(),
            reasoning_logs=reasoning_logs,
            processing_time_ms=processing_time_ms
        )

    except Exception as e:
        update_task_failure(task_id, str(e))

# ===================================
# TASK STATUS POLLING
# ===================================

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):

    task = get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Parse stored JSON fields safely
    extracted_data = None
    reasoning_logs = None

    try:
        if task.extracted_data:
            extracted_data = json.loads(task.extracted_data)
    except:
        extracted_data = task.extracted_data

    try:
        if task.reasoning_logs:
            reasoning_logs = json.loads(task.reasoning_logs)
    except:
        reasoning_logs = task.reasoning_logs

    return {
        "task_id": task.task_id,
        "status": task.status,
        "processing_time_ms": task.processing_time_ms,
        "extracted_data": extracted_data,
        "reasoning_logs": reasoning_logs,
        "match_score": task.match_score,
        "recommendation": task.recommendation,
        "review_reason": task.review_reason,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    }


# ===================================
# DASHBOARD (UI)
# ===================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, status: str = None):

    from app.database import SessionLocal, CandidateRecord
    import json

    db = SessionLocal()
    query = db.query(CandidateRecord)

    # Filtering logic
    if status and status != "All":
        query = query.filter(CandidateRecord.recommendation == status)

    records = query.order_by(CandidateRecord.created_at.desc()).all()

    # Parse reasoning logs
    for r in records:
        try:
            r.parsed_logs = json.loads(r.reasoning_logs) if r.reasoning_logs else {}
        except:
            r.parsed_logs = {}

    db.close()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "records": records,
            "selected_status": status or "All"
        }
    )


# ===================================
# CSV EXPORT
# ===================================

from fastapi.responses import StreamingResponse
from io import StringIO
import csv


@app.get("/export-csv")
def export_csv(status: str = None):

    from app.database import SessionLocal, CandidateRecord

    db = SessionLocal()
    query = db.query(CandidateRecord)

    # Allow filtering by processing status OR recommendation
    if status:
        if status in ["processing", "completed", "failed"]:
            query = query.filter(CandidateRecord.status == status)
        else:
            query = query.filter(CandidateRecord.recommendation == status)

    records = query.order_by(CandidateRecord.created_at.desc()).all()
    db.close()

    output = StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Task ID",
        "Name",
        "Email",
        "Match Score",
        "Recommendation",
        "Status",
        "Review Reason",
        "Processing Time (ms)",
        "Created At",
        "Completed At"
    ])

    # Rows
    for r in records:
        writer.writerow([
            r.task_id,
            r.name,
            r.email,
            r.match_score,
            r.recommendation,
            r.status,
            r.review_reason,
            r.processing_time_ms,
            r.created_at,
            r.completed_at
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=candidates_export.csv"
        }
    )
