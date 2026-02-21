import os
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from app.config import EMBEDDING_MODEL, VECTOR_STORE_PATH
import re

embedding_model = SentenceTransformer(EMBEDDING_MODEL)

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODEL_NAME = "meta-llama/llama-3.1-8b-instruct"


def build_vector_store(documents):
    embeddings = embedding_model.encode(documents)
    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings))

    os.makedirs("vector_store", exist_ok=True)
    faiss.write_index(index, VECTOR_STORE_PATH)


def load_vector_store():
    return faiss.read_index(VECTOR_STORE_PATH)


def retrieve_context(query: str, documents, top_k=2):
    index = load_vector_store()
    query_embedding = embedding_model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)

    return [documents[i] for i in indices[0]]


def extract_required_skills_from_context(context: str):
    prompt = f"""
Extract required technical skills from the job description below.

Return ONLY a JSON array of skill names.

Example:
["Python", "RAG", "AWS"]

Do NOT include explanations.
Do NOT use markdown.

Job Description:
{context}
"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "Return ONLY a raw JSON array of skill names."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
    )

    raw_output = response.choices[0].message.content

    if not raw_output:
        raise RuntimeError("Skill extraction model returned empty response.")

    raw_output = raw_output.strip()

    # Remove markdown fences if present
    raw_output = re.sub(r"```json|```", "", raw_output).strip()

    # Extract JSON array
    start = raw_output.find("[")
    end = raw_output.rfind("]")

    if start == -1 or end == -1:
        raise RuntimeError(f"No JSON array detected in output:\n{raw_output}")

    json_string = raw_output[start:end+1]

    return json.loads(json_string)