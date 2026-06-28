import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from crypto_pseo.insight import compute_information_gain
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


if __name__ == "__main__":
    unittest.main()
