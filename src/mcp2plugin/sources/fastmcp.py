"""FastMCP.me source parser."""

import re

import httpx
from bs4 import BeautifulSoup

from ..models import MCPInfo, MCPTool
from ..utils.url_parser import FASTMCP_PATTERN
from .base import MCPSource


class FastMCPSource(MCPSource):
    """Parser for fastmcp.me MCP server pages."""

    def can_handle(self, url: str) -> bool:
        """Check if this source can handle the given URL."""
        return bool(FASTMCP_PATTERN.match(url))

    async def fetch(self, url: str) -> MCPInfo:
        """Fetch and parse MCP information from fastmcp.me.

        Args:
            url: The fastmcp.me URL

        Returns:
            MCPInfo containing the parsed data
        """
        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract MCP name from URL
        match = FASTMCP_PATTERN.match(url)
        if not match:
            raise ValueError(f"Invalid fastmcp.me URL: {url}")

        mcp_name = match.group(2)

        # Extract title/name from page
        title_elem = soup.find("h1")
        display_name = title_elem.get_text(strip=True) if title_elem else mcp_name

        # Extract description from meta tag or content
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]
        else:
            # Try to find description in page content
            desc_elem = soup.find("p", class_=re.compile(r"description|summary", re.I))
            if desc_elem:
                description = desc_elem.get_text(strip=True)

        # Extract author
        author = ""
        author_elem = soup.find(string=re.compile(r"@\w+"))
        if author_elem:
            author_match = re.search(r"@(\w+)", str(author_elem))
            if author_match:
                author = author_match.group(1)

        # Extract tools from the page
        tools = self._extract_tools(soup)

        # Extract installation command
        install_command, install_args = self._extract_install_command(soup, mcp_name)

        # Determine connection type
        connection_type = "stdio"
        http_url = None

        # Check for HTTP URL indicators
        http_patterns = soup.find_all(string=re.compile(r"https?://.*mcp|endpoint|api", re.I))
        if http_patterns:
            for pattern in http_patterns:
                http_match = re.search(r"(https?://[^\s\"'<>]+)", str(pattern))
                if http_match and "mcp" in http_match.group(1).lower():
                    connection_type = "http"
                    http_url = http_match.group(1)
                    break

        # Extract environment variables
        env_vars = self._extract_env_vars(soup)

        # Extract homepage
        homepage = None
        github_link = soup.find("a", href=re.compile(r"github\.com"))
        if github_link:
            homepage = github_link.get("href")

        return MCPInfo(
            name=display_name or mcp_name,
            description=description,
            author=author,
            tools=tools,
            install_command=install_command,
            install_args=install_args,
            connection_type=connection_type,
            http_url=http_url,
            env_vars=env_vars,
            homepage=homepage,
            source_url=url,
        )

    def _extract_tools(self, soup: BeautifulSoup) -> list[MCPTool]:
        """Extract tool information from the page."""
        tools = []

        # Look for tool sections or lists
        tool_sections = soup.find_all(
            ["div", "section", "ul"],
            class_=re.compile(r"tool|feature|capability", re.I),
        )

        for section in tool_sections:
            items = section.find_all(["li", "div", "p"])
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    # Try to split name and description
                    parts = re.split(r"[-–:]", text, maxsplit=1)
                    if len(parts) == 2:
                        tools.append(MCPTool(name=parts[0].strip(), description=parts[1].strip()))
                    else:
                        tools.append(MCPTool(name=text[:50], description=text))

        # Also look for bold/strong elements that might be tool names
        if not tools:
            strong_elements = soup.find_all(["strong", "b"])
            for elem in strong_elements:
                name = elem.get_text(strip=True)
                if name and "_" in name or name.startswith("get") or name.startswith("create"):
                    next_text = elem.next_sibling
                    desc = str(next_text).strip() if next_text else ""
                    tools.append(MCPTool(name=name, description=desc[:200]))

        return tools[:20]  # Limit to 20 tools

    def _extract_install_command(
        self, soup: BeautifulSoup, mcp_name: str
    ) -> tuple[str, list[str]]:
        """Extract installation command and arguments."""
        # Common patterns for MCP installation
        patterns = [
            (r"npx\s+-y\s+([^\s<\"']+)", "npx"),
            (r"uvx\s+([^\s<\"']+)", "uvx"),
            (r"bunx\s+([^\s<\"']+)", "bunx"),
            (r"npm\s+exec\s+([^\s<\"']+)", "npm"),
        ]

        page_text = soup.get_text()

        for pattern, cmd in patterns:
            match = re.search(pattern, page_text)
            if match:
                package = match.group(1)
                if cmd == "npx":
                    return "npx", ["-y", package]
                elif cmd == "uvx":
                    return "uvx", [package]
                elif cmd == "bunx":
                    return "bunx", [package]
                elif cmd == "npm":
                    return "npm", ["exec", package]

        # Fallback: try to construct a reasonable install command
        # Check for package name patterns
        package_patterns = [
            rf"@[^/\s]+/{mcp_name}",  # @scope/package
            rf"mcp-server-{mcp_name}",  # mcp-server-name
            rf"{mcp_name}-mcp",  # name-mcp
        ]

        for pattern in package_patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                return "npx", ["-y", match.group(0)]

        # Default fallback
        return "npx", ["-y", f"mcp-server-{mcp_name.lower()}"]

    def _extract_env_vars(self, soup: BeautifulSoup) -> list[str]:
        """Extract required environment variables."""
        env_vars = []
        page_text = soup.get_text()

        # Common patterns for environment variables
        env_patterns = [
            r"\$\{([A-Z][A-Z0-9_]+)\}",  # ${VAR_NAME}
            r"\$([A-Z][A-Z0-9_]+)",  # $VAR_NAME
            r"([A-Z][A-Z0-9_]+)=",  # VAR_NAME=
            r"env[:\s]+([A-Z][A-Z0-9_]+)",  # env: VAR_NAME
        ]

        for pattern in env_patterns:
            matches = re.findall(pattern, page_text)
            for match in matches:
                if match not in env_vars and len(match) > 3:
                    # Filter out common non-env strings
                    if not any(
                        x in match.lower()
                        for x in ["url", "uri", "http", "json", "xml"]
                    ):
                        env_vars.append(match)

        return list(set(env_vars))[:10]  # Dedupe and limit
