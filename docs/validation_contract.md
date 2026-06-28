# Validation Contract

This contract describes the fields the pipeline expects from the upstream MongoDB-normalized data.

## Top-Level Collections

Required top-level keys:

- `platforms`
- `claims`
- `sources`
- `article_jobs`
- `editorial_rules`

## Platform

Required:

- `platform_id`
- `name`
- `category`
- `tier`
- `target_regions`
- `supported_fiat_rails`
- `affiliate_program.status`
- `affiliate_program.affiliate_url`
- `affiliate_program.commission_model`
- `affiliate_program.commission_value`
- `affiliate_program.source_url`

Validation rules:

- `platform_id` must be unique.
- `target_regions` must be a non-empty list.
- Active affiliate programs must have an affiliate URL.

## Claim

Required for all claims:

- `claim_id`
- `platform_id`
- `claim_type`
- `source_id`
- `last_checked_at`
- `confidence`

Recommended for all claims:

- `source_url`
- `claim_status`
- `valid_until`

Validation rules:

- `claim_id` must be unique.
- `platform_id` must reference an existing platform.
- `source_id` must reference an existing source.
- `confidence` must be between `0` and `1`.
- The linked source must allow the claim type.

## Signup Bonus Claim

Required:

- `headline_offer`
- `headline_value_usdt`
- `realistic_value_usdt`
- `required_deposit_usdt`
- `user_requirements`
- `eligible_regions`

Recommended:

- `required_trade_volume_usdt`
- `valid_until`

Validation rules:

- `realistic_value_usdt` must not exceed `headline_value_usdt`.
- `required_deposit_usdt` must be greater than or equal to `0`.
- `required_trade_volume_usdt` should be numeric; use `0` when no trade volume is required.

## Trading Fee Claim

Required:

- `fee_type`
- `fee_value`
- `fee_display`

Recommended:

- `fee_unit`, usually `rate`

Validation rules:

- `fee_value` must be greater than or equal to `0`.

## Fiat Onramp Claim

Required:

- `rail`
- `availability`
- `fee_display`
- `fee_value`
- `region`

Recommended:

- `fee_unit`
- `fee_currency`

Validation rules:

- `fee_value` must be greater than or equal to `0`.
- `region` must match the article job region when used in a job.

## Regional Availability Claim

Required:

- `region`
- `availability`

## Source

Required:

- `source_id`
- `domain`
- `source_type`
- `credibility_score`
- `allowed_claim_types`
- `freshness_half_life_days`

Validation rules:

- `credibility_score` must be between `0` and `1`.
- `freshness_half_life_days` must be greater than `0`.

## Article Job

Required:

- `job_id`
- `content_type`
- `target_keyword`
- `region`
- `category`
- `platform_ids`
- `persona`
- `intent`
- `cms_target`

Validation rules:

- `platform_ids` must reference existing platforms.
- A comparison article currently expects exactly two platforms.

## Editorial Rule Set

Required:

- `rule_set_id`
- `tone`
- `forbidden_phrases`
- `required_sections`
- `claim_rules`

Recommended rewrite:

Avoid:

```text
Every fee or bonus claim must be treated as a cold hard fact.
```

Prefer:

```text
Every fee or bonus claim must be source-backed, dated, and qualified if requirements or expiry terms are unclear.
```
