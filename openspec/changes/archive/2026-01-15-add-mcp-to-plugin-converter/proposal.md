# Change: Add MCP to Claude Code Plugin Converter

## Why
MCP (Model Context Protocol) servers from directories like fastmcp.me and smithery.ai require manual configuration to use with Claude Code. Users need an automated tool to convert these MCP server listings into the Claude Code plugin format.

## What Changes
- Add `mcp2plugin` CLI tool with commands: `convert`, `info`, `list`, `init`
- Implement source parsers for fastmcp.me and smithery.ai
- Add optional Gemini LLM enhancement for better parsing and description generation
- Create plugin marketplace management for organizing converted plugins
- Generate Claude Code compatible plugin.json configurations

## Impact
- Affected specs: mcp-plugin-converter (new)
- Affected code: Initial implementation creating new project structure
- New dependencies: click, httpx, pydantic, rich, google-generativeai
