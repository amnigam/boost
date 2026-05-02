import asyncio 
import os
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

            # Keep shell-exported vars higher priority than .env values.
            os.environ.setdefault(key, value)

async def run_interactive_scan():
    load_local_env_file()

    package = input("Enter the package name to scan: ")

    if not package:
        print("No Package entered. Exiting.")
        return
    
    print(f"Starting interactive scan for package: {package}")
    try:
        parsed_package = parse_package_input(package)
    except ValueError as package_error:
        print(f"Invalid package input: {package_error}")
        return

    boost_token = (
        os.getenv("BOOST_TOKEN", "").strip()
        or os.getenv("boost_token", "").strip()
    )
    headers = {"Authorization": f"Bearer {boost_token}"} if boost_token else None

    if not boost_token:
        print("Warning: BOOST_TOKEN is not set. Authenticated MCP endpoints may timeout or reject requests.")

    try:
        # Prevent waiting forever if endpoint is unreachable or auth is missing.
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
                            text = getattr(content, "text", None)
                            if text:
                                print(text)
                            else:
                                print(content)

    except TimeoutError:
        print(
            f"Timed out while connecting to {BOOST_URL} or waiting for scan results. "
            "Check network access and BOOST authentication/token setup."
        )
    except Exception as e:
        print(f"An error occurred during scanning package {package}: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(run_interactive_scan())
    except KeyboardInterrupt:
        print("\nScan interrupted by user. Exiting.")