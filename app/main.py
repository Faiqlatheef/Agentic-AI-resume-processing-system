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
    update_task,
    get_task,
    save_candidate
)

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

        resume_text = extract_text_from_pdf(file_path)

        candidate = extract_candidate_data(resume_text)

        context_docs = retrieve_context("required skills", documents)
        combined_context = "\n".join(context_docs)
        required_skills = extract_required_skills_from_context(combined_context)

        match = compute_match(candidate, required_skills, MIN_EXPERIENCE)

        final_result = route_candidate(
            match,
            candidate.extraction_confidence
        )

        processing_time_ms = round((time.time() - start_time) * 1000, 2)

        reasoning_logs = json.dumps({
            "required_skills": required_skills,
            "match_score": final_result.match_score,
            "missing_skills": final_result.critical_skills_missing,
            "confidence": candidate.extraction_confidence,
            "recommendation": final_result.recommendation
        })

        save_candidate(
            task_id,
            candidate.candidate_name,
            candidate.email,
            final_result.match_score,
            final_result.recommendation,
            final_result.review_reason
        )

        update_task(
            task_id,
            status="completed",
            processing_time_ms=processing_time_ms,
            reasoning_logs=reasoning_logs
        )

    except Exception as e:
        update_task(
            task_id,
            status="failed",
            processing_time_ms=0,
            reasoning_logs=str(e)
        )

# ===================================
# TASK STATUS POLLING
# ===================================

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):

    task = get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": task.id,
        "status": task.status,
        "processing_time_ms": task.processing_time_ms,
        "reasoning_logs": task.reasoning_logs,
        "created_at": task.created_at,
        "completed_at": task.completed_at
    }


# ===================================
# DASHBOARD (UI)
# ===================================

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, status: str = None):

    from app.database import SessionLocal, CandidateRecord

    db = SessionLocal()
    query = db.query(CandidateRecord)

    if status:
        query = query.filter(CandidateRecord.recommendation == status)

    records = query.order_by(CandidateRecord.created_at.desc()).all()
    db.close()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "records": records,
        "selected_status": status
    })


# ===================================
# CSV EXPORT
# ===================================

@app.get("/export-csv")
def export_csv(status: str = None):

    from app.database import SessionLocal, CandidateRecord

    db = SessionLocal()
    query = db.query(CandidateRecord)

    if status:
        query = query.filter(CandidateRecord.recommendation == status)

    records = query.all()
    db.close()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Name",
        "Email",
        "Match Score",
        "Recommendation",
        "Review Reason",
        "Created At"
    ])

    for r in records:
        writer.writerow([
            r.name,
            r.email,
            r.match_score,
            r.recommendation,
            r.review_reason,
            r.created_at
        ])

    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=candidates.csv"
        }
    )