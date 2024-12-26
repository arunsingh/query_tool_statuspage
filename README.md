
# Status Page Report Tool

This tool reads a list of servers from `servers.txt`, then queries each server's
`/status` endpoint. It calculates success rates by `(Application, Version)` and
outputs two types of reports:

1. Human-readable text in the console
2. JSON file for downstream consumption (`report.json` by default)

Name: Status Page Query Tool
Description: This tool reads a list of servers (from a file) and queries each server’s http://<server>/status endpoint. It then aggregates success rates for each (Application, Version) pair and writes two reports:

Human-Readable: Printed to stdout.
Machine-Parseable JSON: Written to report.json (or a file specified by the OUTPUT_FILE environment variable).


##  Installation Requirements

Python 3.8+
aiohttp for asynchronous HTTP. Install via `pip install aiohttp`.
(Optional) `pytest` or `unittest` to run the test suite.

```shell
git clone <this-repo-url>
cd <repo-directory>
pip install -r requirements.txt  # if you create one
```

## Usage
1. Ensure servers.txt is in the same directory (or specify its path).
2. Run: python3 main.py servers.txt
3. Optionally set environment variables:
MAX_CONCURRENCY: Limit the concurrency (default 20).
HTTP_TIMEOUT: Timeout in seconds (default 5).
OUTPUT_FILE: Where to write JSON output (default report.json).

```bash
export MAX_CONCURRENCY=50
export HTTP_TIMEOUT=3
export OUTPUT_FILE="my_report.json"
```

`python3 main.py servers.txt`

## Output
Console: Human-readable success rate summary.
my_report.json (or report.json): JSON array with per (application, version) aggregated data, plus naive HATEOAS links.
Running Tests

### We demonstrate TDD/BDD with unittest in the same file (for simplicity). You can run them:
`python3 -m unittest main.py`

