from backend.app.services.lint_engine.rules.claim_classification import (
    run_claim_classification_rules,
)
from backend.app.services.lint_engine.rules.completeness import run_completeness_rules
from backend.app.services.lint_engine.rules.contradictions import run_contradiction_rules
from backend.app.services.lint_engine.rules.rubric_quality import run_rubric_quality_rules

RULE_MODULES = [
    run_completeness_rules,
    run_claim_classification_rules,
    run_contradiction_rules,
    run_rubric_quality_rules,
]
