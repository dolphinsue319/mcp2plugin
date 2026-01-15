"""Main conversion orchestrator."""

import os
from pathlib import Path

import httpx

from ..llm.gemini import GeminiParser
from ..models import MCPInfo
from ..sources.base import MCPSource
from ..sources.fastmcp import FastMCPSource
from ..sources.smithery import SmitherySource
from ..utils.url_parser import SourceType, detect_source, normalize_url
from .marketplace import Marketplace
from .plugin_generator import PluginGenerator


class ConversionError(Exception):
    """Error during MCP to plugin conversion."""

    pass


class Converter:
    """Orchestrates the conversion of MCP servers to Claude Code plugins."""

    def __init__(
        self,
        output_dir: Path,
        marketplace_path: Path | None = None,
        gemini_api_key: str | None = None,
        use_llm: bool = True,
    ):
        """Initialize the converter.

        Args:
            output_dir: Directory for generated plugins
            marketplace_path: Path to marketplace root (defaults to output_dir parent)
            gemini_api_key: Gemini API key (optional, uses env var)
            use_llm: Whether to use LLM for enhanced parsing
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.marketplace_path = marketplace_path or output_dir.parent
        self.marketplace = Marketplace(self.marketplace_path)
        self.marketplace.initialize()

        self.generator = PluginGenerator(output_dir)

        self.use_llm = use_llm
        self.gemini_parser = None
        if use_llm:
            api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
            if api_key:
                self.gemini_parser = GeminiParser(api_key)

        # Initialize source parsers
        self.sources: list[MCPSource] = [
            FastMCPSource(),
            SmitherySource(),
        ]

    async def convert(self, url: str) -> Path:
        """Convert an MCP URL to a Claude Code plugin.

        Args:
            url: URL of the MCP server page

        Returns:
            Path to the generated plugin directory

        Raises:
            ConversionError: If conversion fails
        """
        # Normalize URL
        url = normalize_url(url)

        # Detect source type
        source_type = detect_source(url)
        if source_type == SourceType.UNKNOWN:
            raise ConversionError(
                f"Unknown URL format: {url}\n"
                "Supported sources:\n"
                "  - fastmcp.me: https://fastmcp.me/MCP/Details/{id}/{name}\n"
                "  - smithery.ai: https://smithery.ai/server/{name}"
            )

        # Find appropriate source parser
        source = self._get_source(url)
        if not source:
            raise ConversionError(f"No parser available for URL: {url}")

        # Fetch MCP information
        try:
            mcp_info = await source.fetch(url)
        except httpx.HTTPError as e:
            raise ConversionError(f"Failed to fetch URL: {e}") from e
        except Exception as e:
            raise ConversionError(f"Failed to parse MCP page: {e}") from e

        # Enhance with LLM if available
        if self.gemini_parser and self.use_llm:
            try:
                html_content = await self._fetch_html(url)
                mcp_info = await self.gemini_parser.enhance_mcp_info(mcp_info, html_content)

                # Generate better description if needed
                if not mcp_info.description or len(mcp_info.description) < 20:
                    mcp_info.description = await self.gemini_parser.generate_plugin_description(
                        mcp_info.name,
                        mcp_info.tools,
                        mcp_info.description,
                    )
            except Exception:
                # Continue without LLM enhancement
                pass

        # Generate plugin
        plugin_path = self.generator.generate(mcp_info)

        # Add to marketplace
        self.marketplace.add_plugin(plugin_path, mcp_info)

        return plugin_path

    async def get_info(self, url: str) -> MCPInfo:
        """Get MCP information without generating a plugin.

        Args:
            url: URL of the MCP server page

        Returns:
            MCPInfo containing the parsed data
        """
        url = normalize_url(url)

        source = self._get_source(url)
        if not source:
            raise ConversionError(f"No parser available for URL: {url}")

        return await source.fetch(url)

    def _get_source(self, url: str) -> MCPSource | None:
        """Get the appropriate source parser for a URL."""
        for source in self.sources:
            if source.can_handle(url):
                return source
        return None

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML content from URL."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
