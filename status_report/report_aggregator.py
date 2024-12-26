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
# status_report/report_aggregator.py

from typing import Dict, Tuple, List
from .data_models import StatusData


class ReportAggregator:
    """
    Aggregates success rates by (Application, Version).
    success_rate = (sum of success_counts) / (sum of request_counts).
    """

    def __init__(self):
        # Dictionary keyed by (application, version): (total_success, total_request)
        self._agg_data: Dict[Tuple[str, str], Tuple[int, int]] = {}

    def add_status(self, status: StatusData):
        """
        Incorporate one server's StatusData into aggregator.
        """
        key = (status.application, status.version)
        existing = self._agg_data.get(key, (0, 0))
        total_success = existing[0] + status.success_count
        total_requests = existing[1] + status.request_count
        self._agg_data[key] = (total_success, total_requests)

    def get_results(self) -> List[dict]:
        """
        Returns a list of results, where each entry is a dict:
           {
             "application": str,
             "version": str,
             "total_requests": int,
             "total_success": int,
             "success_rate": float
           }
        We skip entries where total_requests == 0 to avoid division by zero.
        """
        results = []
        for (app, ver), (succ, req) in self._agg_data.items():
            if req > 0:
                success_rate = succ / req
            else:
                success_rate = 0.0

            results.append({
                "application": app,
                "version": ver,
                "total_requests": req,
                "total_success": succ,
                "success_rate": success_rate
            })
        return results
