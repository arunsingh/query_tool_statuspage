#!/usr/bin/env python3
"""
Machine-code style Python3 application (demonstrating OOP, SOLID, TDD/BDD, etc.)
that queries multiple servers' /status endpoints, aggregates success rates by
Application & Version, and produces two output formats:
  1) Human-readable text to stdout
  2) Machine-parseable JSON file

See the included tests (bottom of file or separate test directory) for TDD/BDD
examples.

Author: Arun Singh
Date: 2024-12-21
"""

import os
import sys
import json
import asyncio
import aiohttp
from typing import Dict, List, Tuple
import unittest

################################################################################
# Configuration (12-Factor alignment)
################################################################################

class Config:
    """
    Holds configuration details, respecting environment variables for easy
    runtime override. Demonstrates 12-Factor principle of config via environment.
    """
    # Maximum concurrency for fetching server status
    MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "50"))
    
    # Timeout for HTTP requests (in seconds)
    TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "5"))
    
    # Output file name
    OUTPUT_FILE = os.getenv("OUTPUT_FILE", "report.json")


################################################################################
# Data Models
################################################################################

class StatusData:
    """
    Represents the data returned by each server's /status endpoint.
    We assume the JSON has the following fields:
        "Application", "Version", "Uptime", "Request_Count", "Error_Count", "Success_Count"
    """
    __slots__ = ["application", "version", "uptime", "request_count", "error_count", "success_count"]
    
    def __init__(self, application: str, version: str, uptime: float,
                 request_count: int, error_count: int, success_count: int):
        self.application = application
        self.version = version
        self.uptime = uptime
        self.request_count = request_count
        self.error_count = error_count
        self.success_count = success_count
    
    @classmethod
    def from_json(cls, data: dict):
        """
        Create StatusData from a JSON dictionary.
        Raises ValueError if required fields are missing or invalid.
        """
        try:
            return cls(
                application=data["Application"],
                version=data["Version"],
                uptime=float(data["Uptime"]),
                request_count=int(data["Request_Count"]),
                error_count=int(data["Error_Count"]),
                success_count=int(data["Success_Count"]),
            )
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid status JSON structure: {e}")


################################################################################
# HTTP Client (Factory + Strategy Pattern - might swap out how we fetch)
################################################################################

class ServerStatusClient:
    """
    A client responsible for fetching status data from servers.
    Demonstrates SOLID (single responsibility: just fetch data),
    and we can apply a Factory or Strategy pattern if we want to swap out
    the transport layer (aiohttp, requests, etc.).
    """

    def __init__(self, session: aiohttp.ClientSession, timeout: int):
        """
        :param session: an aiohttp.ClientSession for re-use
        :param timeout: HTTP request timeout in seconds
        """
        self.session = session
        self.timeout = timeout

    async def fetch_status(self, server: str) -> StatusData:
        """
        Fetch /status endpoint from a given server.
        Example: http://ServerA/status

        :param server: server name or IP
        :return: StatusData object or raises an exception on failure
        """
        url = f"http://{server}/status"
        try:
            async with self.session.get(url, timeout=self.timeout) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return StatusData.from_json(data)
        except Exception as ex:
            # Log to stderr, but do not kill the entire process
            print(f"Warning: Failed to fetch status from {server}. Error: {ex}", file=sys.stderr)
            # Return a "null" StatusData or raise. We'll choose to raise so aggregator can skip.
            raise


################################################################################
# Report Aggregator
################################################################################

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

    def get_results(self):
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


################################################################################
# Report Writer (Strategy pattern for outputting in various formats)
################################################################################

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
        # Add a naive HATEOAS link for demonstration.
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


################################################################################
# Main Tool (Orchestration)
################################################################################

class StatusTool:
    """
    Orchestrates reading servers from a file, fetching status concurrently,
    aggregating results, and writing the final reports.
    """

    def __init__(self, servers_file: str, output_file: str):
        self.servers_file = servers_file
        self.output_file = output_file

    async def run(self):
        # 1) Read list of servers
        servers = self._read_servers(self.servers_file)

        # 2) Setup aggregator
        aggregator = ReportAggregator()

        # 3) Fetch all statuses concurrently
        conn = aiohttp.TCPConnector(limit=Config.MAX_CONCURRENCY)
        async with aiohttp.ClientSession(connector=conn) as session:
            client = ServerStatusClient(session, Config.TIMEOUT)
            tasks = []
            for server in servers:
                tasks.append(self._fetch_and_aggregate(client, server, aggregator))

            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)

        # 4) Produce results
        results = aggregator.get_results()

        # 5) Write reports
        writer = ReportWriter(self.output_file)
        writer.write(results)

    @staticmethod
    def _read_servers(filepath: str) -> List[str]:
        """
        Reads servers from file, ignoring blank lines and comments (#).
        """
        servers = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                servers.append(line)
        return servers

    @staticmethod
    async def _fetch_and_aggregate(client: ServerStatusClient,
                                   server: str,
                                   aggregator: ReportAggregator):
        """
        Helper for concurrency: fetch status from one server, add to aggregator if successful.
        We catch exceptions so one failing server won't stop the entire run.
        """
        try:
            status_data = await client.fetch_status(server)
            aggregator.add_status(status_data)
        except Exception as e:
            # We log the error, but do not re-raise
            print(f"[ERROR] Could not process server '{server}': {e}", file=sys.stderr)


################################################################################
# Entry Point
################################################################################

def main():
    """
    Main entry point. Usage:
        python3 main.py [servers_file]
    """
    if len(sys.argv) < 2:
        print("Usage: python3 main.py [servers_file]", file=sys.stderr)
        sys.exit(1)

    servers_file = sys.argv[1]
    # Optionally use environment variable for output file
    output_file = Config.OUTPUT_FILE

    tool = StatusTool(servers_file, output_file)

    # Run the asynchronous logic
    asyncio.run(tool.run())


if __name__ == "__main__":
    main()


################################################################################
# Test Cases (TDD & BDD demonstration)
# In a real project, place these in a separate /tests/ directory.
################################################################################

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

class TestStatusData(unittest.TestCase):
    def test_from_json_valid(self):
        data = {
            "Application": "Cache1",
            "Version": "1.001",
            "Uptime": "123.45",
            "Request_Count": "100",
            "Error_Count": "10",
            "Success_Count": "90"
        }
        sd = StatusData.from_json(data)
        self.assertEqual(sd.application, "Cache1")
        self.assertEqual(sd.version, "1.001")
        self.assertEqual(sd.uptime, 123.45)
        self.assertEqual(sd.request_count, 100)
        self.assertEqual(sd.error_count, 10)
        self.assertEqual(sd.success_count, 90)

    def test_from_json_invalid(self):
        data = {
            "App": "MissingKeys"
        }
        with self.assertRaises(ValueError):
            StatusData.from_json(data)


# Additional tests might mock the HTTP client or test the concurrency logic,
# but this gives a flavor of how TDD might be done.

################################################################################
# End of file
################################################################################
