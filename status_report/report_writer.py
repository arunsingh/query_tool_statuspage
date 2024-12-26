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
# status_report/report_writer.py

import json
from typing import List


class ReportWriter:
    """
    Writes aggregated results in two formats:
      1. Human-readable text to stdout
      2. JSON to a local file (downstream consumption).
    Also demonstrates a naive HATEOAS approach by embedding a reference link
    for each record (imagine we have a route /apps/<application>/<version>).
    """

    def __init__(self, output_file: str):
        self.output_file = output_file

    def write(self, results: List[dict]):
        # 1) Write to stdout (human-readable)
        print("=" * 60)
        print("SUCCESS RATE REPORT")
        print("=" * 60)

        for res in results:
            print(f"{res['application']} (v{res['version']}): "
                  f"Success Rate={res['success_rate']:.2f} "
                  f"(Requests={res['total_requests']}, Success={res['total_success']})")

        # 2) Write JSON to file
        data_with_links = []
        for item in results:
            item_copy = dict(item)  # shallow copy
            item_copy["links"] = {
                "self": f"/apps/{item['application']}/{item['version']}/info"
            }
            data_with_links.append(item_copy)

        with open(self.output_file, "w") as f:
            json.dump(data_with_links, f, indent=2)

        print(f"\nWrote JSON report to {self.output_file}")
