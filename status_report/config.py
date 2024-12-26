# status_report/config.py

import os


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
