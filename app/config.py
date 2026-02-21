import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
VECTOR_STORE_PATH = str(BASE_DIR / "vector_store" / "faiss.index")

DB_FILE = BASE_DIR / "database" / "hr.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

DB_PATH = f"sqlite:///{DB_FILE}"

MATCH_THRESHOLD_SHORTLIST = 0.85
MATCH_THRESHOLD_REVIEW = 0.6
MIN_EXPERIENCE = 3