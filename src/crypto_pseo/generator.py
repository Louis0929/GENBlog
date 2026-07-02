from __future__ import annotations

import json
from html import escape
from typing import Any


JsonDict = dict[str, Any]


def generate_blog_post(brief: JsonDict) -> JsonDict:
    """Generate a deterministic BlogPostStructure from a writer brief.

    This is the local baseline generator. In production, the same brief should be
    sent to an LLM with structured outputs, then checked by the editorial gate.
    """

    job = brief["job"]
    table = brief["information_gain"]["comparison_table"]
    insights = brief["information_gain"]["computed_insights"]
    metrics = brief["information_gain"].get("metrics", [brief["information_gain"]["metrics_a"], brief["information_gain"]["metrics_b"]])
    metrics_a = brief["information_gain"]["metrics_a"]
    metrics_b = brief["information_gain"]["metrics_b"]

    h1_title = _build_h1_title(table, job)
    meta_description = (
        f"{_platform_list_title(table)} in {job['region'].title()}: compare realistic bonus value, "
        "deposit requirements, trading volume, fees, Pix support, and account-opening perks."
    )
    winner_verdict = _winner_verdict(brief)
    html_content = _html_content(brief, job, table, insights, metrics, winner_verdict)
    mentioned_entities = _mentioned_entities(brief, table)
    compliance_disclaimer = job.get("compliance_disclaimer", "")
    schema_markup = _schema_markup(table, winner_verdict, mentioned_entities)

    return {
        "h1_title": h1_title,
        "meta_description": meta_description[:158],
        "target_keyword": job["target_keyword"],
        "html_content": html_content,
        "schema_markup": schema_markup,
        "winner_verdict": winner_verdict,
        "mentioned_entities": mentioned_entities,
        "compliance_disclaimer": compliance_disclaimer,
    }


def _build_h1_title(table: list[JsonDict], job: JsonDict) -> str:
    region = job["region"].title()
    category = job.get("category", "")
    platform_names = _platform_list_title(table)
    if category == "exchange":
        return f"{platform_names} in {region}: Which Global Crypto Exchange Has the Better Bonus?"
    if category == "card":
        return f"{platform_names} in {region}: Which Card Has the Better Bonus and Benefits?"
    if category == "wallet":
        return f"{platform_names} in {region}: Which Wallet Gives Users More Practical Value?"
    return f"{platform_names} in {region}: Which Offer Gives Users More Practical Value?"


def validate_blog_post(post: JsonDict, brief: JsonDict) -> list[str]:
    issues: list[str] = []
    required = {
        "h1_title",
        "meta_description",
        "target_keyword",
        "html_content",
        "schema_markup",
        "winner_verdict",
        "mentioned_entities",
        "compliance_disclaimer",
    }
    for field in sorted(required):
        if not post.get(field):
            issues.append(f"Missing output field: {field}")

    html = post.get("html_content", "").lower()
    for section in brief["editorial_gate"].get("required_sections", []):
        readable = section.replace("_", " ")
        if readable not in html:
            issues.append(f"Missing required section: {section}")

    for phrase in brief["persona"].get("forbidden_phrases", []):
        if phrase.lower() in html or phrase.lower() in post.get("meta_description", "").lower():
            issues.append(f"Forbidden phrase found: {phrase}")

    for insight in brief["information_gain"].get("computed_insights", []):
        if insight.split(".")[0].lower() not in html:
            issues.append(f"Computed insight not reflected in article: {insight}")

    schema_markup = post.get("schema_markup", "")
    try:
        parsed_schema = json.loads(schema_markup)
    except (TypeError, json.JSONDecodeError):
        issues.append("schema_markup must be valid JSON-LD.")
    else:
        schema_types = _schema_types(parsed_schema)
        if not {"FAQPage", "Product", "Review"}.intersection(schema_types):
            issues.append("schema_markup must include FAQPage, Product, or Review JSON-LD.")

    if "not financial advice" not in post.get("html_content", "").lower() and "not financial advice" not in post.get("compliance_disclaimer", "").lower():
        issues.append("Compliance disclaimer must include not financial advice language.")

    missing_sources = _missing_source_urls(post, brief)
    for source_url in missing_sources:
        issues.append(f"Source URL missing from article: {source_url}")

    return issues


def _html_content(
    brief: JsonDict,
    job: JsonDict,
    table: list[JsonDict],
    insights: list[str],
    metrics: list[JsonDict],
    winner_verdict: str,
) -> str:
    verdict_rows = _verdict_rows(table, metrics)
    lower_deposit = _metric_winner(table, metrics, "required_deposit_usdt", lower_is_better=True)
    higher_bonus = _metric_winner(table, metrics, "realistic_value_usdt", lower_is_better=False)
    bonus_gap = _metric_gap(metrics, "realistic_value_usdt")
    who_should_choose = _who_should_choose_items(table, metrics)
    rows = "\n".join(
        [
            "<tr>"
            f"<td>{escape(row['platform'])}</td>"
            f"<td>{escape(row['headline_offer'])}</td>"
            f"<td>${row['realistic_value_usdt']:,.0f}</td>"
            f"<td>${row['required_deposit_usdt']:,.0f}</td>"
            f"<td>${row['required_trade_volume_usdt']:,.0f}</td>"
            f"<td>{_pct(row['realistic_bonus_roi'])}</td>"
            f"<td>${row['expected_net_value_usdt']:,.0f}</td>"
            f"<td>{escape(str(row.get('spot_fee') or 'Not provided'))}</td>"
            f"<td>{escape(str(row.get('fiat_onramp') or 'Not provided'))}: {escape(str(row.get('fiat_onramp_fee') or 'Not provided'))}</td>"
            f"<td>{escape(str(row.get('benefit_summary') or 'Not provided'))}</td>"
            f"<td>{_cta_link(row)}</td>"
            "</tr>"
            for row in table
        ]
    )
    source_links = _source_links(table)
    return f"""<h2>Quick Verdict</h2>
<p>{escape(winner_verdict)}</p>
<p>The catch is simple: the bigger advertised number is not always the better opening-account deal. For most small depositors, what matters here is the realistic reward after deposit and trading requirements.</p>

<table>
<thead>
<tr><th>Use case</th><th>Better fit</th><th>Reason</th></tr>
</thead>
<tbody>
{verdict_rows}
</tbody>
</table>

<h2>Headline vs Realistic Bonus</h2>
{_headline_bonus_paragraphs(table)}
<p>The headline number is not the consumer value. The useful comparison is what a normal user can unlock without pretending they will meet the maximum deposit or volume tier.</p>

<h2>Deposit Requirement Math</h2>
<ul>
{_insight_items(insights)}
</ul>

<table>
<thead>
<tr><th>Platform</th><th>Headline offer</th><th>Realistic value</th><th>Entry deposit</th><th>Trade volume hurdle</th><th>Realistic ROI</th><th>Expected net value</th><th>Spot fee</th><th>{escape(job['region'].title())} fiat onramp</th><th>Benefits lens</th><th>Action</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<h2>Fees and Fiat Friction</h2>
<p>Both platforms list 0.1% spot trading fees in this data set. The difference is not the headline trading fee; it is the onboarding friction. For {escape(job['region'].title())}, Pix support matters because a bonus that looks attractive can become less useful if deposits are slow, costly, or require extra identity matching.</p>
<p>{escape(lower_deposit['platform'])} has the lower tracked entry deposit in this comparison. {escape(higher_bonus['platform'])} has the highest realistic bonus by a ${bonus_gap:,.0f} gap versus the lowest realistic bonus in the set. The practical question is whether that extra value is worth the deposit, trading-volume and onboarding friction.</p>

<h2>Miles, Lounge Access and Other Benefits</h2>
<p>Some readers care less about the opening bonus and more about ongoing perks: miles, lounge access, card rewards, fee rebates or application eligibility. This data set is still exchange-led, so miles and airport lounge access should not be assumed unless a separate card-benefit claim is present.</p>
<ul>
{_benefit_items(table)}
</ul>

<h2>Who Should Choose Each</h2>
{who_should_choose}

<h2>Source Notes</h2>
<p>Claims should be rechecked before publishing because crypto bonuses, fiat rails, and fee schedules can change quickly.</p>
<ul>
{source_links}
</ul>

<h2>Compliance Disclaimer</h2>
<p>{escape(job.get("compliance_disclaimer", "This is not financial advice. Crypto products can be volatile and may be restricted in some jurisdictions."))}</p>"""


def _winner_verdict(brief: JsonDict) -> str:
    info = brief["information_gain"]
    table = info["comparison_table"]
    low_budget = info["low_budget_winner"]
    roi_winner = info["roi_winner"]
    higher_bonus = info.get("highest_bonus_winner") or _metric_winner(table, info.get("metrics", []), "realistic_value_usdt", lower_is_better=False)["platform"]
    if low_budget == roi_winner:
        return (
            f"{low_budget} is the cleaner choice for low-budget users because it combines the stronger realistic bonus ROI "
            f"with the lower tracked entry deposit. {higher_bonus} still deserves attention when its realistic reward is higher, "
            "but only if the user can meet the requirements without overtrading."
        )
    return (
        f"{low_budget} is the lower-friction option for opening an account, while {roi_winner} has the stronger realistic bonus ROI in this data set. "
        f"{higher_bonus} has the higher realistic reward, but the requirements decide whether that value is practical."
    )


def _verdict_rows(table: list[JsonDict], metrics: list[JsonDict]) -> str:
    low_deposit = _metric_winner(table, metrics, "required_deposit_usdt", lower_is_better=True)["platform"]
    higher_bonus = _metric_winner(table, metrics, "realistic_value_usdt", lower_is_better=False)["platform"]
    better_roi = _metric_winner(table, metrics, "realistic_bonus_roi", lower_is_better=False)["platform"]
    better_ev = _metric_winner(table, metrics, "expected_net_value_usdt", lower_is_better=False)["platform"]
    rows = [
        ("Small first deposit", low_deposit, "Lower entry deposit and less bonus friction."),
        ("Highest realistic bonus", higher_bonus, "Higher realistic reward, before considering effort and capital lock-up."),
        ("Best bonus ROI", better_roi, "Better reward relative to the required deposit."),
        ("Best expected value", better_ev, "Higher net value after estimated trading-fee drag."),
    ]
    return "\n".join(
        f"<tr><td>{escape(use_case)}</td><td>{escape(winner)}</td><td>{escape(reason)}</td></tr>"
        for use_case, winner, reason in rows
    )


def _metric_winner(table: list[JsonDict], metrics: list[JsonDict], metric: str, *, lower_is_better: bool) -> JsonDict:
    rows_by_id = {row.get("platform", "").lower(): row for row in table}

    def value(item: JsonDict) -> float:
        raw = item.get(metric)
        if raw is None:
            return float("inf") if lower_is_better else float("-inf")
        return float(raw)

    winner = min(metrics, key=value) if lower_is_better else max(metrics, key=value)
    return rows_by_id.get(str(winner.get("name", "")).lower(), table[0])


def _who_should_choose_items(table: list[JsonDict], metrics: list[JsonDict]) -> str:
    lower_deposit = _metric_winner(table, metrics, "required_deposit_usdt", lower_is_better=True)["platform"]
    higher_bonus = _metric_winner(table, metrics, "realistic_value_usdt", lower_is_better=False)["platform"]
    by_name = {row["platform"]: row for row in table}
    sections = []
    for row in table:
        platform = row["platform"]
        reasons = []
        if platform == lower_deposit:
            reasons.append("you want the lower-friction account-opening route")
        if platform == higher_bonus and row["realistic_value_usdt"] > 0:
            reasons.append("you care more about the higher realistic reward and can satisfy the terms")
        if not reasons:
            reasons.append("its local access, product fit or benefit claims matter more to you than the headline bonus")
        sections.append(
            f"<h3>Choose {escape(platform)} if</h3>\n"
            f"<p>{escape(' and '.join(reasons).capitalize())}. {_inline_cta(by_name[platform])}</p>"
        )
    return "\n".join(sections)


def _schema_markup(table: list[JsonDict], winner_verdict: str, mentioned_entities: list[str]) -> str:
    platform_names = _platform_list_title(table)
    schema = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f"Which bonus is better for low-budget users: {platform_names}?",
                        "acceptedAnswer": {"@type": "Answer", "text": winner_verdict},
                    },
                    {
                        "@type": "Question",
                        "name": "Should I trust the headline crypto bonus amount?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "No. The headline amount should be checked against the realistic reward tier, deposit requirement, trading volume, expiry date, and regional eligibility.",
                        },
                    },
                ],
            },
            {
                "@type": "ItemList",
                "name": f"{platform_names} comparison",
                "itemListElement": [
                    {
                        "@type": "Product",
                        "position": index + 1,
                        "name": row["platform"],
                        "description": f"{row['platform']} crypto exchange signup bonus comparison entry.",
                    }
                    for index, row in enumerate(table)
                ],
            },
            {
                "@type": "Thing",
                "name": "Mentioned entities",
                "description": ", ".join(mentioned_entities),
            },
        ],
    }
    return json.dumps(schema, ensure_ascii=False)


def _schema_types(schema: JsonDict) -> set[str]:
    types: set[str] = set()

    def visit(node: object) -> None:
        if isinstance(node, dict):
            raw_type = node.get("@type")
            if isinstance(raw_type, str):
                types.add(raw_type)
            elif isinstance(raw_type, list):
                types.update(str(item) for item in raw_type)
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(schema)
    return types


def _mentioned_entities(brief: JsonDict, table: list[JsonDict]) -> list[str]:
    entities = [row["platform"] for row in table]
    region = brief["job"].get("region")
    category = brief["job"].get("category")
    if region:
        entities.append(str(region).title())
    if category:
        entities.append(str(category))
    for row in table:
        fiat = row.get("fiat_onramp")
        if fiat:
            entities.append(str(fiat))
    return list(dict.fromkeys(entities))


def _insight_items(insights: list[str]) -> str:
    return "\n".join(f"<li>{escape(insight)}</li>" for insight in insights)


def _headline_bonus_paragraphs(table: list[JsonDict]) -> str:
    return "\n".join(
        f"<p>{escape(row['platform'])} advertises {escape(row['headline_offer'])}, but the realistic value used in this comparison is ${row['realistic_value_usdt']:,.0f}.</p>"
        for row in table
    )


def _platform_list_title(table: list[JsonDict]) -> str:
    names = [row["platform"] for row in table]
    return " vs ".join(names)


def _metric_gap(metrics: list[JsonDict], metric: str) -> float:
    values = [float(item.get(metric) or 0) for item in metrics]
    if not values:
        return 0
    return max(values) - min(values)


def _benefit_items(table: list[JsonDict]) -> str:
    return "\n".join(
        f"<li><strong>{escape(row['platform'])}:</strong> {escape(str(row.get('benefit_summary') or 'No benefit claims in current data.'))}</li>"
        for row in table
    )


def _source_links(table: list[JsonDict]) -> str:
    urls = []
    for row in table:
        urls.extend(row.get("source_urls", []))
    unique_urls = list(dict.fromkeys(urls))
    return "\n".join(f'<li><a href="{escape(url)}">{escape(url)}</a></li>' for url in unique_urls)


def _cta_link(row: JsonDict) -> str:
    affiliate_url = row.get("affiliate_url")
    if not affiliate_url:
        return "Check current offer"
    return f'<a href="{escape(affiliate_url)}" rel="sponsored nofollow">Claim the bonus</a>'


def _inline_cta(row: JsonDict) -> str:
    affiliate_url = row.get("affiliate_url")
    if not affiliate_url:
        return "Check the current offer terms before signing up."
    return f'<a href="{escape(affiliate_url)}" rel="sponsored nofollow">Claim the bonus</a> after checking the current terms.'


def _missing_source_urls(post: JsonDict, brief: JsonDict) -> list[str]:
    content = "\n".join(
        [
            post.get("html_content", ""),
            post.get("schema_markup", ""),
            post.get("winner_verdict", ""),
        ]
    )
    expected_urls = []
    for row in brief["information_gain"].get("comparison_table", []):
        expected_urls.extend(row.get("source_urls", []))
    return [url for url in dict.fromkeys(expected_urls) if url and url not in content]


def _pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.1f}%"
