"""Helpers for reading uploaded document files."""

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 512_000
MAX_UPLOAD_CHARS = 120_000


async def read_upload_as_text(file: UploadFile) -> tuple[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file must have a filename")

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File {file.filename!r} exceeds maximum size of {MAX_UPLOAD_BYTES} bytes",
        )

    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Could not decode {file.filename!r} as text. Upload .txt or .md files.",
        )

    text = text.strip()
    if not text:
        raise HTTPException(status_code=400, detail=f"File {file.filename!r} is empty")

    if len(text) > MAX_UPLOAD_CHARS:
        text = text[:MAX_UPLOAD_CHARS]

    return file.filename, text
