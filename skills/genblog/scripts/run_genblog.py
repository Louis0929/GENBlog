from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_DIR))

from crypto_pseo.export import export_article
from crypto_pseo.generator import generate_blog_post, validate_blog_post
from crypto_pseo.insight import build_writer_brief, compute_information_gain
from crypto_pseo.llm_prompt import build_llm_prompt_package
from crypto_pseo.search import search_evidence
from crypto_pseo.validation import build_comparison_bundle, validate_campaign


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the GenBlog crypto pSEO workflow.")
    parser.add_argument("--input", required=True, help="Campaign JSON input path.")
    parser.add_argument("--job-id", required=True, help="Article job id.")
    parser.add_argument("--output-dir", required=True, help="Directory for generated outputs.")
    parser.add_argument("--search-provider", choices=["none", "mock", "google_cse"], default="mock")
    args = parser.parse_args()

    input_path = _resolve_path(args.input)
    output_dir = _resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    report = validate_campaign(data)
    if not report.passed:
        for issue in report.errors():
            print(f"[error] {issue.path}: {issue.message}", file=sys.stderr)
        raise SystemExit(1)

    bundle = build_comparison_bundle(data, args.job_id)
    info = compute_information_gain(bundle)
    brief = build_writer_brief(bundle, info)
    evidence = search_evidence(f"{bundle.job['target_keyword']} {bundle.job['region']} crypto bonus fees", args.search_provider)
    prompt_package = build_llm_prompt_package(brief)
    post = generate_blog_post(brief)
    post_issues = validate_blog_post(post, brief)
    if post_issues:
        for issue in post_issues:
            print(f"[error] {issue}", file=sys.stderr)
        raise SystemExit(1)

    (output_dir / "writer_brief.json").write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "llm_prompt_package.json").write_text(json.dumps(prompt_package, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "search_evidence.json").write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    paths = export_article(post, output_dir, evidence)

    print(f"Wrote article JSON: {paths['json']}")
    print(f"Wrote article HTML: {paths['html']}")


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


if __name__ == "__main__":
    main()
