"""Helpers for reading uploaded document files."""

import io
from pathlib import PurePosixPath

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 512_000
MAX_UPLOAD_CHARS = 120_000


def _is_pdf(filename: str) -> bool:
    return PurePosixPath(filename).suffix.lower() == ".pdf"


def _read_pdf_as_markdown(content: bytes, filename: str) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise HTTPException(
            status_code=500,
            detail="PDF uploads require markitdown to be installed.",
        ) from exc

    converter = MarkItDown()
    result = converter.convert_stream(io.BytesIO(content), file_extension=".pdf")
    text = (result.text_content or "").strip()
    if not text:
        raise HTTPException(
            status_code=400,
            detail=f"Could not extract text from PDF {filename!r}.",
        )
    return text


def _read_text_bytes(content: bytes, filename: str) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(
        status_code=400,
        detail=f"Could not decode {filename!r} as text. Upload .txt, .md, or .pdf files.",
    )


async def read_upload_as_text(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename!r} exceeds maximum size of {MAX_UPLOAD_BYTES} bytes",
        )

    if _is_pdf(file.filename):
        text = _read_pdf_as_markdown(content, file.filename)
    else:
        text = _read_text_bytes(content, file.filename)

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"File {file.filename!r} is empty")

    if len(text) > MAX_UPLOAD_CHARS:
        text = text[:MAX_UPLOAD_CHARS]

    return file.filename, text
