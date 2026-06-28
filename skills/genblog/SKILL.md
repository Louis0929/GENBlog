---
name: genblog
description: Claim-gated crypto affiliate and pSEO blog generation workflow. Use when Codex needs to generate, review, humanize, or export crypto comparison articles from campaign data such as mock_campaign.json, writer_brief.json, signup bonus claims, fee/onramp claims, affiliate platform records, or when the user asks for GenBlog, humanized blog, crypto pSEO content, information-gain articles, or BlogPostStructure output.
---

# GenBlog

## Core Rule

Keep facts, math, and wording separate:

```text
campaign data decides facts
Python computes information gain
search creates evidence notes only
LLM or baseline generator writes wording
editorial gate decides publishability
```

Do not let search results or an LLM overwrite campaign claims automatically.

## Standard Workflow

1. Load campaign data from JSON or the current pipeline-compatible source.
2. Validate claim-level data before generation.
3. Compute information gain: realistic bonus ROI, deposit burden, trading-volume hurdle, bonus delta, fee/onramp friction.
4. Optionally collect search evidence with `mock` or `google_cse`; treat it as notes, not source-of-truth facts.
5. Generate a `BlogPostStructure` using the baseline generator or an LLM prompt package.
6. Run the editorial gate.
7. Export `generated_post.json` and `article.html`.

## Quick Start

From the repo root, run:

```powershell
python skills/genblog/scripts/run_genblog.py --input data/mock_campaign.json --job-id job_binance_vs_bybit_brazil_bonus --search-provider mock --output-dir outputs/binance-vs-bybit-brazil
```

Expected outputs:

```text
outputs/binance-vs-bybit-brazil/generated_post.json
outputs/binance-vs-bybit-brazil/article.html
outputs/binance-vs-bybit-brazil/writer_brief.json
outputs/binance-vs-bybit-brazil/llm_prompt_package.json
outputs/binance-vs-bybit-brazil/search_evidence.json
```

## Search Provider Rules

- Use `mock` for deterministic offline testing.
- Use `google_cse` only when `GOOGLE_API_KEY` and `GOOGLE_CSE_ID` exist.
- If Google credentials are missing or the request fails, continue without enrichment and record the skip/error in evidence output.
- Never promote search snippets into verified claims without a later claim-review step.

## References

- Read `references/editorial-standard.md` before writing or reviewing a crypto affiliate article.
- Read `references/data-contract.md` when validating new campaign data, adding claim types, or debugging validation failures.

## Output Contract

The article generator must return:

```json
{
  "h1_title": "string",
  "meta_description": "string",
  "target_keyword": "string",
  "html_content": "string",
  "schema_markup": "JSON-LD string",
  "winner_verdict": "string"
}
```
