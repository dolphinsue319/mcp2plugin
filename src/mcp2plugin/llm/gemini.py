"""Gemini API integration for intelligent MCP parsing."""

import json
import os
import re

from google import genai
from google.genai import types

from ..models import MCPInfo, MCPTool


class GeminiParser:
    """Uses Gemini API to intelligently parse and enhance MCP data."""

    def __init__(self, api_key: str | None = None):
        """Initialize the Gemini parser.

        Args:
            api_key: Gemini API key. If not provided, uses GEMINI_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Gemini API key required. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )

        self.client = genai.Client(api_key=self.api_key)
        self.model = "gemini-2.0-flash"

    async def parse_mcp_page(self, html_content: str, url: str) -> dict:
        """Extract structured MCP data from HTML content using Gemini.

        Args:
            html_content: Raw HTML content of the MCP page
            url: Source URL for context

        Returns:
            Dictionary with extracted MCP information
        """
        prompt = f"""Analyze this MCP (Model Context Protocol) server page and extract structured information.

URL: {url}

HTML Content (truncated):
{html_content[:15000]}

Extract the following information in JSON format:
{{
    "name": "MCP server name",
    "description": "Brief description of what the MCP does",
    "author": "Author name or username",
    "tools": [
        {{"name": "tool_name", "description": "what the tool does"}}
    ],
    "install_command": "npx, uvx, or other command",
    "install_args": ["list", "of", "arguments"],
    "connection_type": "stdio or http",
    "http_url": "URL if connection_type is http, null otherwise",
    "env_vars": ["LIST_OF_REQUIRED", "ENVIRONMENT_VARIABLES"],
    "homepage": "GitHub or project homepage URL"
}}

Important:
- For install_command, identify the package manager (npx, uvx, bunx, npm exec)
- For install_args, include all necessary arguments (e.g., ["-y", "package-name"])
- Only include actual tools/functions the MCP provides, not generic features
- connection_type should be "stdio" for local servers, "http" for remote/hosted
- Only include env_vars that are actually required for the MCP to function

Return ONLY valid JSON, no markdown formatting."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=2000,
            ),
        )

        # Parse the JSON response
        response_text = response.text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            response_text = re.sub(r"```json?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from the response
            json_match = re.search(r"\{[\s\S]*\}", response_text)
            if json_match:
                return json.loads(json_match.group(0))
            raise ValueError(f"Failed to parse Gemini response as JSON: {response_text[:200]}")

    async def enhance_mcp_info(self, mcp_info: MCPInfo, html_content: str) -> MCPInfo:
        """Enhance existing MCP info with additional details from Gemini.

        Args:
            mcp_info: Existing MCPInfo to enhance
            html_content: HTML content for additional context

        Returns:
            Enhanced MCPInfo
        """
        # Only enhance if we're missing important information
        needs_enhancement = (
            not mcp_info.description
            or not mcp_info.tools
            or not mcp_info.install_command
        )

        if not needs_enhancement:
            return mcp_info

        prompt = f"""Given this MCP server information, help fill in missing details.

Current information:
- Name: {mcp_info.name}
- Description: {mcp_info.description or 'MISSING'}
- Tools: {[t.name for t in mcp_info.tools] if mcp_info.tools else 'MISSING'}
- Install command: {mcp_info.install_command or 'MISSING'}
- Install args: {mcp_info.install_args or 'MISSING'}

Page content (for context):
{html_content[:10000]}

Provide missing information in JSON format:
{{
    "description": "description if missing",
    "tools": [{{"name": "tool_name", "description": "description"}}],
    "install_command": "command if missing",
    "install_args": ["args", "if", "missing"]
}}

Only include fields that need to be filled in. Return valid JSON only."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    max_output_tokens=1500,
                ),
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = re.sub(r"```json?\n?", "", response_text)
                response_text = re.sub(r"\n?```$", "", response_text)

            enhancements = json.loads(response_text)

            # Apply enhancements
            if not mcp_info.description and enhancements.get("description"):
                mcp_info.description = enhancements["description"]

            if not mcp_info.tools and enhancements.get("tools"):
                mcp_info.tools = [
                    MCPTool(name=t["name"], description=t.get("description", ""))
                    for t in enhancements["tools"]
                ]

            if not mcp_info.install_command and enhancements.get("install_command"):
                mcp_info.install_command = enhancements["install_command"]

            if not mcp_info.install_args and enhancements.get("install_args"):
                mcp_info.install_args = enhancements["install_args"]

        except Exception:
            # If enhancement fails, return original
            pass

        return mcp_info

    async def generate_plugin_description(
        self,
        mcp_name: str,
        tools: list[MCPTool],
        raw_description: str,
    ) -> str:
        """Generate a polished Claude Code plugin description.

        Args:
            mcp_name: Name of the MCP server
            tools: List of tools provided by the MCP
            raw_description: Original description text

        Returns:
            Polished description string
        """
        tool_list = "\n".join(
            f"- {t.name}: {t.description}" for t in tools[:10]
        ) if tools else "No tools listed"

        prompt = f"""Create a concise, professional description for a Claude Code plugin.

MCP Name: {mcp_name}
Original Description: {raw_description or 'None provided'}
Available Tools:
{tool_list}

Write a 1-2 sentence description that:
1. Explains what the plugin does
2. Highlights key capabilities
3. Is written for developers

Return ONLY the description text, no quotes or formatting."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=200,
            ),
        )

        return response.text.strip()

    async def determine_connection_type(
        self,
        page_content: str,
        install_hints: list[str],
    ) -> tuple[str, dict]:
        """Determine if MCP uses stdio or http connection.

        Args:
            page_content: HTML/text content of the page
            install_hints: List of installation command hints

        Returns:
            Tuple of (connection_type, config_dict)
        """
        prompt = f"""Analyze this MCP server page to determine the connection type.

Page content (excerpt):
{page_content[:8000]}

Installation hints: {install_hints}

Determine:
1. Is this a LOCAL server (runs on user's machine via stdio) or REMOTE server (hosted, accessed via HTTP)?
2. What is the installation/connection configuration?

For LOCAL/stdio servers, respond with:
{{"type": "stdio", "command": "npx", "args": ["-y", "package-name"]}}

For REMOTE/http servers, respond with:
{{"type": "http", "url": "https://server-url/path"}}

Return ONLY valid JSON."""

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=300,
            ),
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            response_text = re.sub(r"```json?\n?", "", response_text)
            response_text = re.sub(r"\n?```$", "", response_text)

        try:
            config = json.loads(response_text)
            conn_type = config.pop("type", "stdio")
            return conn_type, config
        except json.JSONDecodeError:
            # Default to stdio
            return "stdio", {"command": "npx", "args": ["-y", "unknown-mcp"]}
