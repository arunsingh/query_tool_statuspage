"""
Machine-code style Python3 application that queries multiple servers' /status endpoints,
aggregates success rates by Application & Version, and produces two output formats:
  1) Human-readable text to stdout
  2) Machine-parseable JSON file

See the included tests (bottom of file or separate test directory) for TDD/BDD
examples.

It will test ServerStatusClient, you might mock the HTTP call. Below is a trivial skeleton:

Author: Arun Singh
Date: 2024-12-21
"""
# tests/test_http_client.py

import unittest
from unittest.mock import AsyncMock, patch
import aiohttp
from status_report.http_client import ServerStatusClient
from status_report.data_models import StatusData


class TestHttpClient(unittest.IsolatedAsyncioTestCase):
    async def test_fetch_status_success(self):
        # Mock the JSON response
        mock_resp = AsyncMock()
        mock_resp.json.return_value = {
            "Application": "TestApp",
            "Version": "1.0",
            "Uptime": "123.45",
            "Request_Count": "10",
            "Error_Count": "2",
            "Success_Count": "8"
        }
        mock_resp.raise_for_status.return_value = None

        async with patch.object(aiohttp.ClientSession, 'get', return_value=mock_resp):
            async with aiohttp.ClientSession() as session:
                client = ServerStatusClient(session, 5)
                data = await client.fetch_status("fake-server")
                self.assertIsInstance(data, StatusData)
                self.assertEqual(data.application, "TestApp")


if __name__ == '__main__':
    unittest.main()
