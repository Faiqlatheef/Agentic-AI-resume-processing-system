import os
import json
import re
from openai import OpenAI
from app.schemas import CandidateExtraction


# -----------------------------
# OpenRouter Client Setup
# -----------------------------
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

MODEL_NAME = "meta-llama/llama-3.1-8b-instruct"


# -----------------------------
# Utility: Clean Model Output
# -----------------------------
def clean_model_output(text: str) -> str:
    """
    Cleans common LLM formatting issues:
    - Removes markdown fences
    - Extracts first JSON object
    """
    text = text.strip()

    # Remove markdown fences if present
    text = re.sub(r"```json|```", "", text).strip()

    # Extract first valid JSON block
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("No JSON object found in model output.")

    return text[start:end + 1]

def normalize_extraction_schema(data: dict) -> dict:
    """
    Normalizes model output to match CandidateExtraction schema.
    """

    # Normalize previous_roles
    normalized_roles = []

    for role in data.get("previous_roles", []):
        normalized_roles.append({
            "role": role.get("role") or role.get("title") or "",
            "company": role.get("company") or "",
            "duration": role.get("duration") or role.get("dates") or ""
        })

    data["previous_roles"] = normalized_roles

    # Normalize education (optional safeguard)
    normalized_education = []
    for edu in data.get("education", []):
        normalized_education.append({
            "degree": edu.get("degree") or "",
            "institution": edu.get("institution") or edu.get("university") or "",
            "location": edu.get("location") or "",
            "gpa": edu.get("gpa") or "",
            "graduation_date": edu.get("graduation_date") or edu.get("year") or "",
            "duration": edu.get("duration") or ""
        })

    data["education"] = normalized_education

    return data

# -----------------------------
# Main Extraction Function
# -----------------------------
def extract_candidate_data(resume_text: str) -> CandidateExtraction:
    """
    Extracts structured candidate data from resume text using LLM.
    Includes retry with JSON correction logic.
    """

    base_prompt = f"""
You are an expert HR data extraction agent.

Extract structured data from the resume below.

Return ONLY strict valid JSON in this format:

{{
    "candidate_name": "",
    "email": "",
    "phone": "",
    "years_of_experience": number,
    "skills": [],
    "education": [],
    "previous_roles": [],
    "extraction_confidence": number between 0 and 1
}}

STRICT RULES:
- Output must be valid JSON.
- All strings must be quoted.
- Year ranges must be strings (example: "2011-2016").
- Do NOT include explanations.
- Do NOT use markdown.
- Do NOT wrap in code fences.

Resume:
{resume_text}
"""

    raw_output = ""

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Return ONLY strict valid JSON."
                    },
                    {
                        "role": "user",
                        "content": base_prompt
                    }
                ],
                temperature=0.1,
            )

            raw_output = response.choices[0].message.content

            if not raw_output:
                raise ValueError("Model returned empty response.")

            # Clean output
            cleaned_output = clean_model_output(raw_output)

            # Parse JSON
            data = json.loads(cleaned_output)
            data = normalize_extraction_schema(data)

            # Validate using Pydantic schema
            return CandidateExtraction(**data)

        except Exception as e:
            if attempt == 0:
                # Retry with correction prompt
                base_prompt = f"""
The previous output was invalid JSON.

Fix it and return ONLY strict valid JSON.
Do not include explanations.
Do not use markdown.

Previous output:
{raw_output}
"""
            else:
                raise RuntimeError(
                    f"Extraction failed after retry.\n\nRaw model output:\n{raw_output}\n\nError: {str(e)}"
                )