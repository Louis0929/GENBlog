from __future__ import annotations

from typing import Any

from .generator import validate_blog_post


JsonDict = dict[str, Any]


def evaluate_article(post: JsonDict, brief: JsonDict, *, max_retries: int = 2) -> JsonDict:
    """Return pass/fail, score, and a deterministic auto-revision package."""

    issues = validate_blog_post(post, brief)
    scores = {
        "information_gain": _information_gain_score(post, brief),
        "claim_accuracy": _claim_accuracy_score(post, brief),
        "compliance": _compliance_score(post, brief),
    }
    weighted_score = round(
        scores["information_gain"] * 0.4 + scores["claim_accuracy"] * 0.4 + scores["compliance"] * 0.2,
        3,
    )
    revision_reasons = [_classify_issue(issue) for issue in issues]
    retry_plan = {
        "max_retries": max_retries,
        "should_retry": bool(issues) and max_retries > 0,
        "revision_reasons": revision_reasons,
        "revision_context": {
            "target_keyword": brief["job"]["target_keyword"],
            "blocked_fields": sorted({reason["field"] for reason in revision_reasons}),
            "preserve_facts": True,
        },
        "revision_prompt": _revision_prompt(issues, post, brief) if issues and max_retries > 0 else "",
    }
    return {
        "passed": not issues,
        "issues": issues,
        "scores": scores,
        "weighted_score": weighted_score,
        "retry_plan": retry_plan,
    }


def _information_gain_score(post: JsonDict, brief: JsonDict) -> float:
    html = post.get("html_content", "").lower()
    required_terms = ["realistic bonus roi", "expected net bonus value", "deposit requirements"]
    hits = sum(1 for term in required_terms if term in html)
    insight_hits = sum(
        1
        for insight in brief["information_gain"].get("computed_insights", [])
        if insight.split(".")[0].lower() in html
    )
    total = len(required_terms) + len(brief["information_gain"].get("computed_insights", []))
    return round((hits + insight_hits) / total, 3) if total else 1.0


def _claim_accuracy_score(post: JsonDict, brief: JsonDict) -> float:
    html = post.get("html_content", "")
    expected_urls = []
    for row in brief["information_gain"].get("comparison_table", []):
        expected_urls.extend(row.get("source_urls", []))
    unique_urls = [url for url in dict.fromkeys(expected_urls) if url]
    if not unique_urls:
        return 1.0
    hits = sum(1 for url in unique_urls if url in html or url in post.get("schema_markup", ""))
    return round(hits / len(unique_urls), 3)


def _compliance_score(post: JsonDict, brief: JsonDict) -> float:
    disclaimer = brief["job"].get("compliance_disclaimer", "")
    haystack = f"{post.get('html_content', '')}\n{post.get('compliance_disclaimer', '')}".lower()
    checks = [
        "not financial advice" in haystack,
        brief["job"].get("region", "").lower() in haystack,
        bool(disclaimer) and disclaimer[:40].lower() in haystack,
    ]
    return round(sum(1 for item in checks if item) / len(checks), 3)


def _revision_prompt(issues: list[str], post: JsonDict, brief: JsonDict) -> str:
    return (
        "Revise the BlogPostStructure JSON. Preserve all campaign facts exactly; do not change bonus, fee, region, "
        "source URL, or computed insight values. Fix these editorial gate issues:\n"
        + "\n".join(f"- {issue}" for issue in issues)
        + "\n\nOriginal target keyword: "
        + brief["job"]["target_keyword"]
        + "\nCurrent h1_title: "
        + post.get("h1_title", "")
    )


def _classify_issue(issue: str) -> JsonDict:
    lower = issue.lower()
    if "forbidden phrase" in lower:
        return {"code": "style_violation", "field": "html_content", "message": issue}
    if "compliance" in lower or "financial advice" in lower:
        return {"code": "missing_compliance", "field": "compliance_disclaimer", "message": issue}
    if "schema" in lower or "json-ld" in lower:
        return {"code": "invalid_schema", "field": "schema_markup", "message": issue}
    if "source url" in lower or "unsupported claim" in lower:
        return {"code": "claim_accuracy", "field": "html_content", "message": issue}
    if "computed insight" in lower or "required section" in lower:
        return {"code": "information_gain_gap", "field": "html_content", "message": issue}
    return {"code": "editorial_gate_failure", "field": "unknown", "message": issue}
