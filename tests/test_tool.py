"""
Machine-code style Python3 application that queries multiple servers' /status endpoints,
aggregates success rates by Application & Version, and produces two output formats:
  1) Human-readable text to stdout
  2) Machine-parseable JSON file

See the included tests (bottom of file or separate test directory) for TDD/BDD
examples.

It will test the orchestration in StatusTool. We might again mock the HTTP to avoid real networking:

Author: Arun Singh
Date: 2024-12-21
"""
# tests/test_tool.py

import unittest
from unittest.mock import patch, AsyncMock
import aiohttp
import asyncio
import os
from status_report.tool import StatusTool
from status_report.data_models import StatusData


class TestTool(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        # Setup code if needed
        pass

    async def test_run_with_mock(self):
        # Here we can patch _fetch_and_aggregate or the ServerStatusClient to simulate responses.
        with patch('status_report.tool.ServerStatusClient.fetch_status') as mock_fetch:
            mock_fetch.side_effect = [
                StatusData("App1", "1.0", 100.0, 10, 2, 8),
                StatusData("App2", "2.0", 50.0, 5, 0, 5),
            ]

            # Create a temporary servers.txt
            servers_file = "tmp_servers.txt"
            with open(servers_file, "w") as f:
                f.write("server-0001\nserver-0002\n")

            output_file = "test_report.json"
            tool = StatusTool(servers_file, output_file)
            await tool.run()

            # Check that mock was called twice
            self.assertEqual(mock_fetch.call_count, 2)

            # Clean up
            if os.path.exists(servers_file):
                os.remove(servers_file)
            if os.path.exists(output_file):
                os.remove(output_file)


if __name__ == '__main__':
    unittest.main()
