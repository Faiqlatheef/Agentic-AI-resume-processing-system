import pdfplumber


def extract_text_from_pdf(file_path: str) -> str:
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""

    if not text.strip():
        raise ValueError("No extractable text found.")

    return text