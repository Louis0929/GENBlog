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
