# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

mcp2plugin converts MCP (Model Context Protocol) servers into Claude Code plugin format. It supports two MCP sources: fastmcp.me and smithery.ai. The tool can optionally use Gemini LLM to enhance plugin descriptions.

## Commands

```bash
# Run CLI commands (no install needed with uv)
uv run mcp2plugin init                    # Initialize marketplace
uv run mcp2plugin convert <url>           # Convert MCP to plugin
uv run mcp2plugin convert <url> --no-llm  # Convert without LLM enhancement
uv run mcp2plugin info <url>              # Show MCP info without converting
uv run mcp2plugin list                    # List plugins in marketplace

# Workers deployment (Cloudflare)
cd workers && npm install
npm run dev      # Local development
npm run deploy   # Deploy to Cloudflare
```

## Architecture

### Python CLI (`src/mcp2plugin/`)

```
cli.py              # Click CLI entry point
core/
  converter.py      # Main orchestrator - coordinates sources, LLM, generator
  marketplace.py    # Manages .claude-plugin/marketplace.json
  plugin_generator.py  # Generates plugin directories and plugin.json
sources/
  base.py           # MCPSource abstract base class
  fastmcp.py        # Parser for fastmcp.me URLs
  smithery.py       # Parser for smithery.ai URLs
models/
  mcp_info.py       # MCPInfo Pydantic model (parsed MCP data)
  plugin.py         # Plugin Pydantic model (output format)
llm/
  gemini.py         # Optional Gemini LLM for description enhancement
utils/
  url_parser.py     # URL detection and normalization
```

**Flow**: URL → Source parser (`fetch`) → MCPInfo → Optional LLM enhancement → PluginGenerator → marketplace.json update

### Workers API (`workers/`)

Hono-based Cloudflare Worker serving marketplace data as HTTP API:
- `GET /` → marketplace.json
- `GET /plugins` → plugin name list
- `GET /plugins/:name` → specific plugin.json

Plugin data is embedded directly in `workers/src/index.ts`. Update this file when adding new plugins.

**Live URL**: https://mcp2plugin-marketplace.howardsue319.workers.dev/

## Key Patterns

- **Adding new MCP sources**: Implement `MCPSource` interface in `sources/`, add instance to `Converter.sources` list
- **Plugin output structure**: `plugins/<name>/.claude-plugin/plugin.json`
- **Marketplace config**: `.claude-plugin/marketplace.json` at repository root

## Environment

- `GEMINI_API_KEY` - Optional, for LLM-enhanced descriptions (copy `.env.example` to `.env`)
