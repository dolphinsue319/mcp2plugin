# MCP Plugin Converter

## ADDED Requirements

### Requirement: MCP URL Conversion
The system SHALL convert MCP server URLs from supported directories (fastmcp.me, smithery.ai) to Claude Code plugin format.

#### Scenario: Convert fastmcp.me URL
- **WHEN** user runs `mcp2plugin convert https://fastmcp.me/MCP/Details/{id}/{name}`
- **THEN** the system fetches MCP information from fastmcp.me
- **AND** generates a Claude Code plugin in the output directory
- **AND** registers the plugin in the marketplace

#### Scenario: Convert smithery.ai URL
- **WHEN** user runs `mcp2plugin convert https://smithery.ai/server/{name}`
- **THEN** the system fetches MCP information from smithery.ai
- **AND** generates a Claude Code plugin in the output directory
- **AND** registers the plugin in the marketplace

#### Scenario: Unsupported URL
- **WHEN** user provides an unsupported URL
- **THEN** the system displays an error with supported URL formats

### Requirement: MCP Information Display
The system SHALL display MCP server information without conversion.

#### Scenario: Show MCP info
- **WHEN** user runs `mcp2plugin info <url>`
- **THEN** the system displays MCP name, description, author, connection type, and tools

### Requirement: Plugin Marketplace Management
The system SHALL manage a local plugin marketplace for converted plugins.

#### Scenario: Initialize marketplace
- **WHEN** user runs `mcp2plugin init`
- **THEN** the system creates marketplace.json configuration
- **AND** creates plugins directory structure

#### Scenario: List marketplace plugins
- **WHEN** user runs `mcp2plugin list`
- **THEN** the system displays all plugins in the marketplace with name, description, and source

### Requirement: LLM Enhancement
The system SHALL optionally use Gemini LLM to enhance parsing accuracy and generate better descriptions.

#### Scenario: LLM-enhanced conversion
- **WHEN** GEMINI_API_KEY is configured
- **AND** user runs `mcp2plugin convert <url>` without --no-llm flag
- **THEN** the system uses Gemini to enhance parsed information
- **AND** generates improved plugin descriptions

#### Scenario: Disable LLM enhancement
- **WHEN** user runs `mcp2plugin convert <url> --no-llm`
- **THEN** the system uses basic parsing without LLM enhancement

### Requirement: Plugin Generation
The system SHALL generate Claude Code compatible plugin structures.

#### Scenario: Generate stdio plugin
- **WHEN** MCP server uses stdio connection
- **THEN** the system generates plugin.json with command and args configuration

#### Scenario: Generate HTTP plugin
- **WHEN** MCP server uses HTTP connection
- **THEN** the system generates plugin.json with url configuration
