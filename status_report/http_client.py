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
# status_report/http_client.py

import sys
import aiohttp
from .data_models import StatusData


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
            print(
                f"Warning: Failed to fetch status from {server}. Error: {ex}", file=sys.stderr)
            # Return a "null" StatusData or raise. We'll choose to raise so aggregator can skip.
            raise
