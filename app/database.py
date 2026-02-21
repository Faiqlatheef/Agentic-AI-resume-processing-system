from sqlalchemy import (
    create_engine, Column, Integer, String,
    Float, DateTime, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from app.config import DB_PATH
import uuid

engine = create_engine(DB_PATH, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class TaskRecord(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, default="pending")
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    processing_time_ms = Column(Float)
    reasoning_logs = Column(Text)


class CandidateRecord(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String)
    name = Column(String)
    email = Column(String)
    match_score = Column(Float)
    recommendation = Column(String)
    review_reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def create_task(source):
    db = SessionLocal()
    task_id = str(uuid.uuid4())
    task = TaskRecord(id=task_id, source=source)
    db.add(task)
    db.commit()
    db.close()
    return task_id


def update_task(task_id, status, processing_time_ms, reasoning_logs):
    db = SessionLocal()
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    task.status = status
    task.processing_time_ms = processing_time_ms
    task.reasoning_logs = reasoning_logs
    task.completed_at = datetime.utcnow()
    db.commit()
    db.close()


def get_task(task_id):
    db = SessionLocal()
    task = db.query(TaskRecord).filter(TaskRecord.id == task_id).first()
    db.close()
    return task


def save_candidate(task_id, name, email,
                   match_score, recommendation, review_reason):
    db = SessionLocal()
    record = CandidateRecord(
        task_id=task_id,
        name=name,
        email=email,
        match_score=match_score,
        recommendation=recommendation,
        review_reason=review_reason
    )
    db.add(record)
    db.commit()
    db.close()