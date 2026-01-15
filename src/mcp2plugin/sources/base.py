"""Base class for MCP source parsers."""

from abc import ABC, abstractmethod

from ..models import MCPInfo


class MCPSource(ABC):
    """Abstract base class for MCP source parsers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if this source can handle the given URL.

        Args:
            url: The URL to check

        Returns:
            True if this source can handle the URL
        """
        pass

    @abstractmethod
    async def fetch(self, url: str) -> MCPInfo:
        """Fetch and parse MCP information from the URL.

        Args:
            url: The URL to fetch

        Returns:
            MCPInfo containing the parsed data

        Raises:
            ValueError: If the URL cannot be parsed
            httpx.HTTPError: If the fetch fails
        """
        pass
