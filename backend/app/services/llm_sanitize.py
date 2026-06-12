"""Coerce LLM JSON payloads before strict Pydantic validation."""

from enum import Enum
from typing import Any, Union, get_args, get_origin

from pydantic import BaseModel

FACT_CATEGORY_ALIASES: dict[str, str] = {
    "roles": "responsibilities",
    "role": "responsibilities",
    "out_of_scope": "outOfScope",
    "out-of-scope": "outOfScope",
    "acceptance_criteria": "acceptanceCriteria",
    "uat_tests": "uatTests",
    "uat": "uatTests",
    "client_requests": "clientRequests",
    "change_requests": "changeRequests",
    "open_questions": "openQuestions",
    "status_updates": "statusUpdates",
}


def _is_enum_type(annotation: Any) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, Enum)


def _is_model_type(annotation: Any) -> bool:
    return isinstance(annotation, type) and issubclass(annotation, BaseModel)


def _unwrap_optional(annotation: Any) -> Any:
    origin = get_origin(annotation)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def _enum_values(enum_cls: type[Enum]) -> set[str]:
    return {member.value for member in enum_cls}


def _unknown_enum_value(enum_cls: type[Enum]) -> str | None:
    for member in enum_cls:
        if member.name == "UNKNOWN" or member.value == "unknown":
            return member.value
    return None


def _coerce_enum_value(value: Any, enum_cls: type[Enum]) -> Any:
    if value is None:
        return None
    if not isinstance(value, str):
        return value

    valid = _enum_values(enum_cls)
    if value in valid:
        return value

    normalized = value.strip()
    if normalized in valid:
        return normalized

    lowered = normalized.lower().replace(" ", "_")
    alias = FACT_CATEGORY_ALIASES.get(lowered)
    if alias and alias in valid:
        return alias

    for candidate in valid:
        if candidate.lower() == normalized.lower():
            return candidate

    return _unknown_enum_value(enum_cls)


def _coerce_value(value: Any, annotation: Any) -> Any:
    annotation = _unwrap_optional(annotation)
    origin = get_origin(annotation)

    if origin is list:
        item_type = get_args(annotation)[0]
        if not isinstance(value, list):
            return value
        if _is_enum_type(item_type):
            coerced = [_coerce_enum_value(item, item_type) for item in value]
            return [item for item in coerced if item is not None]
        if _is_model_type(item_type):
            return [
                coerce_llm_payload(item, item_type)
                for item in value
                if isinstance(item, dict)
            ]
        return [_coerce_value(item, item_type) for item in value]

    if _is_enum_type(annotation):
        coerced = _coerce_enum_value(value, annotation)
        return coerced if coerced is not None else value

    if _is_model_type(annotation):
        if isinstance(value, dict):
            return coerce_llm_payload(value, annotation)
        return value

    return value


def coerce_llm_payload(data: Any, model: type[BaseModel]) -> Any:
    if not isinstance(data, dict):
        return data

    coerced: dict[str, Any] = {}
    for name, field in model.model_fields.items():
        if name not in data:
            continue
        coerced[name] = _coerce_value(data[name], field.annotation)
    return coerced
