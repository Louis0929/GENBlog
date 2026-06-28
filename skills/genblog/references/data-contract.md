# GenBlog Data Contract

The current v1 input is a normalized campaign JSON object. DB integration is deferred.

## Required Collections

- `platforms`
- `claims`
- `sources`
- `article_jobs`
- `editorial_rules`

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
