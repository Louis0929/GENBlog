from __future__ import annotations

from datetime import date
from typing import Any

from .contract import ComparisonBundle, JsonDict, PlatformBundle, ValidationIssue, ValidationReport


TOP_LEVEL_KEYS = {"platforms", "claims", "sources", "article_jobs", "editorial_rules"}

CLAIM_REQUIRED_FIELDS = {
    "signup_bonus": {
        "headline_offer",
        "headline_value_usdt",
        "realistic_value_usdt",
        "required_deposit_usdt",
        "required_trade_volume_usdt",
        "user_requirements",
        "eligible_regions",
    },
    "trading_fee": {"fee_type", "fee_value", "fee_display"},
    "fiat_onramp": {"rail", "availability", "fee_display", "fee_value", "region"},
    "regional_availability": {"region", "availability"},
    "benefit": {"benefit_type", "availability", "value_display", "requirement", "notes"},
}

RECOMMENDED_CLAIM_FIELDS = {"source_url", "claim_status", "valid_until"}


def validate_campaign(data: JsonDict) -> ValidationReport:
    issues: list[ValidationIssue] = []
    _validate_top_level(data, issues)

    platforms = data.get("platforms", [])
    claims = data.get("claims", [])
    sources = data.get("sources", [])
    jobs = data.get("article_jobs", [])
    rule_sets = data.get("editorial_rules", [])

    platform_ids = _unique_index(platforms, "platform_id", "platforms", issues)
    source_ids = _unique_index(sources, "source_id", "sources", issues)
    _unique_index(claims, "claim_id", "claims", issues)
    _unique_index(jobs, "job_id", "article_jobs", issues)
    _unique_index(rule_sets, "rule_set_id", "editorial_rules", issues)

    for index, platform in enumerate(platforms):
        _validate_platform(platform, index, issues)

    for index, source in enumerate(sources):
        _validate_source(source, index, issues)

    sources_by_id = {source["source_id"]: source for source in sources if "source_id" in source}
    for index, claim in enumerate(claims):
        _validate_claim(claim, index, platform_ids, source_ids, sources_by_id, issues)

    for index, job in enumerate(jobs):
        _validate_article_job(job, index, platform_ids, issues)

    for index, rules in enumerate(rule_sets):
        _validate_editorial_rules(rules, index, issues)

    return ValidationReport(issues)


def build_comparison_bundle(data: JsonDict, job_id: str) -> ComparisonBundle:
    report = validate_campaign(data)
    if not report.passed:
        formatted = "\n".join(f"{issue.path}: {issue.message}" for issue in report.errors())
        raise ValueError(f"Campaign data failed validation:\n{formatted}")

    platforms_by_id = {platform["platform_id"]: platform for platform in data["platforms"]}
    claims = data["claims"]
    sources_by_id = {source["source_id"]: source for source in data["sources"]}
    job = next((item for item in data["article_jobs"] if item["job_id"] == job_id), None)
    if not job:
        raise ValueError(f"Unknown job_id: {job_id}")

    rules = _find_editorial_rules(data, job["persona"])
    platform_ids = job["platform_ids"]
    return ComparisonBundle(
        job=job,
        platforms=[_build_platform_bundle(platform_id, platforms_by_id, claims, job) for platform_id in platform_ids],
        editorial_rules=rules,
        sources_by_id=sources_by_id,
    )


def _validate_top_level(data: JsonDict, issues: list[ValidationIssue]) -> None:
    for key in sorted(TOP_LEVEL_KEYS):
        if key not in data:
            _error(issues, key, "Missing required top-level collection.")
        elif not isinstance(data[key], list):
            _error(issues, key, "Top-level collection must be a list.")


def _validate_platform(platform: JsonDict, index: int, issues: list[ValidationIssue]) -> None:
    path = f"platforms[{index}]"
    required = {
        "platform_id",
        "name",
        "category",
        "tier",
        "target_regions",
        "supported_fiat_rails",
        "affiliate_program",
    }
    _require_fields(platform, required, path, issues)
    if not isinstance(platform.get("target_regions"), list) or not platform.get("target_regions"):
        _error(issues, f"{path}.target_regions", "Must be a non-empty list.")

    affiliate = platform.get("affiliate_program", {})
    _require_fields(
        affiliate,
        {"status", "affiliate_url", "commission_model", "commission_value", "source_url"},
        f"{path}.affiliate_program",
        issues,
    )
    if affiliate.get("status") == "active" and not affiliate.get("affiliate_url"):
        _error(issues, f"{path}.affiliate_program.affiliate_url", "Active affiliate program needs a URL.")


def _validate_source(source: JsonDict, index: int, issues: list[ValidationIssue]) -> None:
    path = f"sources[{index}]"
    _require_fields(
        source,
        {"source_id", "domain", "source_type", "credibility_score", "allowed_claim_types", "freshness_half_life_days"},
        path,
        issues,
    )
    _validate_number_range(source.get("credibility_score"), 0, 1, f"{path}.credibility_score", issues)
    if isinstance(source.get("freshness_half_life_days"), (int, float)) and source["freshness_half_life_days"] <= 0:
        _error(issues, f"{path}.freshness_half_life_days", "Must be greater than 0.")


def _validate_claim(
    claim: JsonDict,
    index: int,
    platform_ids: set[str],
    source_ids: set[str],
    sources_by_id: dict[str, JsonDict],
    issues: list[ValidationIssue],
) -> None:
    path = f"claims[{index}]"
    _require_fields(claim, {"claim_id", "platform_id", "claim_type", "source_id", "last_checked_at", "confidence"}, path, issues)
    claim_type = claim.get("claim_type")
    platform_id = claim.get("platform_id")
    source_id = claim.get("source_id")

    if platform_id and platform_id not in platform_ids:
        _error(issues, f"{path}.platform_id", f"Unknown platform_id: {platform_id}")
    if source_id and source_id not in source_ids:
        _error(issues, f"{path}.source_id", f"Unknown source_id: {source_id}")

    _validate_number_range(claim.get("confidence"), 0, 1, f"{path}.confidence", issues)

    for field in RECOMMENDED_CLAIM_FIELDS:
        if field not in claim:
            _warning(issues, f"{path}.{field}", "Recommended for claim audit and freshness checks.")

    if claim_type in CLAIM_REQUIRED_FIELDS:
        _require_fields(claim, CLAIM_REQUIRED_FIELDS[claim_type], path, issues)
    else:
        _warning(issues, f"{path}.claim_type", f"Unknown claim_type: {claim_type}")

    source = sources_by_id.get(source_id)
    if source and claim_type not in set(source.get("allowed_claim_types", [])):
        _error(issues, f"{path}.source_id", f"Source {source_id} does not allow claim_type {claim_type}.")

    if claim_type == "signup_bonus":
        realistic = claim.get("realistic_value_usdt")
        headline = claim.get("headline_value_usdt")
        if _is_number(realistic) and _is_number(headline) and realistic > headline:
            _error(issues, f"{path}.realistic_value_usdt", "Cannot exceed headline_value_usdt.")
        _validate_min(claim.get("required_deposit_usdt"), 0, f"{path}.required_deposit_usdt", issues)
        _validate_min(claim.get("required_trade_volume_usdt"), 0, f"{path}.required_trade_volume_usdt", issues)

    if claim_type in {"trading_fee", "fiat_onramp"}:
        _validate_min(claim.get("fee_value"), 0, f"{path}.fee_value", issues)

    _validate_iso_date(claim.get("last_checked_at"), f"{path}.last_checked_at", issues)
    if "valid_until" in claim:
        _validate_iso_date(claim.get("valid_until"), f"{path}.valid_until", issues)


def _validate_article_job(job: JsonDict, index: int, platform_ids: set[str], issues: list[ValidationIssue]) -> None:
    path = f"article_jobs[{index}]"
    _require_fields(
        job,
        {
            "job_id",
            "content_type",
            "target_keyword",
            "region",
            "category",
            "platform_ids",
            "persona",
            "intent",
            "cms_target",
            "allowed_regions",
            "restricted_regions",
            "compliance_disclaimer",
        },
        path,
        issues,
    )
    ids = job.get("platform_ids", [])
    if not isinstance(ids, list) or len(ids) < 2:
        _error(issues, f"{path}.platform_ids", "Comparison jobs require at least two platforms.")
        return
    for platform_id in ids:
        if platform_id not in platform_ids:
            _error(issues, f"{path}.platform_ids", f"Unknown platform_id: {platform_id}")
    if not isinstance(job.get("allowed_regions"), list) or not job.get("allowed_regions"):
        _error(issues, f"{path}.allowed_regions", "Must be a non-empty list for jurisdiction gating.")
    elif job.get("region") not in job["allowed_regions"]:
        _error(issues, f"{path}.region", "Region must appear in allowed_regions.")
    if not isinstance(job.get("restricted_regions"), list):
        _error(issues, f"{path}.restricted_regions", "Must be a list, even when empty.")
    if not isinstance(job.get("compliance_disclaimer"), str) or not job.get("compliance_disclaimer", "").strip():
        _error(issues, f"{path}.compliance_disclaimer", "Must be a non-empty dynamic disclaimer.")


def _validate_editorial_rules(rules: JsonDict, index: int, issues: list[ValidationIssue]) -> None:
    path = f"editorial_rules[{index}]"
    _require_fields(rules, {"rule_set_id", "tone", "forbidden_phrases", "required_sections", "claim_rules"}, path, issues)
    bad_rule = "Every fee or bonus claim must be treated as a cold hard fact."
    if bad_rule in rules.get("claim_rules", []):
        _warning(issues, f"{path}.claim_rules", "Prefer source-backed and dated language over 'cold hard fact'.")


def _build_platform_bundle(platform_id: str, platforms_by_id: dict[str, JsonDict], claims: list[JsonDict], job: JsonDict) -> PlatformBundle:
    region = job["region"]
    platform_claims = [claim for claim in claims if claim.get("platform_id") == platform_id]
    return PlatformBundle(
        platform=platforms_by_id[platform_id],
        signup_bonus=_one_claim(platform_claims, "signup_bonus", region),
        trading_fee=_maybe_claim(platform_claims, "trading_fee", region),
        fiat_onramp=_maybe_claim(platform_claims, "fiat_onramp", region),
        regional_availability=_maybe_claim(platform_claims, "regional_availability", region),
        benefit_claims=_claims_for_region(platform_claims, "benefit", region),
    )


def _one_claim(claims: list[JsonDict], claim_type: str, region: str) -> JsonDict:
    claim = _maybe_claim(claims, claim_type, region)
    if not claim:
        raise ValueError(f"Missing required {claim_type} claim for region {region}.")
    return claim


def _maybe_claim(claims: list[JsonDict], claim_type: str, region: str) -> JsonDict | None:
    regional = _claims_for_region(claims, claim_type, region)
    typed = [claim for claim in claims if claim.get("claim_type") == claim_type]
    return regional[0] if regional else (typed[0] if typed else None)


def _claims_for_region(claims: list[JsonDict], claim_type: str, region: str) -> list[JsonDict]:
    typed = [claim for claim in claims if claim.get("claim_type") == claim_type]
    return [
        claim
        for claim in typed
        if claim.get("region") == region or region in claim.get("eligible_regions", []) or "global" in claim.get("eligible_regions", [])
    ]


def _find_editorial_rules(data: JsonDict, persona: str) -> JsonDict:
    expected = f"{persona}_v1"
    for rules in data["editorial_rules"]:
        if rules.get("rule_set_id") == expected or rules.get("rule_set_id", "").startswith(persona):
            return rules
    if data["editorial_rules"]:
        return data["editorial_rules"][0]
    raise ValueError("No editorial rules available.")


def _unique_index(items: list[JsonDict], key: str, path: str, issues: list[ValidationIssue]) -> set[str]:
    seen: set[str] = set()
    for index, item in enumerate(items):
        value = item.get(key)
        if not value:
            _error(issues, f"{path}[{index}].{key}", "Missing unique identifier.")
        elif value in seen:
            _error(issues, f"{path}[{index}].{key}", f"Duplicate identifier: {value}")
        else:
            seen.add(value)
    return seen


def _require_fields(item: JsonDict, fields: set[str], path: str, issues: list[ValidationIssue]) -> None:
    for field in sorted(fields):
        if field not in item:
            _error(issues, f"{path}.{field}", "Missing required field.")


def _validate_iso_date(value: Any, path: str, issues: list[ValidationIssue]) -> None:
    if not isinstance(value, str):
        _error(issues, path, "Must be an ISO date string.")
        return
    try:
        date.fromisoformat(value)
    except ValueError:
        _error(issues, path, "Must use YYYY-MM-DD format.")


def _validate_number_range(value: Any, minimum: float, maximum: float, path: str, issues: list[ValidationIssue]) -> None:
    if not _is_number(value):
        _error(issues, path, "Must be numeric.")
        return
    if not minimum <= value <= maximum:
        _error(issues, path, f"Must be between {minimum} and {maximum}.")


def _validate_min(value: Any, minimum: float, path: str, issues: list[ValidationIssue]) -> None:
    if not _is_number(value):
        _error(issues, path, "Must be numeric.")
        return
    if value < minimum:
        _error(issues, path, f"Must be greater than or equal to {minimum}.")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _error(issues: list[ValidationIssue], path: str, message: str) -> None:
    issues.append(ValidationIssue("error", path, message))


def _warning(issues: list[ValidationIssue], path: str, message: str) -> None:
    issues.append(ValidationIssue("warning", path, message))
