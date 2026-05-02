SUPPORTED_ECOSYSTEMS = {"golang", "npm", "maven", "nuget", "pypi"}


def parse_package_input(raw_package: str) -> dict[str, str | None]:
    """Normalize user package input into Boost validate_package arguments.

    Expected input formats:
    1) <package>@<version>
       Example: httpx@0.28.1

    2) <package> <version>
       Example: httpx 0.28.1

    3) <ecosystem> <package> <version>
       Example: pypi httpx 0.28.1
       Example: golang github.com/golang-jwt/jwt/v5 v5.0.0

    4) <ecosystem>:<package>@<version>
       Example: golang:github.com/golang-jwt/jwt/v5@v5.0.0

    Notes:
    - If ecosystem is not explicitly provided, default is pypi.
    - If a slash exists in a default-pypi package path, treat it as a golang module.
    - For golang modules, namespace and package are split for the MCP schema.
    """
    value = raw_package.strip()
    ecosystem = "pypi"
    namespace = None
    package_name = ""

    # Version can be provided as "name@version" or as a separate token.
    if "@" in value:
        package_part, version = value.rsplit("@", 1)
        if not package_part or not version:
            raise ValueError("Invalid package format. Expected <package>@<version>")

        package_part = package_part.strip()
        version = version.strip()
    else:
        parts = value.split()
        if len(parts) == 2:
            package_part, version = parts
        elif len(parts) == 3 and parts[0] in SUPPORTED_ECOSYSTEMS:
            ecosystem, package_part, version = parts
        else:
            raise ValueError(
                "Invalid package format. Use either '<package>@<version>', "
                "'<package> <version>', or '<ecosystem> <package> <version>'."
            )

    package_name = package_part

    # Optional compact prefix style: "ecosystem:package@version".
    if ":" in package_part and package_part.split(":", 1)[0] in SUPPORTED_ECOSYSTEMS:
        ecosystem, remainder = package_part.split(":", 1)
        package_name = remainder
    else:
        remainder = package_part

    # Heuristic: slash paths are usually Go modules when ecosystem is not explicit.
    if ecosystem == "pypi" and "/" in remainder:
        ecosystem = "golang"

    if ecosystem == "golang":
        if remainder.startswith("github.com/"):
            # github.com/org/name(/subpath...) => namespace=github.com/org, package=name(/subpath...)
            parts = remainder.split("/")
            if len(parts) >= 3:
                namespace = "/".join(parts[:2])
                package_name = "/".join(parts[2:])
            else:
                package_name = remainder
        elif "/" in remainder:
            # org/name(/subpath...) => assume a GitHub module path.
            parts = remainder.split("/")
            if len(parts) >= 2:
                namespace = f"github.com/{parts[0]}"
                package_name = "/".join(parts[1:])

    return {
        "ecosystem": ecosystem,
        "namespace": namespace,
        "package": package_name,
        "version": version,
    }
