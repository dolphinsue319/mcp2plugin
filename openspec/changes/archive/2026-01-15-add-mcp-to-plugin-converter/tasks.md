# Tasks: MCP to Claude Code Plugin Converter

## 1. Project Setup
- [x] 1.1 Initialize Python project with uv
- [x] 1.2 Configure pyproject.toml with dependencies
- [x] 1.3 Set up project structure (src/mcp2plugin)

## 2. Data Models
- [x] 2.1 Create MCPInfo model for parsed MCP data
- [x] 2.2 Create MCPTool model for tool definitions
- [x] 2.3 Create PluginConfig model for plugin.json
- [x] 2.4 Create MarketplaceConfig model for marketplace.json

## 3. Source Parsers
- [x] 3.1 Create base MCPSource abstract class
- [x] 3.2 Implement FastMCPSource for fastmcp.me
- [x] 3.3 Implement SmitherySource for smithery.ai
- [x] 3.4 Create URL parser utility

## 4. Core Conversion
- [x] 4.1 Implement Converter orchestrator class
- [x] 4.2 Implement PluginGenerator for creating plugin files
- [x] 4.3 Implement Marketplace management

## 5. LLM Enhancement
- [x] 5.1 Implement GeminiParser for LLM-enhanced parsing
- [x] 5.2 Add MCP info enhancement
- [x] 5.3 Add plugin description generation

## 6. CLI Interface
- [x] 6.1 Implement `convert` command
- [x] 6.2 Implement `info` command
- [x] 6.3 Implement `list` command
- [x] 6.4 Implement `init` command
