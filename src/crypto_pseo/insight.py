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
    metrics_a: PlatformMetrics
    metrics_b: PlatformMetrics
    bonus_diff_usdt: float
    deposit_diff_usdt: float
    deposit_burden_ratio: float | None
    trade_volume_diff_usdt: float
    roi_winner: str
    low_budget_winner: str
    computed_insights: list[str]
    comparison_table: list[JsonDict]


def compute_information_gain(bundle: ComparisonBundle) -> InformationGain:
    metrics_a = _platform_metrics(bundle.platform_a)
    metrics_b = _platform_metrics(bundle.platform_b)
    bonus_diff = metrics_a.realistic_value_usdt - metrics_b.realistic_value_usdt
    deposit_diff = metrics_a.required_deposit_usdt - metrics_b.required_deposit_usdt
    trade_volume_diff = metrics_a.required_trade_volume_usdt - metrics_b.required_trade_volume_usdt
    deposit_burden_ratio = _safe_divide(metrics_b.required_deposit_usdt, metrics_a.required_deposit_usdt)

    roi_winner = _winner_by_roi(metrics_a, metrics_b)
    low_budget_winner = _winner_by_budget(metrics_a, metrics_b)
    insights = _build_insights(metrics_a, metrics_b, bonus_diff, deposit_burden_ratio, trade_volume_diff, roi_winner, low_budget_winner)

    return InformationGain(
        metrics_a=metrics_a,
        metrics_b=metrics_b,
        bonus_diff_usdt=bonus_diff,
        deposit_diff_usdt=deposit_diff,
        deposit_burden_ratio=deposit_burden_ratio,
        trade_volume_diff_usdt=trade_volume_diff,
        roi_winner=roi_winner,
        low_budget_winner=low_budget_winner,
        computed_insights=insights,
        comparison_table=_comparison_table(bundle, metrics_a, metrics_b),
    )


def build_writer_brief(bundle: ComparisonBundle, info: InformationGain) -> JsonDict:
    return {
        "job": bundle.job,
        "persona": {
            "name": "The Lexington Crypto-Analyst",
            "tone": bundle.editorial_rules.get("tone", []),
            "rules": bundle.editorial_rules.get("claim_rules", []),
            "forbidden_phrases": bundle.editorial_rules.get("forbidden_phrases", []),
        },
        "platforms": {
            "platform_a": _brief_platform(bundle.platform_a),
            "platform_b": _brief_platform(bundle.platform_b),
        },
        "information_gain": {
            "metrics_a": info.metrics_a.__dict__,
            "metrics_b": info.metrics_b.__dict__,
            "bonus_diff_usdt": info.bonus_diff_usdt,
            "deposit_diff_usdt": info.deposit_diff_usdt,
            "deposit_burden_ratio": info.deposit_burden_ratio,
            "trade_volume_diff_usdt": info.trade_volume_diff_usdt,
            "roi_winner": info.roi_winner,
            "low_budget_winner": info.low_budget_winner,
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
                "Do not repeat headline bonuses without requirements.",
                "Explain realistic value before headline value.",
                "Qualify claims with sources and dates when possible.",
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


def _build_insights(
    a: PlatformMetrics,
    b: PlatformMetrics,
    bonus_diff: float,
    deposit_burden_ratio: float | None,
    trade_volume_diff: float,
    roi_winner: str,
    low_budget_winner: str,
) -> list[str]:
    insights = []
    if a.realistic_bonus_roi is not None and b.realistic_bonus_roi is not None:
        insights.append(
            f"{a.name} has a realistic bonus ROI of {_pct(a.realistic_bonus_roi)}, versus {_pct(b.realistic_bonus_roi)} for {b.name}."
        )
    if deposit_burden_ratio is not None:
        insights.append(
            f"{b.name} requires {deposit_burden_ratio:g}x the entry deposit of {a.name} for the compared realistic bonus tier."
        )
    if trade_volume_diff != 0:
        higher = b.name if b.required_trade_volume_usdt > a.required_trade_volume_usdt else a.name
        insights.append(f"{higher} adds a ${abs(trade_volume_diff):,.0f} trading-volume hurdle in this comparison.")
    if bonus_diff != 0:
        higher_bonus = a.name if bonus_diff > 0 else b.name
        insights.append(f"{higher_bonus} has the higher realistic bonus by ${abs(bonus_diff):,.0f}, but deposit and volume requirements change the practical value.")
    insights.append(f"ROI winner: {roi_winner}. Low-budget onboarding winner: {low_budget_winner}.")
    return insights


def _comparison_table(bundle: ComparisonBundle, a: PlatformMetrics, b: PlatformMetrics) -> list[JsonDict]:
    return [
        _comparison_row(bundle.platform_a, a),
        _comparison_row(bundle.platform_b, b),
    ]


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
        "source_urls": _source_urls(bundle),
    }


def _brief_platform(bundle: PlatformBundle) -> JsonDict:
    return {
        "platform": bundle.platform,
        "signup_bonus": bundle.signup_bonus,
        "trading_fee": bundle.trading_fee,
        "fiat_onramp": bundle.fiat_onramp,
        "regional_availability": bundle.regional_availability,
    }


def _source_urls(bundle: PlatformBundle) -> list[str]:
    urls = []
    for claim in [bundle.signup_bonus, bundle.trading_fee, bundle.fiat_onramp, bundle.regional_availability]:
        if claim and claim.get("source_url"):
            urls.append(claim["source_url"])
    return urls


def _winner_by_roi(a: PlatformMetrics, b: PlatformMetrics) -> str:
    if a.realistic_bonus_roi is None:
        return b.name
    if b.realistic_bonus_roi is None:
        return a.name
    return a.name if a.realistic_bonus_roi >= b.realistic_bonus_roi else b.name


def _winner_by_budget(a: PlatformMetrics, b: PlatformMetrics) -> str:
    if a.required_deposit_usdt == b.required_deposit_usdt:
        return _winner_by_roi(a, b)
    return a.name if a.required_deposit_usdt < b.required_deposit_usdt else b.name


def _safe_divide(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _pct(value: float) -> str:
    return f"{value * 100:.1f}%"
