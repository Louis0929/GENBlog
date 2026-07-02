from __future__ import annotations

import argparse
import json
from pathlib import Path

from .export import export_article
from .gate import evaluate_article
from .generator import generate_blog_post, validate_blog_post
from .insight import build_writer_brief, compute_information_gain
from .llm_prompt import build_llm_prompt_package
from .search import search_evidence
from .validation import build_comparison_bundle, validate_campaign


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate crypto pSEO mock data and build a writer brief.")
    parser.add_argument("--input", required=True, help="Path to campaign JSON.")
    parser.add_argument("--job-id", required=True, help="Article job id to process.")
    parser.add_argument("--brief-output", help="Optional path to write the writer brief JSON.")
    parser.add_argument("--post-output", help="Optional path to write the generated BlogPostStructure JSON.")
    parser.add_argument("--llm-prompt-output", help="Optional path to write a provider-agnostic LLM prompt package.")
    parser.add_argument("--html-output", help="Optional path to write the generated article HTML.")
    parser.add_argument("--output-dir", help="Optional directory to write generated_post.json and article.html.")
    parser.add_argument("--search-provider", choices=["none", "mock", "google_cse"], default="none")
    parser.add_argument("--evidence-output", help="Optional path to write search evidence notes JSON.")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = validate_campaign(data)

    print("Validation")
    print(f"- passed: {report.passed}")
    print(f"- errors: {len(report.errors())}")
    print(f"- warnings: {len(report.warnings())}")
    for issue in report.issues:
        print(f"  [{issue.severity}] {issue.path}: {issue.message}")

    if not report.passed:
        raise SystemExit(1)

    bundle = build_comparison_bundle(data, args.job_id)
    info = compute_information_gain(bundle)
    brief = build_writer_brief(bundle, info)

    print("\nComputed Insights")
    for insight in info.computed_insights:
        print(f"- {insight}")

    print("\nWriter Brief")
    print(json.dumps(brief, indent=2, ensure_ascii=False))

    if args.brief_output:
        Path(args.brief_output).write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote brief: {args.brief_output}")

    if args.llm_prompt_output:
        prompt_package = build_llm_prompt_package(brief)
        Path(args.llm_prompt_output).write_text(json.dumps(prompt_package, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote LLM prompt package: {args.llm_prompt_output}")

    evidence = search_evidence(f"{bundle.job['target_keyword']} {bundle.job['region']} crypto bonus fees", args.search_provider)
    if args.search_provider != "none":
        print("\nSearch Evidence")
        print(f"- provider: {evidence['provider']}")
        print(f"- status: {evidence['status']}")
        print(f"- note: {evidence['note']}")
    if args.evidence_output:
        Path(args.evidence_output).write_text(json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nWrote evidence: {args.evidence_output}")

    if args.post_output or args.html_output or args.output_dir:
        post = generate_blog_post(brief)
        gate_report = evaluate_article(post, brief)
        post_issues = gate_report["issues"]
        print("\nGenerated BlogPostStructure")
        print(json.dumps(post, indent=2, ensure_ascii=False))
        print("\nEditorial Gate")
        print(f"- passed: {gate_report['passed']}")
        print(f"- weighted_score: {gate_report['weighted_score']}")
        print(f"- scores: {json.dumps(gate_report['scores'], ensure_ascii=False)}")
        for issue in post_issues:
            print(f"  [error] {issue}")
        if post_issues:
            raise SystemExit(1)
        if args.post_output:
            Path(args.post_output).write_text(json.dumps(post, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\nWrote post: {args.post_output}")
        if args.output_dir:
            outputs = export_article(post, args.output_dir, evidence)
            print(f"\nWrote article JSON: {outputs['json']}")
            print(f"Wrote article HTML: {outputs['html']}")
        if args.html_output:
            from .export import render_article_html

            Path(args.html_output).write_text(render_article_html(post, evidence), encoding="utf-8")
            print(f"\nWrote HTML: {args.html_output}")


if __name__ == "__main__":
    main()
