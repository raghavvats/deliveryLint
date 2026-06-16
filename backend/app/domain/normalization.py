"""Subject normalization helpers."""

import re

# Section-title markers that indicate the content beneath them is explicitly
# *excluded* work rather than committed scope.
OUT_OF_SCOPE_SECTION_MARKERS = (
    "out of scope",
    "out-of-scope",
    "outofscope",
    "exclusion",
    "excluded",
    "not in scope",
    "not in-scope",
)


def fallback_normalized_subject(subject: str) -> str:
    cleaned = subject.strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "unknown_subject"


def is_out_of_scope_section(section_title: str | None) -> bool:
    """True when a section heading marks its contents as out of scope/excluded.

    Used to preserve claim polarity from headings: an item listed under "Out of
    Scope" must not be treated as included scope even if the extractor labelled it
    with positive polarity.
    """
    if not section_title:
        return False
    lowered = section_title.lower()
    return any(marker in lowered for marker in OUT_OF_SCOPE_SECTION_MARKERS)
