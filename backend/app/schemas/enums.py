from enum import Enum


class DocType(str, Enum):
    SIGNED_SOW = "SIGNED_SOW"
    DRAFT_SOW = "DRAFT_SOW"
    REQUIREMENTS_DOC = "REQUIREMENTS_DOC"
    UAT_PLAN = "UAT_PLAN"
    MEETING_TRANSCRIPT = "MEETING_TRANSCRIPT"
    CLIENT_EMAIL = "CLIENT_EMAIL"
    PROJECT_PLAN = "PROJECT_PLAN"
    CHANGE_ORDER = "CHANGE_ORDER"
    STATUS_REPORT = "STATUS_REPORT"
    UNKNOWN = "UNKNOWN"


class DocumentRole(str, Enum):
    TARGET = "target"
    REFERENCE = "reference"


class SourceOrigin(str, Enum):
    CLIENT = "client"
    INTERNAL = "internal"
    JOINT = "joint"
    UNKNOWN = "unknown"


class SourceStatus(str, Enum):
    SIGNED = "signed"
    APPROVED = "approved"
    DRAFT = "draft"
    INFORMAL = "informal"
    TRANSCRIPT = "transcript"
    UNKNOWN = "unknown"


class InferenceSource(str, Enum):
    USER = "user"
    INFERRED = "inferred"
    METADATA = "metadata"
    DEFAULT = "default"
    UNKNOWN = "unknown"


class FactCategory(str, Enum):
    SCOPE = "scope"
    OUT_OF_SCOPE = "outOfScope"
    REQUIREMENTS = "requirements"
    ACCEPTANCE_CRITERIA = "acceptanceCriteria"
    UAT_TESTS = "uatTests"
    DECISIONS = "decisions"
    DATES = "dates"
    RISKS = "risks"
    CLIENT_REQUESTS = "clientRequests"
    RESPONSIBILITIES = "responsibilities"
    DELIVERABLES = "deliverables"
    ASSUMPTIONS = "assumptions"
    DEPENDENCIES = "dependencies"
    STAKEHOLDERS = "stakeholders"
    OPEN_QUESTIONS = "openQuestions"
    SYSTEMS = "systems"
    CHANGE_REQUESTS = "changeRequests"
    STATUS_UPDATES = "statusUpdates"


class ReliabilityFlag(str, Enum):
    LOW_DOC_TYPE_CONFIDENCE = "LOW_DOC_TYPE_CONFIDENCE"
    LOW_ORIGIN_CONFIDENCE = "LOW_ORIGIN_CONFIDENCE"
    LOW_STATUS_CONFIDENCE = "LOW_STATUS_CONFIDENCE"
    AMBIGUOUS_DECISION_LANGUAGE = "AMBIGUOUS_DECISION_LANGUAGE"
    NO_EXPLICIT_APPROVAL = "NO_EXPLICIT_APPROVAL"
    POSSIBLY_STALE = "POSSIBLY_STALE"
    MISSING_EXPECTED_CONTENT = "MISSING_EXPECTED_CONTENT"
    INTERNAL_CONFLICTS = "INTERNAL_CONFLICTS"
    UNKNOWN_SOURCE = "UNKNOWN_SOURCE"
    DRAFT_SOURCE = "DRAFT_SOURCE"
    INFORMAL_SOURCE = "INFORMAL_SOURCE"
    UNCLEAR_SPEAKER_ATTRIBUTION = "UNCLEAR_SPEAKER_ATTRIBUTION"
    USER_LABEL_CONFLICTS_WITH_CONTENT = "USER_LABEL_CONFLICTS_WITH_CONTENT"


class TargetQualityFlag(str, Enum):
    MISSING_EXPECTED_CONTENT = "MISSING_EXPECTED_CONTENT"
    UNKNOWN_TARGET_TYPE = "UNKNOWN_TARGET_TYPE"
    LOW_DOC_TYPE_CONFIDENCE = "LOW_DOC_TYPE_CONFIDENCE"
    UNSTRUCTURED_DOCUMENT = "UNSTRUCTURED_DOCUMENT"
    MISSING_SECTION_HEADINGS = "MISSING_SECTION_HEADINGS"
    TARGET_TYPE_NOT_ELIGIBLE = "TARGET_TYPE_NOT_ELIGIBLE"


class FactType(str, Enum):
    SCOPE_ITEM = "scope_item"
    OUT_OF_SCOPE_ITEM = "out_of_scope_item"
    REQUIREMENT = "requirement"
    ACCEPTANCE_CRITERIA = "acceptance_criteria"
    UAT_TEST = "uat_test"
    DELIVERABLE = "deliverable"
    DATE = "date"
    ASSUMPTION = "assumption"
    DEPENDENCY = "dependency"
    CLIENT_RESPONSIBILITY = "client_responsibility"
    TEAM_RESPONSIBILITY = "team_responsibility"
    DECISION = "decision"
    CLIENT_REQUEST = "client_request"
    CHANGE_REQUEST = "change_request"
    RISK = "risk"
    OPEN_QUESTION = "open_question"
    STAKEHOLDER = "stakeholder"
    SYSTEM_OR_INTEGRATION = "system_or_integration"
    STATUS_UPDATE = "status_update"
    MILESTONE = "milestone"


class FactStatus(str, Enum):
    CONFIRMED = "confirmed"
    APPROVED = "approved"
    SIGNED = "signed"
    PROPOSED = "proposed"
    REQUESTED = "requested"
    TENTATIVE = "tentative"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    UNKNOWN = "unknown"


class FactPolarity(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class DateType(str, Enum):
    KICKOFF = "kickoff"
    GO_LIVE = "go_live"
    UAT_START = "uat_start"
    UAT_END = "uat_end"
    DELIVERY_DEADLINE = "delivery_deadline"
    MILESTONE = "milestone"
    APPROVAL = "approval"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DependencyType(str, Enum):
    CLIENT = "client"
    INTERNAL = "internal"
    THIRD_PARTY = "third_party"
    TECHNICAL = "technical"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LintFindingType(str, Enum):
    MISSING_EXPECTED_CONTENT = "missing_expected_content"
    UNSUPPORTED_TARGET_CLAIM = "unsupported_target_claim"
    REFERENCE_CONTRADICTION = "reference_contradiction"
    UNRESOLVED_REFERENCE_CONFLICT = "unresolved_reference_conflict"
    STATUS_AUTHORITY_MISMATCH = "status_authority_mismatch"
    VAGUE_REQUIREMENT = "vague_requirement"
    MISSING_ACCEPTANCE_CRITERIA = "missing_acceptance_criteria"
    MISSING_OWNER = "missing_owner"
    MISSING_DATE_VALUE = "missing_date_value"
    UAT_TEST_MISSING_EXPECTED_RESULT = "uat_test_missing_expected_result"
    UAT_COVERAGE_GAP = "uat_coverage_gap"


class LintSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewPriority(str, Enum):
    NEEDS_FIX = "needs_fix"
    NEEDS_REVIEW = "needs_review"
    QUALITY_SUGGESTION = "quality_suggestion"
    INFO = "info"


class ClusterResolutionStatus(str, Enum):
    UNRESOLVED = "unresolved"
    CONFLICT = "conflict"
    CONSISTENT = "consistent"
