"""
Machine-code style Python3 application that queries multiple servers' /status endpoints,
aggregates success rates by Application & Version, and produces two output formats:
  1) Human-readable text to stdout
  2) Machine-parseable JSON file

See the included tests (bottom of file or separate test directory) for TDD/BDD
examples.

Author: Arun Singh
Date: 2024-12-21
"""
# tests/test_aggregator.py

import unittest
from status_report.report_aggregator import ReportAggregator
from status_report.data_models import StatusData


class TestAggregator(unittest.TestCase):
    def test_aggregator_basic(self):
        agg = ReportAggregator()

        # Add 2 records for "App1", version "1.0"
        status1 = StatusData("App1", "1.0", 100.0, 10, 2, 8)
        status2 = StatusData("App1", "1.0", 150.0, 20, 5, 15)

        agg.add_status(status1)
        agg.add_status(status2)

        results = agg.get_results()
        self.assertEqual(len(results), 1)
        r = results[0]
        self.assertEqual(r["application"], "App1")
        self.assertEqual(r["version"], "1.0")
        self.assertEqual(r["total_requests"], 30)  # 10 + 20
        self.assertEqual(r["total_success"], 23)   # 8 + 15
        # success_rate = 23 / 30 = 0.7666...
        self.assertAlmostEqual(r["success_rate"], 0.7666, places=3)

    def test_aggregator_multi_app_version(self):
        agg = ReportAggregator()

        # App1 v1.0
        agg.add_status(StatusData("App1", "1.0", 100.0, 10, 1, 9))
        # App1 v2.0
        agg.add_status(StatusData("App1", "2.0", 50.0, 5, 2, 3))
        # App2 v1.0
        agg.add_status(StatusData("App2", "1.0", 200.0, 20, 2, 18))

        results = agg.get_results()
        self.assertEqual(len(results), 3)


if __name__ == '__main__':
    unittest.main()
