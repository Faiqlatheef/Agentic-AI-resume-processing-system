import os
import json
import uuid
from datetime import datetime

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text
)
from sqlalchemy.orm import declarative_base, sessionmaker


# ==========================================
# DATABASE LOCATION (database/candidatesdb.db)
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FOLDER = os.path.join(BASE_DIR, "database")

os.makedirs(DB_FOLDER, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DB_FOLDER, 'candidatesdb.db')}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# ==========================================
# Candidate Table
# ==========================================

class CandidateRecord(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)

    name = Column(String)
    email = Column(String)

    match_score = Column(Float)
    recommendation = Column(String)
    review_reason = Column(String)

    extracted_data = Column(Text)
    reasoning_logs = Column(Text)

    processing_time_ms = Column(Float)

    status = Column(String)

    created_at = Column(DateTime)
    completed_at = Column(DateTime)


# ==========================================
# DB INIT
# ==========================================

def init_db():
    Base.metadata.create_all(bind=engine)


# ==========================================
# TASK LIFECYCLE
# ==========================================

def create_task(source: str):
    db = SessionLocal()

    task_id = str(uuid.uuid4())

    task = CandidateRecord(
        task_id=task_id,
        status="processing",
        created_at=datetime.utcnow()
    )

    db.add(task)
    db.commit()
    db.close()

    return task_id


def update_task_failure(task_id: str, error_message: str):
    db = SessionLocal()

    record = db.query(CandidateRecord).filter(
        CandidateRecord.task_id == task_id
    ).first()

    if record:
        record.status = "failed"
        record.reasoning_logs = error_message
        record.completed_at = datetime.utcnow()
        db.commit()

    db.close()


def complete_task(
    task_id,
    name,
    email,
    match_score,
    recommendation,
    review_reason,
    extracted_data,
    reasoning_logs,
    processing_time_ms
):
    db = SessionLocal()

    record = db.query(CandidateRecord).filter(
        CandidateRecord.task_id == task_id
    ).first()

    if record:
        record.name = name
        record.email = email
        record.match_score = match_score
        record.recommendation = recommendation
        record.review_reason = review_reason
        record.extracted_data = json.dumps(extracted_data)
        record.reasoning_logs = json.dumps(reasoning_logs)
        record.processing_time_ms = processing_time_ms
        record.status = "completed"
        record.completed_at = datetime.utcnow()

        db.commit()

    db.close()


def get_task(task_id: str):
    db = SessionLocal()

    record = db.query(CandidateRecord).filter(
        CandidateRecord.task_id == task_id
    ).first()

    db.close()
    return record
