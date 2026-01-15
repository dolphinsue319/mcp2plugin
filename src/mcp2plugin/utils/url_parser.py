"""URL parsing and detection utilities."""

import re
from enum import Enum


class SourceType(Enum):
    """Supported MCP source types."""

    FASTMCP = "fastmcp"
    SMITHERY = "smithery"
    UNKNOWN = "unknown"


# URL patterns for different sources
FASTMCP_PATTERN = re.compile(r"https?://(?:www\.)?fastmcp\.me/MCP/Details/(\d+)/([^/\s]+)")
SMITHERY_PATTERN = re.compile(r"https?://(?:server\.)?smithery\.ai/(?:server/)?([^/\s]+)")


def detect_source(url: str) -> SourceType:
    """Detect the source type from a URL.

    Args:
        url: The URL to analyze

    Returns:
        SourceType enum indicating the detected source
    """
    if FASTMCP_PATTERN.match(url):
        return SourceType.FASTMCP
    if SMITHERY_PATTERN.match(url):
        return SourceType.SMITHERY
    return SourceType.UNKNOWN


def normalize_url(url: str) -> str:
    """Normalize a URL to its canonical form.

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL string
    """
    # Handle smithery.ai redirects
    if "server.smithery.ai" in url:
        match = re.search(r"server\.smithery\.ai/([^/\s]+)", url)
        if match:
            server_name = match.group(1)
            return f"https://smithery.ai/server/{server_name}"

    return url


def extract_mcp_name(url: str) -> str | None:
    """Extract the MCP name from a URL.

    Args:
        url: The URL to parse

    Returns:
        MCP name or None if not found
    """
    # Try fastmcp pattern
    match = FASTMCP_PATTERN.match(url)
    if match:
        return match.group(2)

    # Try smithery pattern
    match = SMITHERY_PATTERN.match(url)
    if match:
        return match.group(1)

    return None
