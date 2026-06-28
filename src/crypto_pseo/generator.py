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
    metrics_a = brief["information_gain"]["metrics_a"]
    metrics_b = brief["information_gain"]["metrics_b"]
    platform_a = table[0]
    platform_b = table[1]

    h1_title = f"{platform_a['platform']} vs {platform_b['platform']} Bonus in {job['region'].title()}: Which Offer Is Actually Better?"
    meta_description = (
        f"A skeptical comparison of {platform_a['platform']} and {platform_b['platform']} bonuses in {job['region'].title()}, "
        "using realistic bonus value, deposit requirements, trading volume, fees, and Pix support."
    )
    winner_verdict = _winner_verdict(brief)
    html_content = _html_content(brief, job, table, insights, metrics_a, metrics_b, winner_verdict)
    schema_markup = _faq_schema(platform_a, platform_b, winner_verdict)

    return {
        "h1_title": h1_title,
        "meta_description": meta_description[:158],
        "target_keyword": job["target_keyword"],
        "html_content": html_content,
        "schema_markup": schema_markup,
        "winner_verdict": winner_verdict,
    }


def validate_blog_post(post: JsonDict, brief: JsonDict) -> list[str]:
    issues: list[str] = []
    required = {"h1_title", "meta_description", "target_keyword", "html_content", "schema_markup", "winner_verdict"}
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
        json.loads(schema_markup)
    except (TypeError, json.JSONDecodeError):
        issues.append("schema_markup must be valid JSON-LD.")

    missing_sources = _missing_source_urls(post, brief)
    for source_url in missing_sources:
        issues.append(f"Source URL missing from article: {source_url}")

    return issues


def _html_content(
    brief: JsonDict,
    job: JsonDict,
    table: list[JsonDict],
    insights: list[str],
    metrics_a: JsonDict,
    metrics_b: JsonDict,
    winner_verdict: str,
) -> str:
    verdict_rows = _verdict_rows(table, metrics_a, metrics_b)
    lower_deposit = _metric_winner(table, metrics_a, metrics_b, "required_deposit_usdt", lower_is_better=True)
    higher_bonus = _metric_winner(table, metrics_a, metrics_b, "realistic_value_usdt", lower_is_better=False)
    who_should_choose = _who_should_choose_items(table, metrics_a, metrics_b)
    rows = "\n".join(
        [
            "<tr>"
            f"<td>{escape(row['platform'])}</td>"
            f"<td>{escape(row['headline_offer'])}</td>"
            f"<td>${row['realistic_value_usdt']:,.0f}</td>"
            f"<td>${row['required_deposit_usdt']:,.0f}</td>"
            f"<td>${row['required_trade_volume_usdt']:,.0f}</td>"
            f"<td>{_pct(row['realistic_bonus_roi'])}</td>"
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
<p>{escape(table[0]['platform'])} advertises {escape(table[0]['headline_offer'])}, but the realistic value used in this comparison is ${table[0]['realistic_value_usdt']:,.0f}. {escape(table[1]['platform'])} advertises {escape(table[1]['headline_offer'])}, but the realistic entry value used here is ${table[1]['realistic_value_usdt']:,.0f}.</p>
<p>The headline number is not the consumer value. The useful comparison is what a normal user can unlock without pretending they will meet the maximum deposit or volume tier.</p>

<h2>Deposit Requirement Math</h2>
<ul>
{_insight_items(insights)}
</ul>

<table>
<thead>
<tr><th>Platform</th><th>Headline offer</th><th>Realistic value</th><th>Entry deposit</th><th>Trade volume hurdle</th><th>Realistic ROI</th><th>Spot fee</th><th>{escape(job['region'].title())} fiat onramp</th><th>Benefits lens</th><th>Action</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<h2>Fees and Fiat Friction</h2>
<p>Both platforms list 0.1% spot trading fees in this data set. The difference is not the headline trading fee; it is the onboarding friction. For {escape(job['region'].title())}, Pix support matters because a bonus that looks attractive can become less useful if deposits are slow, costly, or require extra identity matching.</p>
<p>{escape(lower_deposit['platform'])} has the lower tracked entry deposit in this comparison. {escape(higher_bonus['platform'])} has the higher realistic bonus by ${abs(metrics_a['realistic_value_usdt'] - metrics_b['realistic_value_usdt']):,.0f}. The practical question is whether that extra value is worth the deposit, trading-volume and onboarding friction.</p>

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
</ul>"""


def _winner_verdict(brief: JsonDict) -> str:
    info = brief["information_gain"]
    table = info["comparison_table"]
    low_budget = info["low_budget_winner"]
    roi_winner = info["roi_winner"]
    higher_bonus = table[0]["platform"] if table[0]["realistic_value_usdt"] >= table[1]["realistic_value_usdt"] else table[1]["platform"]
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


def _verdict_rows(table: list[JsonDict], metrics_a: JsonDict, metrics_b: JsonDict) -> str:
    platform_a = table[0]["platform"]
    platform_b = table[1]["platform"]
    low_deposit = platform_a if metrics_a["required_deposit_usdt"] <= metrics_b["required_deposit_usdt"] else platform_b
    higher_bonus = platform_a if metrics_a["realistic_value_usdt"] >= metrics_b["realistic_value_usdt"] else platform_b
    better_roi = platform_a if (metrics_a["realistic_bonus_roi"] or 0) >= (metrics_b["realistic_bonus_roi"] or 0) else platform_b
    rows = [
        ("Small first deposit", low_deposit, "Lower entry deposit and less bonus friction."),
        ("Highest realistic bonus", higher_bonus, "Higher realistic reward, before considering effort and capital lock-up."),
        ("Best bonus ROI", better_roi, "Better reward relative to the required deposit."),
    ]
    return "\n".join(
        f"<tr><td>{escape(use_case)}</td><td>{escape(winner)}</td><td>{escape(reason)}</td></tr>"
        for use_case, winner, reason in rows
    )


def _metric_winner(table: list[JsonDict], metrics_a: JsonDict, metrics_b: JsonDict, metric: str, *, lower_is_better: bool) -> JsonDict:
    value_a = metrics_a.get(metric)
    value_b = metrics_b.get(metric)
    if value_a == value_b:
        return table[0]
    if lower_is_better:
        return table[0] if value_a < value_b else table[1]
    return table[0] if value_a > value_b else table[1]


def _who_should_choose_items(table: list[JsonDict], metrics_a: JsonDict, metrics_b: JsonDict) -> str:
    lower_deposit = _metric_winner(table, metrics_a, metrics_b, "required_deposit_usdt", lower_is_better=True)["platform"]
    higher_bonus = _metric_winner(table, metrics_a, metrics_b, "realistic_value_usdt", lower_is_better=False)["platform"]
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


def _faq_schema(platform_a: JsonDict, platform_b: JsonDict, winner_verdict: str) -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Which bonus is better for low-budget users, {platform_a['platform']} or {platform_b['platform']}?",
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
    }
    return json.dumps(schema, ensure_ascii=False)


def _insight_items(insights: list[str]) -> str:
    return "\n".join(f"<li>{escape(insight)}</li>" for insight in insights)


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
