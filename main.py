import argparse
import asyncio
import json
import os
import sys
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from package_input_parser import parse_package_input

BOOST_URL = 'https://mcp.boostsecurity.io/mcp'
CONNECT_TIMEOUT_SECONDS = 20
SCAN_TIMEOUT_SECONDS = 30

def load_local_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            # Keep non-empty shell vars higher priority than .env values.
            # If a shell var exists but is blank, prefer the .env value.
            existing = os.getenv(key)
            if existing is None or not existing.strip():
                os.environ[key] = value


def format_mcp_content(content: object) -> str:
    """Render MCP response content in a readable format.

    - JSON text payloads are pretty-printed.
    - Non-JSON text payloads are returned as-is.
    - Structured objects are serialized to pretty JSON when possible.
    """
    text = getattr(content, "text", None)
    if isinstance(text, str):
        try:
            parsed = json.loads(text)
            return json.dumps(parsed, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            return text

    if hasattr(content, "model_dump"):
        try:
            return json.dumps(content.model_dump(), indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(content)

    if isinstance(content, (dict, list)):
        try:
            return json.dumps(content, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(content)

    return str(content)

async def run_scan(package: str) -> None:
    """Run a single package validation and print the result."""
    print(f"Starting scan for package: {package}")
    try:
        parsed_package = parse_package_input(package)
    except ValueError as package_error:
        print(f"Invalid package input: {package_error}")
        sys.exit(1)

    boost_token = (
        os.getenv("BOOST_TOKEN", "").strip()
        or os.getenv("boost_token", "").strip()
    )
    headers = {"Authorization": f"Bearer {boost_token}"} if boost_token else None

    if not boost_token:
        print("Warning: BOOST_TOKEN is not set. Authenticated MCP endpoints may timeout or reject requests.")

    try:
        async with asyncio.timeout(CONNECT_TIMEOUT_SECONDS):
            async with httpx.AsyncClient(
                headers=headers,
                timeout=httpx.Timeout(10, read=SCAN_TIMEOUT_SECONDS),
            ) as http_client:
                async with streamable_http_client(url=BOOST_URL, http_client=http_client) as (read, write, _):
                    async with ClientSession(read, write) as session:
                        await session.initialize()

                        result = await asyncio.wait_for(
                            session.call_tool(
                                "validate_package",
                                arguments=parsed_package
                            ),
                            timeout=SCAN_TIMEOUT_SECONDS,
                        )

                        print("\n" + "="*40)
                        print(f"Scan result for package {package}:")
                        print("="*40 + "\n")

                        if not getattr(result, "content", None):
                            print("No content returned by validate_package.")
                            return

                        for content in result.content:
                            print(format_mcp_content(content))

    except TimeoutError:
        print(
            f"Timed out while connecting to {BOOST_URL} or waiting for scan results. "
            "Check network access and BOOST authentication/token setup."
        )
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during scanning package {package}: {e}")
        sys.exit(1)


def cli() -> None:
    """CLI entry point: boost-scan [PACKAGE]

    When PACKAGE is omitted the tool falls back to an interactive prompt.
    """
    load_local_env_file()

    parser = argparse.ArgumentParser(
        prog="boost-scan",
        description="Validate a package version against the Boost Security MCP server.",
    )
    parser.add_argument(
        "package",
        nargs="?",
        help=(
            "Package to scan. Accepted formats: "
            "'httpx 0.28.1', 'httpx@0.28.1', "
            "'pypi httpx 0.28.1', 'golang-jwt/jwt/v5@v5.0.0'"
        ),
    )
    args = parser.parse_args()

    package = args.package
    if not package:
        # Fall back to interactive prompt when no argument is supplied.
        try:
            package = input("Enter the package name to scan: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nScan interrupted by user. Exiting.")
            sys.exit(0)

    if not package:
        parser.print_help()
        sys.exit(1)

    try:
        asyncio.run(run_scan(package))
    except KeyboardInterrupt:
        print("\nScan interrupted by user. Exiting.")


async def run_interactive_scan():
    """Legacy async entry point kept for programmatic use."""
    load_local_env_file()

    package = input("Enter the package name to scan: ")

    if not package:
        print("No Package entered. Exiting.")
        return
    
    print(f"Starting interactive scan for package: {package}")
    await run_scan(package)


if __name__ == "__main__":
    cli()