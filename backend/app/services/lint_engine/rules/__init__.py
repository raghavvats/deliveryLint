from backend.app.services.lint_engine.rules.completeness import run_completeness_rules
from backend.app.services.lint_engine.rules.contradictions import run_contradiction_rules
from backend.app.services.lint_engine.rules.grounding import run_grounding_rules
from backend.app.services.lint_engine.rules.rubric_quality import run_rubric_quality_rules
from backend.app.services.lint_engine.rules.status_authority import run_status_authority_rules

RULE_MODULES = [
    run_completeness_rules,
    run_grounding_rules,
    run_contradiction_rules,
    run_status_authority_rules,
    run_rubric_quality_rules,
]
