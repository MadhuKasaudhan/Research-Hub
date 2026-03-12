"""ResearchHub AI - Paper service for file handling and text processing."""

import os
import uuid
import logging
from pathlib import Path

import aiofiles
from fastapi import UploadFile

logger = logging.getLogger(__name__)

UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")

MIME_TYPE_MAP: dict[str, str] = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".txt": "text/plain",
}


def get_mime_type(filename: str) -> str:
    """Map a filename's extension to its MIME type.

    Args:
        filename: The filename (or path) to inspect.

    Returns:
        The MIME type string, or 'application/octet-stream' if unknown.
    """
    ext = Path(filename).suffix.lower()
    return MIME_TYPE_MAP.get(ext, "application/octet-stream")


async def save_uploaded_file(
    file: UploadFile, workspace_id: str, upload_dir: str = UPLOAD_DIR
) -> tuple[str, int]:
    """Save an uploaded file to disk asynchronously.

    Generates a UUID-based filename while preserving the original extension.
    Creates the workspace subdirectory if it doesn't exist.

    Args:
        file: The uploaded file from FastAPI.
        workspace_id: The workspace this file belongs to.
        upload_dir: Base upload directory path.

    Returns:
        A tuple of (file_path, file_size).
    """
    original_name = file.filename or "upload"
    ext = Path(original_name).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{ext}"

    workspace_dir = os.path.join(upload_dir, workspace_id)
    os.makedirs(workspace_dir, exist_ok=True)

    file_path = os.path.join(workspace_dir, unique_filename)

    file_size = 0
    async with aiofiles.open(file_path, "wb") as out_file:
        while True:
            chunk = await file.read(1024 * 64)  # 64KB chunks
            if not chunk:
                break
            await out_file.write(chunk)
            file_size += len(chunk)

    return file_path, file_size


def extract_text_from_pdf(file_path: str) -> list[str]:
    """Extract text from a PDF file using PyPDF2.

    Args:
        file_path: Path to the PDF file on disk.

    Returns:
        A list of strings, one per page.
    """
    try:
        from PyPDF2 import PdfReader

        reader = PdfReader(file_path)
        pages: list[str] = []
        for page in reader.pages:
            text = page.extract_text()
            pages.append(text if text else "")
        return pages
    except Exception as e:
        logger.error("Failed to extract text from PDF %s: %s", file_path, e)
        return []


def extract_text_from_docx(file_path: str) -> list[str]:
    """Extract text from a DOCX file using python-docx.

    Args:
        file_path: Path to the DOCX file on disk.

    Returns:
        A list of paragraph text strings.
    """
    try:
        from docx import Document

        doc = Document(file_path)
        paragraphs: list[str] = [p.text for p in doc.paragraphs if p.text.strip()]
        return paragraphs
    except Exception as e:
        logger.error("Failed to extract text from DOCX %s: %s", file_path, e)
        return []


def extract_text_from_txt(file_path: str) -> list[str]:
    """Read a plain text file and split into page-sized segments.

    Splits the file content into segments of approximately 3000 characters
    to emulate page boundaries.

    Args:
        file_path: Path to the text file on disk.

    Returns:
        A list of text segments.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        page_size = 3000
        pages: list[str] = []
        for i in range(0, len(content), page_size):
            segment = content[i : i + page_size]
            if segment:
                pages.append(segment)

        return pages if pages else [""]
    except Exception as e:
        logger.error("Failed to read text file %s: %s", file_path, e)
        return []


def chunk_text(
    pages: list[str], chunk_size: int = 800, overlap: int = 150
) -> list[str]:
    """Split pages of text into overlapping chunks.

    Joins all pages together, then splits into chunks of approximately
    ``chunk_size`` characters with ``overlap`` characters of overlap between
    consecutive chunks.

    Args:
        pages: List of page text strings to chunk.
        chunk_size: Target size for each chunk in characters.
        overlap: Number of overlapping characters between consecutive chunks.

    Returns:
        A list of chunk strings.
    """
    full_text = "\n".join(pages)
    if not full_text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_length = len(full_text)

    while start < text_length:
        end = start + chunk_size
        chunk = full_text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        # Advance by chunk_size minus overlap so successive chunks share text
        start += chunk_size - overlap
        if start >= text_length:
            break

    return chunks
