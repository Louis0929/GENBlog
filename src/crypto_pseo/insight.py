from __future__ import annotations

from dataclasses import dataclass

from .contract import ComparisonBundle, JsonDict, PlatformBundle


@dataclass(frozen=True)
class PlatformMetrics:
    platform_id: str
    name: str
    headline_value_usdt: float
    realistic_value_usdt: float
    required_deposit_usdt: float
    required_trade_volume_usdt: float
    realistic_bonus_roi: float | None
    headline_to_realistic_ratio: float | None


@dataclass(frozen=True)
class InformationGain:
    metrics: list[PlatformMetrics]
    metrics_a: PlatformMetrics
    metrics_b: PlatformMetrics
    bonus_diff_usdt: float
    deposit_diff_usdt: float
    deposit_burden_ratio: float | None
    trade_volume_diff_usdt: float
    roi_winner: str
    low_budget_winner: str
    highest_bonus_winner: str
    computed_insights: list[str]
    comparison_table: list[JsonDict]


def compute_information_gain(bundle: ComparisonBundle) -> InformationGain:
    metrics = [_platform_metrics(platform) for platform in bundle.platforms]
    metrics_a = metrics[0]
    metrics_b = metrics[1]
    bonus_diff = metrics_a.realistic_value_usdt - metrics_b.realistic_value_usdt
    deposit_diff = metrics_a.required_deposit_usdt - metrics_b.required_deposit_usdt
    trade_volume_diff = metrics_a.required_trade_volume_usdt - metrics_b.required_trade_volume_usdt
    deposit_burden_ratio = _safe_divide(metrics_b.required_deposit_usdt, metrics_a.required_deposit_usdt)

    roi_winner = _winner_name(metrics, "realistic_bonus_roi", lower_is_better=False)
    low_budget_winner = _winner_name(metrics, "required_deposit_usdt", lower_is_better=True)
    highest_bonus_winner = _winner_name(metrics, "realistic_value_usdt", lower_is_better=False)
    insights = _build_insights(metrics, roi_winner, low_budget_winner, highest_bonus_winner)

    return InformationGain(
        metrics=metrics,
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        bonus_diff_usdt=bonus_diff,
        deposit_diff_usdt=deposit_diff,
        deposit_burden_ratio=deposit_burden_ratio,
        trade_volume_diff_usdt=trade_volume_diff,
        roi_winner=roi_winner,
        low_budget_winner=low_budget_winner,
        highest_bonus_winner=highest_bonus_winner,
        computed_insights=insights,
        comparison_table=_comparison_table(bundle, metrics),
    )


def build_writer_brief(bundle: ComparisonBundle, info: InformationGain) -> JsonDict:
    return {
        "job": bundle.job,
        "persona": {
            "name": "The Lexington Crypto-Analyst",
            "tone": bundle.editorial_rules.get("tone", []),
            "style_profile": bundle.editorial_rules.get("style_profile", {}),
            "rules": bundle.editorial_rules.get("claim_rules", []),
            "forbidden_phrases": bundle.editorial_rules.get("forbidden_phrases", []),
        },
        "platforms": {
            "platform_list": [_brief_platform(platform) for platform in bundle.platforms],
            "platform_a": _brief_platform(bundle.platform_a),
            "platform_b": _brief_platform(bundle.platform_b),
        },
        "information_gain": {
            "metrics": [metric.__dict__ for metric in info.metrics],
            "metrics_a": info.metrics_a.__dict__,
            "metrics_b": info.metrics_b.__dict__,
            "bonus_diff_usdt": info.bonus_diff_usdt,
            "deposit_diff_usdt": info.deposit_diff_usdt,
            "deposit_burden_ratio": info.deposit_burden_ratio,
            "trade_volume_diff_usdt": info.trade_volume_diff_usdt,
            "roi_winner": info.roi_winner,
            "low_budget_winner": info.low_budget_winner,
            "highest_bonus_winner": info.highest_bonus_winner,
            "computed_insights": info.computed_insights,
            "comparison_table": info.comparison_table,
        },
        "required_output_schema": {
            "h1_title": "string",
            "meta_description": "string",
            "target_keyword": "string",
            "html_content": "string with H2/H3 tags and comparison tables",
            "schema_markup": "FAQPage or Product JSON-LD string",
            "winner_verdict": "string",
        },
        "editorial_gate": {
            "required_sections": bundle.editorial_rules.get("required_sections", []),
            "must_do": [
                "Lead with a practical verdict.",
                "Keep the tone neutral, human, and affiliate-friendly.",
                "Do not repeat headline bonuses without requirements.",
                "Explain realistic value before headline value.",
                "Qualify claims with sources and dates when possible.",
                "Use MoneyHero-style comparison tables where possible.",
                "Use a clear but honest CTA such as 'Claim the bonus'.",
                "Do not use hype or generic SEO filler.",
            ],
        },
    }


def _platform_metrics(bundle: PlatformBundle) -> PlatformMetrics:
    bonus = bundle.signup_bonus
    headline = float(bonus["headline_value_usdt"])
    realistic = float(bonus["realistic_value_usdt"])
    deposit = float(bonus["required_deposit_usdt"])
    trade_volume = float(bonus.get("required_trade_volume_usdt", 0))
    return PlatformMetrics(
        platform_id=bundle.platform["platform_id"],
        name=bundle.platform["name"],
        headline_value_usdt=headline,
        realistic_value_usdt=realistic,
        required_deposit_usdt=deposit,
        required_trade_volume_usdt=trade_volume,
        realistic_bonus_roi=_safe_divide(realistic, deposit),
        headline_to_realistic_ratio=_safe_divide(headline, realistic),
    )


def _build_insights(metrics: list[PlatformMetrics], roi_winner: str, low_budget_winner: str, highest_bonus_winner: str) -> list[str]:
    insights = []
    roi_parts = [f"{metric.name}: {_pct(metric.realistic_bonus_roi)}" for metric in metrics]
    insights.append(f"Realistic bonus ROI by platform: {'; '.join(roi_parts)}.")
    deposit_parts = [f"{metric.name}: ${metric.required_deposit_usdt:,.0f}" for metric in metrics]
    insights.append(f"Entry deposit requirements: {'; '.join(deposit_parts)}.")
    volume_hurdles = [metric for metric in metrics if metric.required_trade_volume_usdt > 0]
    if volume_hurdles:
        hurdle_parts = [f"{metric.name}: ${metric.required_trade_volume_usdt:,.0f}" for metric in volume_hurdles]
        insights.append(f"Trading-volume hurdles appear in this data set: {'; '.join(hurdle_parts)}.")
    bonus_parts = [f"{metric.name}: ${metric.realistic_value_usdt:,.0f}" for metric in metrics]
    insights.append(f"Realistic bonus values: {'; '.join(bonus_parts)}.")
    insights.append(f"ROI winner: {roi_winner}. Low-budget onboarding winner: {low_budget_winner}. Highest realistic bonus: {highest_bonus_winner}.")
    return insights


def _comparison_table(bundle: ComparisonBundle, metrics: list[PlatformMetrics]) -> list[JsonDict]:
    return [_comparison_row(platform, metric) for platform, metric in zip(bundle.platforms, metrics)]


def _comparison_row(bundle: PlatformBundle, metrics: PlatformMetrics) -> JsonDict:
    bonus = bundle.signup_bonus
    fiat = bundle.fiat_onramp or {}
    fee = bundle.trading_fee or {}
    return {
        "platform": metrics.name,
        "headline_offer": bonus.get("headline_offer"),
        "realistic_value_usdt": metrics.realistic_value_usdt,
        "required_deposit_usdt": metrics.required_deposit_usdt,
        "required_trade_volume_usdt": metrics.required_trade_volume_usdt,
        "realistic_bonus_roi": metrics.realistic_bonus_roi,
        "spot_fee": fee.get("fee_display"),
        "fiat_onramp": fiat.get("rail"),
        "fiat_onramp_fee": fiat.get("fee_display"),
        "benefit_summary": _benefit_summary(bundle.benefit_claims),
        "benefit_claims": bundle.benefit_claims,
        "affiliate_url": bundle.platform.get("affiliate_program", {}).get("affiliate_url"),
        "source_urls": _source_urls(bundle),
    }


def _brief_platform(bundle: PlatformBundle) -> JsonDict:
    return {
        "platform": bundle.platform,
        "signup_bonus": bundle.signup_bonus,
        "trading_fee": bundle.trading_fee,
        "fiat_onramp": bundle.fiat_onramp,
        "regional_availability": bundle.regional_availability,
        "benefit_claims": bundle.benefit_claims,
    }


def _source_urls(bundle: PlatformBundle) -> list[str]:
    urls = []
    for claim in [bundle.signup_bonus, bundle.trading_fee, bundle.fiat_onramp, bundle.regional_availability]:
        if claim and claim.get("source_url"):
            urls.append(claim["source_url"])
    for claim in bundle.benefit_claims:
        if claim and claim.get("source_url"):
            urls.append(claim["source_url"])
    return urls


def _benefit_summary(claims: list[JsonDict]) -> str:
    if not claims:
        return "No benefit claims in current data."
    visible = []
    for claim in claims:
        benefit_type = str(claim.get("benefit_type", "benefit")).replace("_", " ")
        availability = claim.get("availability", "unknown")
        value = claim.get("value_display", "Not provided")
        visible.append(f"{benefit_type}: {value} ({availability})")
    return "; ".join(visible)


def _winner_name(metrics: list[PlatformMetrics], field: str, *, lower_is_better: bool) -> str:
    def key(metric: PlatformMetrics) -> float:
        value = getattr(metric, field)
        if value is None:
            return float("-inf") if not lower_is_better else float("inf")
        return value

    winner = min(metrics, key=key) if lower_is_better else max(metrics, key=key)
    return winner.name


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"
