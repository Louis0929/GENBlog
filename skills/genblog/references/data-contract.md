# GenBlog Data Contract

The current v1 input is a normalized campaign JSON object. DB integration is deferred.

## Required Collections

- `platforms`
- `claims`
- `sources`
- `article_jobs`
- `editorial_rules`

## Article Job Fields

Required:

- `allowed_regions`: non-empty jurisdiction allow-list
- `restricted_regions`: explicit jurisdiction deny-list, even when empty
- `compliance_disclaimer`: region-specific disclaimer, including not-financial-advice language when crypto products are discussed

Rules:

- The job `region` must appear in `allowed_regions`.
- Do not generate or publish a job for a restricted region.
- Keep the disclaimer in both the structured output and article HTML.

## Claim-Level Data

Use claim-level records rather than only platform-level records. A platform comparison needs separate claims for:

- signup bonus
- trading fee
- fiat onramp
- regional availability
- benefit claims, when users care about miles, lounge access, card perks, rewards, fee rebates, or application eligibility

## Signup Bonus Fields

Required:

- `headline_offer`
- `headline_value_usdt`
- `realistic_value_usdt`
- `required_deposit_usdt`
- `required_trade_volume_usdt`
- `user_requirements`
- `eligible_regions`
- `source_id`
- `source_url`
- `last_checked_at`
- `confidence`

Validation:

- realistic value must not exceed headline value
- required deposit and required trading volume must be numeric
- source must allow the claim type

## Search Evidence

Search evidence is auxiliary. It can support context and freshness review, but it must not overwrite campaign facts automatically.

Prompt payloads must separate:

- `absolute_facts`: campaign data, computed information gain, platform claims, source URLs
- `search_notes`: optional background context only

If the two conflict, `absolute_facts` wins.

`llm_prompt_package.json` must also include `prompt_context_xml` with this exact tag shape:

```xml
<CAMPAIGN_FACTS>
  campaign facts, computed metrics, source URLs, and compliance disclaimer
</CAMPAIGN_FACTS>
<SEARCH_NOTES>
  optional background notes only
</SEARCH_NOTES>
```

The LLM must never rewrite numeric values or compliance statements from `<CAMPAIGN_FACTS>`.

## Editorial Gate Feedback

When the gate blocks an article, return:

- `issues`: raw error strings
- `revision_reasons`: structured objects with `code`, `field`, and `message`
- `revision_context`: retry metadata such as target keyword, blocked fields, and fact-preservation rule
- `revision_prompt`: concise rewrite instruction for the next LLM pass

## Information Gain Fields

Compute and pass these metrics before writing:

- `realistic_bonus_roi`
- `estimated_fee_cost_usdt`
- `expected_net_value_usdt`
- `required_deposit_usdt`
- `required_trade_volume_usdt`
- fiat/onramp friction

Expected net value is the realistic bonus minus estimated trading-fee drag from required volume. Add more costs later only when the data contract has explicit fields for them.

## Output Contract Additions

Structured output must include:

- `mentioned_entities`: exchanges, regions, fiat rails, product categories, and other linkable entities
- `compliance_disclaimer`: the jurisdiction-specific disclaimer used in the article

`schema_markup` must include `FAQPage`, `Product`, or `Review` JSON-LD.

## Benefit Claim Fields

Required:

- `benefit_type`: `miles`, `lounge_access`, `card_rewards`, `application_eligibility`, `fee_rebate`, `localization`, or another explicit benefit type
- `availability`: `available`, `not_available`, `not_evidenced`, `varies`, or `needs_review`
- `value_display`
- `requirement`
- `notes`
- `source_id`
- `source_url`
- `last_checked_at`
- `confidence`

Rules:

- Do not imply miles or lounge access unless the claim explicitly supports it.
- If a product is exchange-only, use benefit claims to say card-style perks are not evidenced in the current data.
- Keep benefits separate from signup bonuses; a high bonus does not imply better ongoing perks.
