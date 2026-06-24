import io
from unittest.mock import patch

import pytest
from fastapi import HTTPException, UploadFile

from backend.app.services.upload import read_upload_as_text


def _upload_file(filename: str, content: bytes) -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


@pytest.mark.asyncio
async def test_read_upload_as_text_decodes_utf8() -> None:
    filename, text = await read_upload_as_text(_upload_file("doc.md", b"# Hello\n"))
    assert filename == "doc.md"
    assert text == "# Hello"


@pytest.mark.asyncio
async def test_read_upload_as_text_rejects_empty_file() -> None:
    with pytest.raises(HTTPException, match="is empty"):
        await read_upload_as_text(_upload_file("empty.txt", b"   "))


@pytest.mark.asyncio
async def test_read_upload_as_text_converts_pdf() -> None:
    with patch(
        "backend.app.services.upload._read_pdf_as_markdown",
        return_value="# Converted from PDF\n\nSome content.",
    ):
        filename, text = await read_upload_as_text(_upload_file("scope.pdf", b"%PDF-1.4"))

    assert filename == "scope.pdf"
    assert "Converted from PDF" in text


@pytest.mark.asyncio
async def test_read_upload_as_text_rejects_empty_pdf() -> None:
    with patch("backend.app.services.upload._read_pdf_as_markdown", side_effect=HTTPException(status_code=400, detail="Could not extract text from PDF 'empty.pdf'.")):
        with pytest.raises(HTTPException, match="Could not extract text"):
            await read_upload_as_text(_upload_file("empty.pdf", b"%PDF"))
