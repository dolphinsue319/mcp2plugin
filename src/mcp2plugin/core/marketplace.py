"""Marketplace management for converted plugins."""

import json
from pathlib import Path

from ..models import (
    MCPInfo,
    MarketplaceConfig,
    MarketplaceOwner,
    MarketplacePlugin,
)


class Marketplace:
    """Manages the plugin marketplace catalog."""

    def __init__(self, marketplace_path: Path):
        """Initialize the marketplace.

        Args:
            marketplace_path: Root directory of the marketplace
        """
        self.path = marketplace_path
        self.config_dir = marketplace_path / ".claude-plugin"
        self.config_path = self.config_dir / "marketplace.json"

    def initialize(
        self,
        name: str = "mcp2plugin-marketplace",
        owner_name: str = "mcp2plugin",
        description: str = "Converted MCP servers as Claude Code plugins",
    ) -> None:
        """Initialize the marketplace with default configuration.

        Args:
            name: Marketplace name
            owner_name: Owner name
            description: Marketplace description
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        if not self.config_path.exists():
            config = MarketplaceConfig(
                name=name,
                description=description,
                owner=MarketplaceOwner(name=owner_name),
                plugins=[],
            )
            self._save_config(config)

    def add_plugin(self, plugin_path: Path, mcp_info: MCPInfo) -> None:
        """Add a plugin to the marketplace catalog.

        Args:
            plugin_path: Path to the plugin directory
            mcp_info: MCP information for the plugin
        """
        config = self._load_config()

        # Calculate relative path from marketplace root
        try:
            relative_path = plugin_path.relative_to(self.path)
            source = f"./{relative_path}"
        except ValueError:
            source = str(plugin_path)

        # Create plugin entry
        plugin_name = plugin_path.name
        plugin_entry = MarketplacePlugin(
            name=plugin_name,
            source=source,
            description=mcp_info.description or f"MCP server: {mcp_info.name}",
            category="mcp",
            homepage=mcp_info.homepage,
        )

        # Check if plugin already exists, update if so
        existing_idx = None
        for idx, p in enumerate(config.plugins):
            if p.name == plugin_name:
                existing_idx = idx
                break

        if existing_idx is not None:
            config.plugins[existing_idx] = plugin_entry
        else:
            config.plugins.append(plugin_entry)

        self._save_config(config)

    def remove_plugin(self, name: str) -> bool:
        """Remove a plugin from the marketplace.

        Args:
            name: Plugin name to remove

        Returns:
            True if plugin was removed, False if not found
        """
        config = self._load_config()

        original_count = len(config.plugins)
        config.plugins = [p for p in config.plugins if p.name != name]

        if len(config.plugins) < original_count:
            self._save_config(config)
            return True
        return False

    def list_plugins(self) -> list[dict]:
        """List all plugins in the marketplace.

        Returns:
            List of plugin dictionaries
        """
        config = self._load_config()
        return [p.model_dump() for p in config.plugins]

    def get_plugin(self, name: str) -> dict | None:
        """Get plugin details by name.

        Args:
            name: Plugin name

        Returns:
            Plugin dictionary or None if not found
        """
        config = self._load_config()
        for plugin in config.plugins:
            if plugin.name == name:
                return plugin.model_dump()
        return None

    def _load_config(self) -> MarketplaceConfig:
        """Load marketplace configuration from file."""
        if not self.config_path.exists():
            self.initialize()

        with open(self.config_path, encoding="utf-8") as f:
            data = json.load(f)

        return MarketplaceConfig(**data)

    def _save_config(self, config: MarketplaceConfig) -> None:
        """Save marketplace configuration to file."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)
            f.write("\n")
