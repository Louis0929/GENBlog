# Crypto pSEO Affiliate Pipeline MVP

This workspace contains a small, runnable MVP for a crypto affiliate pSEO content pipeline.

It is designed around one core rule:

> DB decides facts. Python decides math. The LLM decides wording. The editorial gate decides whether it is publishable.

## What It Does

- Validates normalized Mongo-style campaign data.
- Checks claim-level requirements for signup bonuses, fees, fiat onramps, regional availability, and sources.
- Computes information gain before any LLM call.
- Builds a strict writer brief for a skeptical crypto analyst persona.
- Exports the brief as JSON so it can be passed to Claude, Gemini, or another writer agent.
- Exports a provider-agnostic LLM prompt package for structured-output generation.
- Generates a local baseline `BlogPostStructure` JSON for end-to-end testing.
- Provides a repo-local `genblog` skill wrapper that exports article JSON and HTML.
- Supports optional search evidence with deterministic `mock` and credential-gated `google_cse` providers.
- Renders a MoneyHero-inspired comparison article layout with a verdict hero, trust strip, tables, and CTA buttons.
- Supports benefit-lens claims for miles, lounge access, card rewards, fee rebates, application eligibility, and localized onboarding.

## Run

```powershell
python run_pipeline.py --input data/mock_campaign.json --job-id job_binance_vs_bybit_brazil_bonus --brief-output data/writer_brief.json --llm-prompt-output data/llm_prompt_package.json --post-output data/generated_post.json
```

The command prints validation results, computed insights, and a writer brief.

Run the GenBlog skill wrapper:

```powershell
python skills/genblog/scripts/run_genblog.py --input data/mock_campaign.json --job-id job_binance_vs_bybit_brazil_bonus --search-provider mock --output-dir outputs/binance-vs-bybit-brazil
```

Generate the OKX comparison mock article:

```powershell
python skills/genblog/scripts/run_genblog.py --input data/mock_campaign.json --job-id job_bybit_vs_okx_brazil_bonus --search-provider mock --output-dir outputs/bybit-vs-okx-brazil
```

## Project Shape

```text
data/mock_campaign.json
docs/validation_contract.md
skills/genblog/
src/crypto_pseo/
  __init__.py
  cli.py
  contract.py
  export.py
  generator.py
  insight.py
  llm_prompt.py
  search.py
  validation.py
tests/
  test_pipeline.py
```

Run the stdlib test suite:

```powershell
python -m unittest discover
```

## Next Integration Points

- Replace the JSON loader with a MongoDB loader.
- Add Pydantic models in the FastAPI service using the same field contract.
- Add Perplexity as a freshness/evidence checker, not as the source of truth.
- Send the generated writer brief into a Structured Output writer agent.
