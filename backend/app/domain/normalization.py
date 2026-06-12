"""Subject normalization helpers."""

import re


def fallback_normalized_subject(subject: str) -> str:
    cleaned = subject.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unknown_subject"
