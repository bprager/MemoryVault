from __future__ import annotations

from .models import EvaluationCheck, EvaluationReport, ExpectedItem, ResumePacket, Scenario


def evaluate_resume_packet(scenario: Scenario, packet: ResumePacket) -> EvaluationReport:
    checks: list[EvaluationCheck] = []

    for expected in scenario.expected_items:
        haystack = _category_text(packet, expected)
        normalized = haystack.lower()
        missing_keywords = [keyword for keyword in expected.keywords if keyword.lower() not in normalized]
        passed = not missing_keywords
        details = "matched expected keywords" if passed else f"missing: {', '.join(missing_keywords)}"
        checks.append(
            EvaluationCheck(
                name=expected.name,
                category=expected.category,
                passed=passed,
                details=details,
                expected_keywords=expected.keywords,
            )
        )

    score = 0.0
    if checks:
        score = sum(1 for check in checks if check.passed) / len(checks)

    missing_categories = sorted({check.category for check in checks if not check.passed})
    improvement_actions = [
        _improvement_message(check)
        for check in checks
        if not check.passed
    ]

    return EvaluationReport(
        run_id=packet.run_id,
        scenario_id=scenario.scenario_id,
        score=score,
        checks=checks,
        improvement_actions=improvement_actions,
        missing_categories=missing_categories,
    )


def _category_text(packet: ResumePacket, expected: ExpectedItem) -> str:
    if expected.category == "goal":
        return packet.final_goal_guard
    if expected.category == "current_focus":
        return "\n".join(packet.current_focus)
    if expected.category == "constraint":
        return "\n".join(packet.constraints)
    if expected.category == "decision":
        return "\n".join(packet.decisions)
    if expected.category == "blocker":
        return "\n".join(packet.blockers)
    if expected.category == "assumption":
        return "\n".join(packet.assumptions)
    if expected.category == "recent_failures":
        return "\n".join(packet.recent_failures)
    if expected.category == "lesson":
        return "\n".join(packet.lessons)
    if expected.category == "open_question":
        return "\n".join(packet.open_questions)
    if expected.category == "source":
        return "\n".join(packet.sources)
    return ""


def _improvement_message(check: EvaluationCheck) -> str:
    missing = ", ".join(check.expected_keywords)
    return (
        f"Capture {check.category} more reliably for `{check.name}`; "
        f"expected to retain: {missing}."
    )
