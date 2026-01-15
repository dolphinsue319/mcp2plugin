"""MCP server information data models."""

from typing import Optional
from pydantic import BaseModel, Field


class MCPTool(BaseModel):
    """Represents a single MCP tool."""

    name: str
    description: str = ""


class MCPInfo(BaseModel):
    """Represents MCP server information extracted from sources."""

    name: str = Field(..., description="MCP server name")
    description: str = Field(default="", description="MCP server description")
    author: str = Field(default="", description="Author name")
    tools: list[MCPTool] = Field(default_factory=list, description="List of tools")
    install_command: str = Field(default="", description="Installation command (e.g., npx)")
    install_args: list[str] = Field(default_factory=list, description="Installation arguments")
    connection_type: str = Field(default="stdio", description="Connection type: stdio or http")
    http_url: Optional[str] = Field(default=None, description="HTTP URL for http type connections")
    env_vars: list[str] = Field(default_factory=list, description="Required environment variables")
    homepage: Optional[str] = Field(default=None, description="Project homepage URL")
    source_url: str = Field(..., description="Source URL where MCP info was fetched")

    def get_server_name(self) -> str:
        """Get a sanitized server name for use in configuration."""
        return self.name.lower().replace(" ", "-").replace("_", "-")
