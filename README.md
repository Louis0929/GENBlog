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

## Run

```powershell
python run_pipeline.py --input data/mock_campaign.json --job-id job_binance_vs_bybit_brazil_bonus
```

The command prints validation results, computed insights, and a writer brief.

## Project Shape

```text
data/mock_campaign.json
docs/validation_contract.md
src/crypto_pseo/
  __init__.py
  cli.py
  contract.py
  insight.py
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
