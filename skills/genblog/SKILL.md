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

## Style System

GenBlog supports multiple personas over time. The default is `lexington_humanized_affiliate_v1`:

- Stay neutral and affiliate-friendly.
- Write like a careful human analyst, not a corporate review page.
- Prioritize users who may open an account through an affiliate link.
- Show real data first: realistic bonus, deposit, trading volume, fee/onramp friction.
- Use MoneyHero-style comparison tables with clear "better fit" rows.
- Use honest CTAs such as `Claim the bonus`, but only after requirements are visible.
- Avoid stacked adjectives and AI-polished phrases. Prefer numbers and caveats.
- If a platform lacks a clear numerical advantage in a multi-platform comparison, highlight source-backed ecosystem utility, local onboarding fit, or benefit evidence instead of fabricating a forced win.

SEO intro rule: do not write a generic intro just to target keywords. Use at most one short context sentence, then give the verdict.

## Standard Workflow

1. Load campaign data from JSON or the current pipeline-compatible source.
2. Validate claim-level data before generation.
3. Enforce jurisdiction gating from `allowed_regions`, `restricted_regions`, and `compliance_disclaimer`.
4. Compute information gain: realistic bonus ROI, expected net value after trading-fee drag, deposit burden, trading-volume hurdle, bonus delta, fee/onramp friction.
5. Optionally collect search evidence with `mock` or `google_cse`; treat it as notes, not source-of-truth facts.
6. Generate a `BlogPostStructure` using the baseline generator or an LLM prompt package.
7. Run the editorial gate with scores. If blocked by style, missing facts, invalid schema, or disclaimer issues, append `revision_reasons` to the retry context and retry up to the configured maximum.
8. Export `generated_post.json` and `article.html`.

Comparison jobs can include two or more platforms. For three-way posts, use verdict rows such as "Small first deposit", "Highest realistic bonus", and "Best bonus ROI" instead of forcing a single overall winner.

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
  "winner_verdict": "string",
  "mentioned_entities": ["string"],
  "compliance_disclaimer": "string"
}
```

`schema_markup` must include `FAQPage`, `Product`, or `Review` JSON-LD. Prefer `FAQPage` plus product entries for comparison pages.
