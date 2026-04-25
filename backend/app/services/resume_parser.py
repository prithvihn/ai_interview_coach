import fitz  # PyMuPDF
import docx
import os


def parse_resume(file_path: str) -> str:
    """
    Parse a resume file (PDF or DOCX) and return plain text.
    Raises ValueError for unsupported file types.
    """
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".docx":
        return _parse_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def _parse_pdf(path: str) -> str:
    """Extract text from a PDF using PyMuPDF."""
    doc = fitz.open(path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text("text"))
    doc.close()
    return "\n".join(text_parts).strip()


def _parse_docx(path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs).strip()
