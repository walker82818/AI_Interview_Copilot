from pathlib import Path

import fitz

from src.core.config import settings


def extract_text_from_pdf(file_path: str | Path) -> str:
    path = Path(file_path)
    doc = fitz.open(path)
    try:
        return "\n".join(page.get_text() for page in doc)
    finally:
        doc.close()


def extract_text_from_txt(file_path: str | Path) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="ignore")


def parse_document(file_path: str | Path) -> str:
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(path)
    if suffix in {".txt", ".md"}:
        return extract_text_from_txt(path)
    raise ValueError(f"Unsupported file type: {suffix}")
