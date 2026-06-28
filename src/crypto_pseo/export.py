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
  <title>{escape(post["h1_title"])}</title>
  <meta name="description" content="{escape(post["meta_description"])}">
  <script type="application/ld+json">{schema_markup}</script>
</head>
<body>
  <main>
    <h1>{escape(post["h1_title"])}</h1>
{post["html_content"]}
{evidence_html}
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
    <section>
      <h2>Search Evidence Notes</h2>
      <p>{escape(evidence.get("note", "No search evidence available."))}</p>
    </section>"""
    items = "\n".join(
        f'      <li><a href="{escape(item.get("url", ""))}">{escape(item.get("title", ""))}</a>: {escape(item.get("snippet", ""))}</li>'
        for item in results
    )
    return f"""
    <section>
      <h2>Search Evidence Notes</h2>
      <p>{escape(evidence.get("note", ""))}</p>
      <ul>
{items}
      </ul>
    </section>"""
