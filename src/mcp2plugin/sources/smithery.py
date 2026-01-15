"""Smithery.ai source parser."""

import re

import httpx
from bs4 import BeautifulSoup

from ..models import MCPInfo, MCPTool
from ..utils.url_parser import SMITHERY_PATTERN
from .base import MCPSource


class SmitherySource(MCPSource):
    """Parser for smithery.ai MCP server pages."""

    def can_handle(self, url: str) -> bool:
        """Check if this source can handle the given URL."""
        return bool(SMITHERY_PATTERN.match(url))

    async def fetch(self, url: str) -> MCPInfo:
        """Fetch and parse MCP information from smithery.ai.

        Args:
            url: The smithery.ai URL

        Returns:
            MCPInfo containing the parsed data
        """
        # Normalize URL (handle server.smithery.ai redirect)
        if "server.smithery.ai" in url:
            match = re.search(r"server\.smithery\.ai/([^/\s]+)", url)
            if match:
                server_name = match.group(1)
                url = f"https://smithery.ai/server/{server_name}"

        async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        # Extract server name from URL
        match = SMITHERY_PATTERN.match(url)
        if not match:
            raise ValueError(f"Invalid smithery.ai URL: {url}")

        server_name = match.group(1)

        # Extract title/name from page
        title_elem = soup.find("h1")
        display_name = title_elem.get_text(strip=True) if title_elem else server_name

        # Extract description
        description = ""
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc and meta_desc.get("content"):
            description = meta_desc["content"]
        else:
            # Try to find description in page content
            desc_elem = soup.find("p")
            if desc_elem:
                description = desc_elem.get_text(strip=True)[:500]

        # Extract author
        author = ""
        author_elem = soup.find(string=re.compile(r"by\s+@?\w+|author", re.I))
        if author_elem:
            author_match = re.search(r"@?(\w+)", str(author_elem))
            if author_match:
                author = author_match.group(1)

        # Extract tools
        tools = self._extract_tools(soup)

        # Determine connection type and install command
        connection_type, install_command, install_args, http_url = (
            self._determine_connection(soup, server_name)
        )

        # Extract environment variables
        env_vars = self._extract_env_vars(soup)

        # Extract homepage
        homepage = None
        github_link = soup.find("a", href=re.compile(r"github\.com"))
        if github_link:
            homepage = github_link.get("href")

        return MCPInfo(
            name=display_name or server_name,
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

        # Look for tool/function sections
        tool_sections = soup.find_all(
            ["div", "section", "ul", "table"],
            class_=re.compile(r"tool|function|method|endpoint|api", re.I),
        )

        for section in tool_sections:
            items = section.find_all(["li", "tr", "div"])
            for item in items:
                text = item.get_text(strip=True)
                if text and len(text) > 5:
                    parts = re.split(r"[-–:]", text, maxsplit=1)
                    if len(parts) == 2:
                        tools.append(MCPTool(name=parts[0].strip(), description=parts[1].strip()))
                    else:
                        tools.append(MCPTool(name=text[:50], description=text))

        # Look for code blocks that might contain tool definitions
        code_blocks = soup.find_all("code")
        for code in code_blocks:
            text = code.get_text(strip=True)
            # Look for function-like names
            func_matches = re.findall(r"(\w+)\s*\(", text)
            for func_name in func_matches:
                if func_name not in ["if", "for", "while", "function", "def"]:
                    if not any(t.name == func_name for t in tools):
                        tools.append(MCPTool(name=func_name, description=""))

        return tools[:20]

    def _determine_connection(
        self, soup: BeautifulSoup, server_name: str
    ) -> tuple[str, str, list[str], str | None]:
        """Determine connection type and installation details.

        Returns:
            Tuple of (connection_type, install_command, install_args, http_url)
        """
        page_text = soup.get_text()

        # Check for hosted/remote server indicators
        if re.search(r"hosted|remote|cloud|server\.smithery\.ai", page_text, re.I):
            # This is likely a hosted server
            http_url = f"https://server.smithery.ai/{server_name}"
            return "http", "", [], http_url

        # Check for local installation patterns
        install_patterns = [
            (r"npx\s+@smithery/cli\s+install\s+([^\s]+)", "npx"),
            (r"npx\s+-y\s+([^\s<\"']+)", "npx"),
            (r"npm\s+install\s+([^\s]+)", "npm"),
        ]

        for pattern, cmd in install_patterns:
            match = re.search(pattern, page_text)
            if match:
                package = match.group(1)
                if cmd == "npx" and "@smithery/cli" in pattern:
                    return "stdio", "npx", ["-y", "@smithery/cli", "run", package], None
                elif cmd == "npx":
                    return "stdio", "npx", ["-y", package], None
                elif cmd == "npm":
                    return "stdio", "npx", ["-y", package], None

        # Default to smithery CLI for local servers
        return "stdio", "npx", ["-y", "@smithery/cli", "run", server_name], None

    def _extract_env_vars(self, soup: BeautifulSoup) -> list[str]:
        """Extract required environment variables."""
        env_vars = []
        page_text = soup.get_text()

        # Look for config/env sections
        config_sections = soup.find_all(
            ["div", "section", "pre", "code"],
            class_=re.compile(r"config|env|setting", re.I),
        )

        for section in config_sections:
            text = section.get_text()
            # Extract variable names
            matches = re.findall(r'"([A-Z][A-Z0-9_]+)"', text)
            env_vars.extend(matches)

        # Also search entire page for common patterns
        patterns = [
            r"\$\{([A-Z][A-Z0-9_]+)\}",
            r"([A-Z][A-Z0-9_]+):\s*(?:string|required)",
            r'"([A-Z][A-Z0-9_]+)":\s*\{',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            env_vars.extend(matches)

        # Filter and dedupe
        filtered = []
        for var in set(env_vars):
            if len(var) > 3 and not any(
                x in var.lower() for x in ["type", "string", "number", "boolean"]
            ):
                filtered.append(var)

        return filtered[:10]
