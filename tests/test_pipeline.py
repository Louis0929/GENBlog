import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import run

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crypto_pseo.export import export_article
from crypto_pseo.generator import generate_blog_post, validate_blog_post
from crypto_pseo.insight import build_writer_brief
from crypto_pseo.insight import compute_information_gain
from crypto_pseo.llm_prompt import build_llm_prompt_package
from crypto_pseo.search import search_evidence
from crypto_pseo.validation import build_comparison_bundle, validate_campaign


def _brief_and_post():
    data = json.loads(Path("data/mock_campaign.json").read_text(encoding="utf-8"))
    bundle = build_comparison_bundle(data, "job_binance_vs_bybit_brazil_bonus")
    info = compute_information_gain(bundle)
    brief = build_writer_brief(bundle, info)
    post = generate_blog_post(brief)
    return brief, post


class PipelineTest(unittest.TestCase):
    def test_mock_campaign_validates_and_computes_insights(self):
        data = json.loads(Path("data/mock_campaign.json").read_text(encoding="utf-8"))
        report = validate_campaign(data)
        self.assertTrue(report.passed)

        bundle = build_comparison_bundle(data, "job_binance_vs_bybit_brazil_bonus")
        info = compute_information_gain(bundle)

        self.assertEqual(info.metrics_a.name, "Binance")
        self.assertEqual(info.metrics_b.name, "Bybit")
        self.assertEqual(info.metrics_a.realistic_bonus_roi, 3)
        self.assertEqual(info.metrics_b.realistic_bonus_roi, 0.1)
        self.assertEqual(info.deposit_burden_ratio, 50)
        self.assertEqual(info.low_budget_winner, "Binance")

    def test_generator_outputs_blog_post_structure(self):
        data = json.loads(Path("data/mock_campaign.json").read_text(encoding="utf-8"))
        bundle = build_comparison_bundle(data, "job_binance_vs_bybit_brazil_bonus")
        info = compute_information_gain(bundle)
        brief = build_writer_brief(bundle, info)

        post = generate_blog_post(brief)
        issues = validate_blog_post(post, brief)

        self.assertFalse(issues)
        self.assertEqual(post["target_keyword"], "Binance vs Bybit bonus Brazil 2026")
        self.assertIn("html_content", post)
        self.assertIn("winner_verdict", post)

    def test_llm_prompt_package_contains_schema_and_computed_insights(self):
        data = json.loads(Path("data/mock_campaign.json").read_text(encoding="utf-8"))
        bundle = build_comparison_bundle(data, "job_binance_vs_bybit_brazil_bonus")
        info = compute_information_gain(bundle)
        brief = build_writer_brief(bundle, info)

        package = build_llm_prompt_package(brief)

        self.assertEqual(package["output_schema_name"], "BlogPostStructure")
        self.assertIn("system_prompt", package)
        self.assertIn("user_payload", package)
        self.assertIn("computed_insights", package["user_payload"]["information_gain"])
        self.assertIn("html_content", package["output_schema"]["properties"])

    def test_skill_wrapper_exports_json_and_html(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run(
                [
                    sys.executable,
                    "skills/genblog/scripts/run_genblog.py",
                    "--input",
                    "data/mock_campaign.json",
                    "--job-id",
                    "job_binance_vs_bybit_brazil_bonus",
                    "--search-provider",
                    "mock",
                    "--output-dir",
                    tmpdir,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(Path(tmpdir, "generated_post.json").exists())
            self.assertTrue(Path(tmpdir, "article.html").exists())
            self.assertTrue(Path(tmpdir, "writer_brief.json").exists())
            self.assertTrue(Path(tmpdir, "llm_prompt_package.json").exists())
            self.assertTrue(Path(tmpdir, "search_evidence.json").exists())

    def test_search_mock_provider_returns_deterministic_evidence(self):
        evidence = search_evidence("Binance Bybit Brazil Pix", "mock")

        self.assertEqual(evidence["provider"], "mock")
        self.assertEqual(evidence["status"], "ok")
        self.assertEqual(len(evidence["results"]), 2)
        self.assertIn("Pix", evidence["results"][0]["snippet"])

    def test_google_cse_missing_env_is_non_fatal(self):
        old_key = os.environ.pop("GOOGLE_API_KEY", None)
        old_cse = os.environ.pop("GOOGLE_CSE_ID", None)
        try:
            evidence = search_evidence("Binance Bybit Brazil Pix", "google_cse")
        finally:
            if old_key is not None:
                os.environ["GOOGLE_API_KEY"] = old_key
            if old_cse is not None:
                os.environ["GOOGLE_CSE_ID"] = old_cse

        self.assertEqual(evidence["provider"], "google_cse")
        self.assertEqual(evidence["status"], "skipped")
        self.assertEqual(evidence["results"], [])

    def test_article_gate_rejects_forbidden_phrase(self):
        brief, post = _brief_and_post()
        post["html_content"] += "<p>This is a game-changer.</p>"

        issues = validate_blog_post(post, brief)

        self.assertIn("Forbidden phrase found: game-changer", issues)

    def test_article_gate_rejects_invalid_json_ld(self):
        brief, post = _brief_and_post()
        post["schema_markup"] = "{not valid json"

        issues = validate_blog_post(post, brief)

        self.assertIn("schema_markup must be valid JSON-LD.", issues)

    def test_article_gate_rejects_missing_computed_insight(self):
        brief, post = _brief_and_post()
        post["html_content"] = post["html_content"].replace(
            "Binance has a realistic bonus ROI of 300.0%, versus 10.0% for Bybit.",
            "",
        )

        issues = validate_blog_post(post, brief)

        self.assertTrue(any(issue.startswith("Computed insight not reflected") for issue in issues))

    def test_export_article_writes_html_with_schema(self):
        _, post = _brief_and_post()
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = export_article(post, tmpdir)

            html = Path(paths["html"]).read_text(encoding="utf-8")
            self.assertIn("<h1>Binance vs Bybit Bonus in Brazil", html)
            self.assertIn('type="application/ld+json"', html)


if __name__ == "__main__":
    unittest.main()
