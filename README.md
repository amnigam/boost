# Boost Package Validator (MCP)

Simple interactive Python script to validate third-party package versions using the Boost Security MCP server.

## What It Does

- Prompts for a package and version
- Normalizes user input into Boost `validate_package` tool arguments
- Connects to the Boost MCP endpoint via the Streamable HTTP transport
- Calls Boost MCP and prints the validation result
- Supports `.env` token loading

## Requirements

- Python `>=3.14`
- Dependencies:
	- `mcp>=1.27.0`
	- `httpx>=0.28.1`

## Install

Using `uv`:

```powershell
uv sync
```

Or with `pip`:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

## Configure Token

Create a `.env` file in the project root:

```env
BOOST_TOKEN=your_token_here
```

Notes:

- `BOOST_TOKEN` is preferred.
- `boost_token` is also accepted.
- If both shell environment and `.env` are set, shell environment wins.
- `.env` is listed in `.gitignore` and will not be committed.

## Run

```powershell
python main.py
```

Then enter one of the supported formats when prompted.

## Supported Input Formats

1. `<package>@<version>`
2. `<package> <version>`
3. `<ecosystem> <package> <version>`
4. `<ecosystem>:<package>@<version>`

Supported ecosystems: `golang`, `npm`, `maven`, `nuget`, `pypi`

If no ecosystem is specified, `pypi` is assumed. Package paths containing a `/` are automatically treated as Go modules.

## Examples

### PyPI

```text
httpx 0.28.1
```

```text
httpx@0.28.1
```

```text
pypi httpx 0.28.1
```

### Go Modules

```text
golang-jwt/jwt/v5@v5.0.0
```

```text
golang github.com/golang-jwt/jwt/v5 v5.0.0
```

## Sample Output

### Safe package

```json
{
  "purl": "pkg:pypi/httpx@0.28.1",
  "ecosystem": "pypi",
  "namespace": null,
  "package": "httpx",
  "version": "0.28.1",
  "evaluation": "safe",
  "reason": "No vulnerabilities found",
  "recommendation": null
}
```

### Update available

```json
{
  "purl": "pkg:golang/github.com/golang-jwt/jwt/v5@v5.0.0",
  "ecosystem": "golang",
  "namespace": "github.com/golang-jwt",
  "package": "jwt/v5",
  "version": "v5.0.0",
  "evaluation": "update_available",
  "reason": "The packages contains vulnerabilities but fixes are available in newer versions.",
  "recommendation": "Use version 5.2.2 or above of the package."
}
```

## Transport

The script uses the MCP **Streamable HTTP** transport (`streamable_http_client` from the `mcp` library). This transport sends requests as HTTP `POST` calls and receives responses as either a single JSON body or a server-sent event (SSE) stream, depending on the operation. An explicit `httpx.AsyncClient` is used so headers (auth token) and timeouts are configured precisely.

The older SSE transport (`sse_client`) is not compatible with this endpoint and will time out.

## Timeouts

| Constant | Default | Purpose |
|---|---|---|
| `CONNECT_TIMEOUT_SECONDS` | 20s | Total wall-clock limit for the whole request |
| `SCAN_TIMEOUT_SECONDS` | 30s | Read timeout passed to `httpx`; also guards `call_tool` |

## Troubleshooting

- **Timeout during scan:**
	- Verify internet/network access to `https://mcp.boostsecurity.io/mcp`
	- Confirm `BOOST_TOKEN` is set and valid
- **Validation argument errors:**
	- Include an exact version (e.g. `0.28.1`, not `latest`)
	- Check the input format matches a supported pattern
- **Empty input:**
	- Script exits with `No Package entered. Exiting.`

## Running Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The test suite in `tests/test_package_input_parser.py` covers all supported input formats and invalid cases for the parser.

## File Overview

| File | Purpose |
|---|---|
| `main.py` | Interactive scanner entry point |
| `package_input_parser.py` | Input normalisation logic and format parsing |
| `tests/test_package_input_parser.py` | Unit tests for the parser |
| `pyproject.toml` | Project metadata and dependencies |
| `.env` | Local secrets (not committed) |
