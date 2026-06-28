import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crypto_pseo.generator import generate_blog_post, validate_blog_post
from crypto_pseo.insight import build_writer_brief
from crypto_pseo.insight import compute_information_gain
from crypto_pseo.llm_prompt import build_llm_prompt_package
from crypto_pseo.validation import build_comparison_bundle, validate_campaign


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


if __name__ == "__main__":
    unittest.main()
