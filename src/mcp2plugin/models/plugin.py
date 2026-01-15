"""Claude Code Plugin configuration data models."""

from typing import Optional
from pydantic import BaseModel, Field


class MCPServerConfig(BaseModel):
    """MCP server configuration for plugin.json."""

    type: Optional[str] = Field(default=None, description="Connection type: http or omit for stdio")
    command: Optional[str] = Field(default=None, description="Command for stdio type")
    args: Optional[list[str]] = Field(default=None, description="Arguments for stdio type")
    url: Optional[str] = Field(default=None, description="URL for http type")
    headers: Optional[dict[str, str]] = Field(default=None, description="Headers for http type")
    env: Optional[dict[str, str]] = Field(default=None, description="Environment variables")

    def model_dump(self, **kwargs):
        """Override to exclude None values."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class PluginAuthor(BaseModel):
    """Plugin author information."""

    name: str
    email: Optional[str] = None


class PluginConfig(BaseModel):
    """Claude Code plugin.json configuration."""

    name: str = Field(..., description="Plugin name in kebab-case")
    description: str = Field(default="", description="Plugin description")
    version: str = Field(default="1.0.0", description="Plugin version")
    author: Optional[PluginAuthor] = Field(default=None, description="Author information")
    homepage: Optional[str] = Field(default=None, description="Plugin homepage URL")
    repository: Optional[str] = Field(default=None, description="Source repository URL")
    mcpServers: dict[str, MCPServerConfig] = Field(
        default_factory=dict, description="MCP server configurations"
    )

    def model_dump(self, **kwargs):
        """Override to exclude None values and serialize nested models."""
        kwargs.setdefault("exclude_none", True)
        data = super().model_dump(**kwargs)
        if "mcpServers" in data:
            data["mcpServers"] = {
                k: {kk: vv for kk, vv in v.items() if vv is not None}
                for k, v in data["mcpServers"].items()
            }
        return data


class MarketplacePlugin(BaseModel):
    """Plugin entry in marketplace.json."""

    name: str = Field(..., description="Plugin name")
    source: str = Field(..., description="Plugin source path")
    description: str = Field(default="", description="Plugin description")
    category: Optional[str] = Field(default=None, description="Plugin category")
    homepage: Optional[str] = Field(default=None, description="Plugin homepage")


class MarketplaceOwner(BaseModel):
    """Marketplace owner information."""

    name: str
    email: Optional[str] = None


class MarketplaceConfig(BaseModel):
    """Claude Code marketplace.json configuration."""

    name: str = Field(..., description="Marketplace name")
    description: str = Field(default="", description="Marketplace description")
    owner: MarketplaceOwner = Field(..., description="Marketplace owner")
    plugins: list[MarketplacePlugin] = Field(default_factory=list, description="Plugin entries")

    def model_dump(self, **kwargs):
        """Override to exclude None values."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
