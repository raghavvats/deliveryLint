"""Discover and load DeliveryLint test suites from testFiles/."""

from __future__ import annotations

import re
from pathlib import Path

from backend.app.schemas.enums import DocType, LintFindingType, SourceStatus
from backend.app.schemas.upload import ReferenceProfileHints, ReferenceUpload, UploadedDocument
from backend.app.test_harness.schemas import ExpectedFinding, TestSuiteDefinition

SUITE_DIR_PREFIX = "deliverylint_suite_"
ANSWER_KEY_FILENAME = "answer_key.md"
REFERENCES_DIRNAME = "references"

TARGET_LINE_RE = re.compile(r"^Target:\s+`([^`]+)`", re.MULTILINE)
TARGET_FILE_LINE_RE = re.compile(r"^Target file:\s+`([^`]+)`", re.MULTILINE)
TARGET_DOC_TYPE_RE = re.compile(r"^Target doc type:\s+`([^`]+)`", re.MULTILINE)
INJECTED_FINDING_RE = re.compile(
    r"^\d+\.\s+`([^`]+)`(?:\s+or\s+`([^`]+)`)?\s+[—-]\s+(.+)$",
    re.MULTILINE,
)

STOPWORDS = {
    "target",
    "signed",
    "reference",
    "references",
    "explicitly",
    "includes",
    "include",
    "included",
    "says",
    "said",
    "but",
    "only",
    "even",
    "though",
    "without",
    "requires",
    "require",
    "required",
    "approved",
    "draft",
    "meeting",
    "notes",
    "client",
    "email",
    "status",
    "report",
    "plan",
    "document",
    "concrete",
    "specific",
    "matching",
    "valid",
    "wrong",
    "empty",
    "generic",
    "lack",
    "lacks",
    "missing",
    "omit",
    "omits",
    "omitted",
    "uses",
    "used",
    "using",
    "treated",
    "appears",
    "lists",
    "list",
    "still",
    "already",
    "additional",
    "listed",
    "changes",
    "change",
    "order",
    "behavior",
    "successful",
    "supporting",
    "support",
    "supports",
    "supported",
    "conflicts",
    "conflict",
    "conflicting",
    "contradicts",
    "contradict",
    "contradiction",
    "mismatch",
    "informal",
    "request",
    "requested",
    "requests",
    "proposes",
    "proposed",
    "propose",
    "discuss",
    "discusses",
    "discussed",
    "decision",
    "decisions",
    "adopts",
    "adopted",
    "adopt",
    "idea",
    "threshold",
    "automatic",
    "approval",
    "approvals",
    "pending",
    "state",
    "verify",
    "verifies",
    "required",
    "details",
    "detail",
    "section",
    "sections",
    "content",
    "results",
    "result",
    "expected",
    "actual",
    "owner",
    "owners",
    "date",
    "dates",
    "timeline",
    "impact",
    "fee",
    "cost",
    "scope",
    "out",
    "within",
    "minutes",
    "users",
    "user",
    "training",
    "admin",
    "production",
    "configuration",
    "integration",
    "integrations",
    "real",
    "time",
    "nightly",
    "export",
    "synchronization",
    "sync",
    "sprint",
    "complete",
    "go",
    "live",
    "execution",
    "coordinates",
    "coordination",
    "credentials",
    "control",
    "written",
    "before",
    "work",
    "begins",
    "weekly",
    "check",
    "checkin",
    "performance",
    "experience",
    "intuitive",
    "needed",
    "motions",
    "criteria",
    "acceptance",
    "dependencies",
    "dependency",
    "delays",
    "minor",
    "absorbed",
    "push",
    "validation",
    "efficiently",
    "efficient",
    "soon",
    "early",
    "launch",
    "window",
    "instead",
    "from",
    "than",
    "greater",
    "above",
    "below",
    "less",
    "more",
    "like",
    "similar",
    "because",
    "there",
    "their",
    "they",
    "them",
    "this",
    "that",
    "these",
    "those",
    "with",
    "have",
    "has",
    "had",
    "were",
    "was",
    "been",
    "being",
    "will",
    "would",
    "could",
    "should",
    "must",
    "also",
    "when",
    "where",
    "while",
    "into",
    "onto",
    "upon",
    "after",
    "during",
    "current",
    "phase",
    "phase1",
    "north",
    "america",
    "emea",
    "rollout",
    "templates",
    "template",
    "accessories",
    "guided",
    "selling",
    "treadmills",
    "bikes",
    "rowers",
    "discount",
    "explore",
    "change",
    "yet",
    "weakens",
    "allowing",
    "allow",
    "allows",
    "weaker",
    "weaken",
    "weakened",
    "weakening",
    "weakened",
}


def get_test_files_root() -> Path:
    return Path(__file__).resolve().parents[3] / "testFiles"


def _parse_acceptable_types(primary: str, secondary: str | None) -> list[LintFindingType]:
    types: list[LintFindingType] = []
    for raw in (primary, secondary):
        if not raw:
            continue
        for token in re.split(r"\s+or\s+", raw.strip()):
            cleaned = token.strip().strip("`")
            if cleaned:
                types.append(LintFindingType(cleaned))
    return types


def parse_answer_key(text: str) -> tuple[str | None, DocType | None, list[ExpectedFinding]]:
    target_filename = None
    target_match = TARGET_LINE_RE.search(text)
    if target_match:
        target_filename = target_match.group(1)
    else:
        file_match = TARGET_FILE_LINE_RE.search(text)
        if file_match:
            target_filename = file_match.group(1)

    target_doc_type = None
    doc_type_match = TARGET_DOC_TYPE_RE.search(text)
    if doc_type_match:
        target_doc_type = DocType(doc_type_match.group(1))

    expected: list[ExpectedFinding] = []
    for index, match in enumerate(INJECTED_FINDING_RE.finditer(text), start=1):
        acceptable_types = _parse_acceptable_types(match.group(1), match.group(2))
        expected.append(
            ExpectedFinding(
                index=index,
                acceptable_types=acceptable_types,
                description=match.group(3).strip(),
            )
        )
    return target_filename, target_doc_type, expected


def _suite_title(directory_name: str) -> str:
    suffix = directory_name.removeprefix(SUITE_DIR_PREFIX)
    return suffix.replace("_", " ").strip()


def infer_reference_hints(filename: str) -> ReferenceProfileHints:
    lower = filename.lower()
    hints = ReferenceProfileHints()

    if "signed_sow" in lower:
        hints.user_provided_doc_type = DocType.SIGNED_SOW
        hints.user_provided_status = SourceStatus.SIGNED
    elif "meeting_notes" in lower or lower.startswith("meeting"):
        hints.user_provided_doc_type = DocType.MEETING_TRANSCRIPT
        hints.user_provided_status = SourceStatus.TRANSCRIPT
    elif "client_email" in lower:
        hints.user_provided_doc_type = DocType.CLIENT_EMAIL
        hints.user_provided_status = SourceStatus.INFORMAL
    elif "approved_requirements" in lower or (
        "requirements" in lower and "approved" in lower
    ):
        hints.user_provided_doc_type = DocType.REQUIREMENTS_DOC
        hints.user_provided_status = SourceStatus.APPROVED
    elif "requirements" in lower:
        hints.user_provided_doc_type = DocType.REQUIREMENTS_DOC
    elif "uat_plan" in lower:
        hints.user_provided_doc_type = DocType.UAT_PLAN
    elif "status_report" in lower:
        hints.user_provided_doc_type = DocType.STATUS_REPORT
    elif "project_plan" in lower:
        hints.user_provided_doc_type = DocType.PROJECT_PLAN
    elif "approved_change_order" in lower:
        hints.user_provided_doc_type = DocType.CHANGE_ORDER
        hints.user_provided_status = SourceStatus.APPROVED
    elif "draft_change_order" in lower or "change_order" in lower:
        hints.user_provided_doc_type = DocType.CHANGE_ORDER
        hints.user_provided_status = SourceStatus.DRAFT

    return hints


def _resolve_target_filename(suite_dir: Path, answer_key_text: str, readme_text: str) -> str:
    parsed_target, _, _ = parse_answer_key(answer_key_text)
    if parsed_target:
        return parsed_target

    readme_match = TARGET_FILE_LINE_RE.search(readme_text)
    if readme_match:
        return readme_match.group(1)

    candidates = sorted(path.name for path in suite_dir.glob("target_*.md"))
    if len(candidates) == 1:
        return candidates[0]
    if not candidates:
        msg = f"No target_*.md found in {suite_dir}"
        raise ValueError(msg)
    msg = f"Multiple target files in {suite_dir}; specify Target in answer_key.md"
    raise ValueError(msg)


def _resolve_target_doc_type(answer_key_text: str, readme_text: str) -> DocType:
    _, parsed_type, _ = parse_answer_key(answer_key_text)
    if parsed_type:
        return parsed_type

    readme_match = TARGET_DOC_TYPE_RE.search(readme_text)
    if readme_match:
        return DocType(readme_match.group(1))

    msg = "Could not determine target doc type from answer_key.md or README.md"
    raise ValueError(msg)


def load_suite_definition(suite_dir: Path) -> TestSuiteDefinition:
    answer_key_path = suite_dir / ANSWER_KEY_FILENAME
    readme_path = suite_dir / "README.md"
    if not answer_key_path.is_file():
        msg = f"Missing {ANSWER_KEY_FILENAME} in {suite_dir}"
        raise ValueError(msg)

    answer_key_text = answer_key_path.read_text(encoding="utf-8")
    readme_text = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    target_filename = _resolve_target_filename(suite_dir, answer_key_text, readme_text)
    target_doc_type = _resolve_target_doc_type(answer_key_text, readme_text)
    _, _, expected_findings = parse_answer_key(answer_key_text)

    references_dir = suite_dir / REFERENCES_DIRNAME
    reference_count = len(list(references_dir.glob("*.md"))) if references_dir.is_dir() else 0

    return TestSuiteDefinition(
        id=suite_dir.name,
        name=_suite_title(suite_dir.name),
        directory=str(suite_dir),
        target_filename=target_filename,
        target_doc_type=target_doc_type,
        expected_findings=expected_findings,
        reference_count=reference_count,
    )


def discover_suites(root: Path | None = None) -> list[TestSuiteDefinition]:
    root = root or get_test_files_root()
    if not root.is_dir():
        return []

    suites: list[TestSuiteDefinition] = []
    for child in sorted(root.iterdir()):
        if not child.is_dir() or not child.name.startswith(SUITE_DIR_PREFIX):
            continue
        suites.append(load_suite_definition(child))
    return suites


def load_suite_documents(suite: TestSuiteDefinition) -> tuple[UploadedDocument, list[ReferenceUpload]]:
    suite_dir = Path(suite.directory)
    target_path = suite_dir / suite.target_filename
    if not target_path.is_file():
        msg = f"Target file not found: {target_path}"
        raise FileNotFoundError(msg)

    target = UploadedDocument(
        filename=target_path.name,
        text=target_path.read_text(encoding="utf-8"),
    )

    references_dir = suite_dir / REFERENCES_DIRNAME
    references: list[ReferenceUpload] = []
    if references_dir.is_dir():
        for ref_path in sorted(references_dir.glob("*.md")):
            references.append(
                ReferenceUpload(
                    filename=ref_path.name,
                    text=ref_path.read_text(encoding="utf-8"),
                    profile_hints=infer_reference_hints(ref_path.name),
                )
            )
    return target, references


def extract_match_keywords(text: str) -> set[str]:
    keywords: set[str] = set()
    keywords.update(re.findall(r"\d{4}-\d{2}-\d{2}", text))
    keywords.update(re.findall(r"\b(?:REQ|UAT|RET|CO|CR)-[A-Z0-9-]+\b", text, flags=re.IGNORECASE))
    keywords.update(re.findall(r"\$[\d,]+(?:\.\d+)?|\b\d+(?:\.\d+)?%", text))
    keywords.update(re.findall(r"`([^`]+)`", text))
    keywords.update(re.findall(r"[“\"]([^”\"]{3,})[”\"]", text))

    for word in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", text):
        lowered = word.lower()
        if lowered not in STOPWORDS:
            keywords.add(lowered)
    return {item.strip().lower() for item in keywords if item.strip()}
