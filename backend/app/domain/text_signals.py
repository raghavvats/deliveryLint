"""Deterministic text parsing helpers for lint rules."""

from __future__ import annotations

import re

PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
COUNT_RE = re.compile(
    r"\b(?:up to|maximum|max|at least|no more than)\s+(\d+)\b",
    re.IGNORECASE,
)
DOLLAR_RE = re.compile(r"\$[\d,]+(?:\.\d+)?|\b(\d+)\s*dollars?\b", re.IGNORECASE)
REQ_ID_RE = re.compile(r"\b((?:REQ|UAT|RET|CO|CR)-[A-Z0-9-]+)\b", re.IGNORECASE)

RELATIVE_DATE_MARKERS = (
    "week of",
    "early ",
    "late ",
    "before ",
    "after ",
    "soon",
    "as needed",
    "mid-",
    "end of",
    "beginning of",
    "q1",
    "q2",
    "q3",
    "q4",
)

UAT_EXECUTION_MARKERS = (
    "uat execution",
    "executes uat",
    "execute uat",
    "own uat",
    "runs uat",
    "run uat",
    "lead uat",
)

CHANGE_CONTROL_INFORMAL_TERMS = (
    "backlog",
    "sprint",
    "project team",
    "verbal",
    "informal",
    "weekly check-in",
    "weekly check in",
    "check-ins",
    "check ins",
    "without a formal",
    "without formal",
)

CHANGE_CONTROL_FORMAL_TERMS = (
    "signed",
    "written change",
    "change order",
    "change request",
    "executive sponsor",
    "engagement manager",
    "both parties",
)

GENERIC_AC_PHRASES = (
    "all required",
    "work properly",
    "as expected",
    "successfully",
    "without issue",
    "meets requirements",
    "functions correctly",
)


def extract_percentages(text: str) -> set[str]:
    return {match.group(1) for match in PERCENT_RE.finditer(text)}


def extract_counts(text: str) -> set[str]:
    counts = {match.group(1) for match in COUNT_RE.finditer(text)}
    for match in re.finditer(r"\bup to (\d+)\b", text, flags=re.IGNORECASE):
        counts.add(match.group(1))
    for match in re.finditer(r"\b(\d+)\s+(?:users|user)\b", text, flags=re.IGNORECASE):
        counts.add(match.group(1))
    return counts


def extract_dollar_amounts(text: str) -> set[str]:
    amounts: set[str] = set()
    for match in DOLLAR_RE.finditer(text):
        value = match.group(0) if match.group(0).startswith("$") else match.group(1)
        digits = re.sub(r"[^\d]", "", value)
        if digits:
            amounts.add(digits)
    return amounts


def extract_requirement_ids(text: str) -> set[str]:
    return {match.group(1).upper() for match in REQ_ID_RE.finditer(text)}


def has_relative_date_language(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in RELATIVE_DATE_MARKERS)


def mentions_uat_execution(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in UAT_EXECUTION_MARKERS)


def has_informal_change_control_language(text: str) -> bool:
    lowered = text.lower()
    if any(
        term in lowered
        for term in (
            "without a formal",
            "without formal",
            "without a signed",
            "without signed",
        )
    ):
        return True
    has_informal = any(term in lowered for term in CHANGE_CONTROL_INFORMAL_TERMS)
    has_formal = any(term in lowered for term in CHANGE_CONTROL_FORMAL_TERMS)
    return has_informal and not has_formal


def is_generic_acceptance_criteria(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in GENERIC_AC_PHRASES)


def claims_no_open_questions(text: str) -> bool:
    lowered = text.strip().lower()
    return lowered in {"none", "none.", "n/a", "no open questions", "no open question"}
