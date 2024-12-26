# status_report/data_models.py

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
from typing import Dict


class StatusData:
    """
    Represents the data returned by each server's /status endpoint.
    We assume the JSON has the following fields:
        "Application", "Version", "Uptime", "Request_Count", "Error_Count", "Success_Count"
    """
    __slots__ = ["application", "version", "uptime",
                 "request_count", "error_count", "success_count"]

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
