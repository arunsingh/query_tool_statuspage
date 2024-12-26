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
# status_report/tool.py

import sys
import asyncio
import aiohttp
from typing import List
from .config import Config
from .report_aggregator import ReportAggregator
from .report_writer import ReportWriter
from .http_client import ServerStatusClient


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
                tasks.append(self._fetch_and_aggregate(
                    client, server, aggregator))

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
            print(
                f"[ERROR] Could not process server '{server}': {e}", file=sys.stderr)
