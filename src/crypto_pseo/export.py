from __future__ import annotations

import json
from html import escape
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def render_article_html(post: JsonDict, evidence: JsonDict | None = None) -> str:
    evidence_html = _render_evidence(evidence)
    schema_markup = post.get("schema_markup", "{}")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(post["h1_title"])}</title>
  <meta name="description" content="{escape(post["meta_description"])}">
  <style>
    :root {{
      --bg: #f5f7fb;
      --surface: #ffffff;
      --ink: #182230;
      --muted: #5f6b7a;
      --line: #dce3ee;
      --brand: #ff6b00;
      --brand-dark: #c84f00;
      --blue: #1256a3;
      --green: #0f7a4f;
      --warning: #8a5a00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Arial, Helvetica, sans-serif;
      line-height: 1.55;
    }}
    a {{ color: var(--blue); }}
    .page-shell {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 48px;
    }}
    .hero {{
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 28px;
      box-shadow: 0 8px 24px rgba(24, 34, 48, 0.06);
    }}
    .eyebrow {{
      margin: 0 0 8px;
      color: var(--brand-dark);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      margin: 0;
      font-size: 34px;
      line-height: 1.18;
      letter-spacing: 0;
    }}
    .dek {{
      max-width: 760px;
      margin: 14px 0 0;
      color: var(--muted);
      font-size: 17px;
    }}
    .trust-strip {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 12px;
      margin: 16px 0 0;
    }}
    .trust-item {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcff;
      font-size: 14px;
    }}
    .trust-item strong {{ display: block; margin-bottom: 3px; }}
    .article-card {{
      margin-top: 18px;
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(24, 34, 48, 0.05);
    }}
    .article-card h2 {{
      margin: 28px 0 10px;
      font-size: 24px;
      line-height: 1.25;
    }}
    .article-card h2:first-child {{ margin-top: 0; }}
    .article-card h3 {{
      margin: 18px 0 8px;
      font-size: 18px;
    }}
    .article-card p {{ margin: 0 0 14px; }}
    .article-card ul {{ padding-left: 22px; }}
    .article-card li {{ margin: 8px 0; }}
    table {{
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 18px 0 24px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
    }}
    th {{
      background: #edf4ff;
      color: #132f4c;
      font-size: 13px;
      text-align: left;
      padding: 13px 12px;
      border-bottom: 1px solid var(--line);
    }}
    td {{
      padding: 14px 12px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      font-size: 14px;
    }}
    tr:last-child td {{ border-bottom: 0; }}
    tbody tr:nth-child(even) td {{ background: #fafcff; }}
    td:nth-child(2):not(:last-child) {{ font-weight: 700; }}
    td a[rel~="sponsored"] {{
      display: inline-block;
      min-width: 132px;
      text-align: center;
      padding: 10px 13px;
      border-radius: 6px;
      background: var(--brand);
      color: white;
      font-weight: 700;
      text-decoration: none;
    }}
    td a[rel~="sponsored"]:hover {{ background: var(--brand-dark); }}
    p a[rel~="sponsored"] {{
      display: inline-block;
      margin-left: 4px;
      color: var(--brand-dark);
      font-weight: 700;
    }}
    .evidence-box {{
      margin-top: 24px;
      padding: 18px;
      border: 1px solid #f0d28a;
      border-radius: 8px;
      background: #fff8e6;
      color: var(--warning);
    }}
    .evidence-box h2 {{ margin-top: 0; }}
    @media (max-width: 760px) {{
      .page-shell {{ width: min(100% - 20px, 1120px); padding-top: 12px; }}
      .hero, .article-card {{ padding: 18px; }}
      h1 {{ font-size: 26px; }}
      .trust-strip {{ grid-template-columns: 1fr; }}
      table {{ display: block; overflow-x: auto; white-space: nowrap; }}
      th, td {{ min-width: 140px; }}
    }}
  </style>
  <script type="application/ld+json">{schema_markup}</script>
</head>
<body>
  <main class="page-shell">
    <section class="hero">
      <p class="eyebrow">Crypto bonus comparison</p>
      <h1>{escape(post["h1_title"])}</h1>
      <p class="dek">{escape(post["meta_description"])}</p>
      <div class="trust-strip" aria-label="Editorial checks">
        <div class="trust-item"><strong>Realistic value first</strong>Headline bonuses are checked against unlock requirements.</div>
        <div class="trust-item"><strong>Claim-gated data</strong>Fees, bonuses, and fiat rails keep visible source notes.</div>
        <div class="trust-item"><strong>Affiliate disclosure</strong>CTA links use sponsored/nofollow attributes.</div>
      </div>
    </section>
    <article class="article-card">
{post["html_content"]}
{evidence_html}
    </article>
  </main>
</body>
</html>
"""


def export_article(post: JsonDict, output_dir: str | Path, evidence: JsonDict | None = None) -> dict[str, str]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "generated_post.json"
    html_path = directory / "article.html"
    json_path.write_text(json.dumps(post, indent=2, ensure_ascii=False), encoding="utf-8")
    html_path.write_text(render_article_html(post, evidence), encoding="utf-8")
    return {"json": str(json_path), "html": str(html_path)}


def _render_evidence(evidence: JsonDict | None) -> str:
    if not evidence or evidence.get("status") == "skipped":
        return ""
    results = evidence.get("results", [])
    if not results:
        return f"""
    <section class="evidence-box">
      <h2>Search Evidence Notes</h2>
      <p>{escape(evidence.get("note", "No search evidence available."))}</p>
    </section>"""
    items = "\n".join(
        f'      <li><a href="{escape(item.get("url", ""))}">{escape(item.get("title", ""))}</a>: {escape(item.get("snippet", ""))}</li>'
        for item in results
    )
    return f"""
    <section class="evidence-box">
      <h2>Search Evidence Notes</h2>
      <p>{escape(evidence.get("note", ""))}</p>
      <ul>
{items}
      </ul>
    </section>"""
