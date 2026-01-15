"""Plugin configuration generator."""

import json
from pathlib import Path

from ..models import MCPInfo, MCPServerConfig, PluginConfig, PluginAuthor


class PluginGenerator:
    """Generates Claude Code plugin configuration files."""

    def __init__(self, output_dir: Path):
        """Initialize the generator.

        Args:
            output_dir: Base directory for generated plugins
        """
        self.output_dir = output_dir

    def generate(self, mcp_info: MCPInfo) -> Path:
        """Generate a Claude Code plugin from MCP information.

        Args:
            mcp_info: MCP server information

        Returns:
            Path to the generated plugin directory
        """
        # Create plugin directory
        plugin_name = self._sanitize_name(mcp_info.name)
        plugin_dir = self.output_dir / plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)

        # Create .claude-plugin directory
        claude_plugin_dir = plugin_dir / ".claude-plugin"
        claude_plugin_dir.mkdir(exist_ok=True)

        # Generate plugin.json
        plugin_config = self._create_plugin_config(mcp_info, plugin_name)
        plugin_json_path = claude_plugin_dir / "plugin.json"
        self._write_json(plugin_json_path, plugin_config.model_dump())

        return plugin_dir

    def _create_plugin_config(self, mcp_info: MCPInfo, plugin_name: str) -> PluginConfig:
        """Create plugin configuration from MCP info.

        Args:
            mcp_info: MCP server information
            plugin_name: Sanitized plugin name

        Returns:
            PluginConfig object
        """
        # Create MCP server configuration
        server_name = mcp_info.get_server_name()

        if mcp_info.connection_type == "http" and mcp_info.http_url:
            server_config = MCPServerConfig(
                type="http",
                url=mcp_info.http_url,
            )
        else:
            # stdio type
            server_config = MCPServerConfig(
                command=mcp_info.install_command or "npx",
                args=mcp_info.install_args or ["-y", f"mcp-server-{plugin_name}"],
            )

            # Add environment variables if needed
            if mcp_info.env_vars:
                server_config.env = {var: f"${{{var}}}" for var in mcp_info.env_vars}

        # Create author info
        author = None
        if mcp_info.author:
            author = PluginAuthor(name=mcp_info.author)

        return PluginConfig(
            name=plugin_name,
            description=mcp_info.description or f"MCP server: {mcp_info.name}",
            version="1.0.0",
            author=author,
            homepage=mcp_info.homepage,
            repository=mcp_info.homepage if mcp_info.homepage and "github" in mcp_info.homepage else None,
            mcpServers={server_name: server_config},
        )

    def _sanitize_name(self, name: str) -> str:
        """Convert name to valid plugin name (kebab-case).

        Args:
            name: Original name

        Returns:
            Sanitized kebab-case name
        """
        import re

        # Remove special characters and convert to lowercase
        sanitized = re.sub(r"[^\w\s-]", "", name.lower())
        # Replace spaces and underscores with hyphens
        sanitized = re.sub(r"[\s_]+", "-", sanitized)
        # Remove consecutive hyphens
        sanitized = re.sub(r"-+", "-", sanitized)
        # Remove leading/trailing hyphens
        sanitized = sanitized.strip("-")

        return sanitized or "unknown-plugin"

    def _write_json(self, path: Path, data: dict) -> None:
        """Write JSON data to file with pretty formatting.

        Args:
            path: Output file path
            data: JSON data to write
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
