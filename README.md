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

### As a CLI command (after install)

```powershell
boost-scan httpx@0.28.1
```

Or with the interactive prompt (no argument):

```powershell
boost-scan
```

### Directly with Python

```powershell
python main.py httpx@0.28.1
```

Or interactively:

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
- **Empty input or missing argument:**
	- `boost-scan` (with no argument and no interactive input) prints help and exits with code 1

## Running Tests

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

The test suite covers:
- `tests/test_package_input_parser.py` — all supported input formats and invalid cases for the parser
- `tests/test_main.py` — unit tests for the main module

## File Overview

| File | Purpose |
|---|---|
| `main.py` | CLI (`boost-scan`) and interactive scanner entry point |
| `package_input_parser.py` | Input normalisation logic and format parsing |
| `tests/test_package_input_parser.py` | Unit tests for the parser |
| `tests/test_main.py` | Unit tests for the main module |
| `pyproject.toml` | Project metadata, dependencies, and `boost-scan` script entry point |
| `.env` | Local secrets (not committed) |
