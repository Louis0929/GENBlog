from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path
from typing import Any


JsonDict = dict[str, Any]


def render_article_html(post: JsonDict, evidence: JsonDict | None = None) -> str:
    evidence_html = _render_evidence(evidence)
    schema_markup = post.get("schema_markup", "{}")
    updated_label = date.today().strftime("%d %b %Y")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(post["h1_title"])}</title>
  <meta name="description" content="{escape(post["meta_description"])}">
  <style>
    :root {{
      --bg: #f6f7f9;
      --surface: #ffffff;
      --ink: #20242a;
      --muted: #606b7b;
      --line: #dde3ec;
      --brand: #f28c28;
      --brand-dark: #d46f00;
      --blue: #1457a8;
      --blue-soft: #eaf2ff;
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
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      height: 58px;
      background: var(--surface);
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 18px;
    }}
    .topbar-inner {{
      width: min(1120px, 100%);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
    }}
    .brandmark {{
      color: var(--blue);
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
    }}
    .brandmark span {{ color: var(--brand); }}
    .menu-dot {{
      width: 34px;
      height: 34px;
      border: 1px solid var(--line);
      border-radius: 999px;
      display: grid;
      place-items: center;
      color: var(--blue);
      font-weight: 700;
    }}
    .campaign-banner {{
      height: 54px;
      background: linear-gradient(90deg, #03677a, #10bfd0);
    }}
    .page-shell {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 26px 0 48px;
    }}
    .breadcrumbs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: center;
      margin: 0 0 16px;
      color: var(--muted);
      font-size: 14px;
    }}
    .breadcrumbs a {{
      color: var(--muted);
      text-decoration: none;
    }}
    .hero {{
      padding: 0;
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
      max-width: 900px;
      margin: 14px 0 0;
      color: var(--muted);
      font-size: 17px;
    }}
    .updated {{
      margin: 8px 0 0;
      color: var(--muted);
      font-size: 14px;
      font-weight: 700;
    }}
    .trust-strip {{
      margin: 24px 0 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--surface);
      overflow: hidden;
    }}
    .trust-item {{
      padding: 14px 16px;
      font-size: 14px;
      border-bottom: 1px solid var(--line);
    }}
    .trust-item:last-child {{ border-bottom: 0; }}
    .trust-item:first-child {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      font-size: 17px;
    }}
    .trust-item strong {{ display: block; margin-bottom: 3px; }}
    .category-strip {{
      display: flex;
      gap: 8px;
      overflow-x: auto;
      padding: 4px 0 14px;
      margin: 0 0 10px;
      scrollbar-width: thin;
    }}
    .category-chip {{
      flex: 0 0 auto;
      border: 1px solid var(--line);
      border-radius: 7px;
      background: var(--surface);
      color: var(--ink);
      padding: 8px 14px;
      font-size: 15px;
      font-weight: 700;
      text-decoration: none;
      white-space: nowrap;
    }}
    .category-chip.active {{
      border-color: var(--blue);
      background: var(--blue-soft);
      color: var(--blue);
    }}
    .summary-heading {{
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 8px 0 14px;
      color: var(--ink);
      font-size: 18px;
      font-weight: 800;
    }}
    .summary-heading span:first-child {{
      font-size: 24px;
      line-height: 1;
      font-weight: 400;
    }}
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
      background: #f4f6f9;
      color: #4a5361;
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
    td:nth-child(2):not(:last-child),
    td:nth-child(3):not(:last-child) {{
      font-weight: 700;
    }}
    td:nth-child(3),
    td:nth-child(4) {{
      color: #133f78;
    }}
    td a[rel~="sponsored"] {{
      display: inline-block;
      min-width: 92px;
      text-align: center;
      padding: 9px 14px;
      border-radius: 6px;
      border: 1px solid var(--brand);
      background: var(--surface);
      color: var(--brand-dark);
      font-weight: 700;
      text-decoration: none;
    }}
    td a[rel~="sponsored"]:hover {{ background: #fff4e9; }}
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
      .article-card {{ padding: 16px; }}
      h1 {{ font-size: 26px; }}
      .topbar {{ height: 48px; }}
      .brandmark {{ font-size: 24px; }}
      .campaign-banner {{ height: 48px; }}
      table {{ display: block; overflow-x: auto; white-space: nowrap; }}
      th, td {{ min-width: 140px; }}
    }}
  </style>
  <script type="application/ld+json">{schema_markup}</script>
</head>
<body>
  <header class="topbar" aria-label="Site header">
    <div class="topbar-inner">
      <div class="menu-dot" aria-hidden="true">☰</div>
      <div class="brandmark">Gen<span>Blog</span></div>
      <div class="menu-dot" aria-hidden="true">◎</div>
    </div>
  </header>
  <div class="campaign-banner" aria-hidden="true"></div>
  <main class="page-shell">
    <nav class="breadcrumbs" aria-label="Breadcrumb">
      <a href="#">Home</a><span>/</span><a href="#">Crypto Exchanges</a><span>/</span><span>{escape(post["target_keyword"])}</span>
    </nav>
    <section class="hero">
      <p class="eyebrow">Crypto bonus comparison</p>
      <h1>{escape(post["h1_title"])}</h1>
      <p class="updated">Updated: {updated_label}</p>
      <p class="dek">{escape(post["meta_description"])}</p>
      <div class="trust-strip" aria-label="Editorial checks">
        <div class="trust-item"><strong>Why Trust GenBlog</strong><span>⌄</span></div>
        <div class="trust-item"><strong>Realistic value first</strong>Headline bonuses are checked against unlock requirements.</div>
        <div class="trust-item"><strong>Claim-gated data</strong>Fees, bonuses, and fiat rails keep visible source notes.</div>
        <div class="trust-item"><strong>Affiliate disclosure</strong>CTA links use sponsored/nofollow attributes.</div>
      </div>
    </section>
    <div class="category-strip" aria-label="Comparison filters">
      <a class="category-chip active" href="#">All exchanges</a>
      <a class="category-chip" href="#">Best bonus</a>
      <a class="category-chip" href="#">Low deposit</a>
      <a class="category-chip" href="#">Pix onramp</a>
      <a class="category-chip" href="#">Fee friction</a>
      <a class="category-chip" href="#">Beginner fit</a>
    </div>
    <div class="summary-heading"><span>+</span><span>Summary Products</span></div>
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
