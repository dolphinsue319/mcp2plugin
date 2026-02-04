import { Hono } from 'hono'
import { cors } from 'hono/cors'

// Embedded marketplace data
const marketplace = {
  name: "mcp2plugin-marketplace",
  description: "Converted MCP servers as Claude Code plugins",
  owner: {
    name: "kedia"
  },
  plugins: [
    {
      name: "repomix",
      source: "./plugins/repomix",
      description: "Optimize your codebase for AI with Repomix—transform, compress, and secure repos for easier analysis with modern AI tools.",
      category: "mcp",
      homepage: "https://github.com/yamadashy/repomix"
    },
    {
      name: "sequential-thinking",
      source: "./plugins/sequential-thinking",
      description: "Break down complex problems with Sequential Thinking, a structured tool and step by step math solver for dynamic, reflective solutions.",
      category: "mcp",
      homepage: "https://github.com/modelcontextprotocol/servers/tree/HEAD/src/sequentialthinking"
    },
    {
      name: "gemini-cli",
      source: "./plugins/gemini-cli",
      description: "Integrate with Gemini CLI for large-scale file analysis, secure code execution, and advanced context control using Google's powerful tools.",
      category: "mcp",
      homepage: "https://github.com/jamubc/gemini-mcp-tool"
    },
    {
      name: "docs-crawler",
      source: "./plugins/docs-crawler",
      description: "Query documentation using semantic search via Gemini File Search",
      category: "mcp",
      homepage: "https://github.com/dolphinsue319/docs_crawler"
    }
  ]
}

// Embedded plugins data
const plugins: Record<string, object> = {
  "repomix": {
    name: "repomix",
    description: "Optimize your codebase for AI with Repomix—transform, compress, and secure repos for easier analysis with modern AI tools.",
    version: "1.0.0",
    author: {
      name: "context"
    },
    homepage: "https://github.com/yamadashy/repomix",
    repository: "https://github.com/yamadashy/repomix",
    mcpServers: {
      repomix: {
        command: "npx",
        args: ["-y", "repomix", "--mcp"]
      }
    }
  },
  "sequential-thinking": {
    name: "sequential-thinking",
    description: "Break down complex problems with Sequential Thinking, a structured tool and step by step math solver for dynamic, reflective solutions.",
    version: "1.0.0",
    author: {
      name: "context"
    },
    homepage: "https://github.com/modelcontextprotocol/servers/tree/HEAD/src/sequentialthinking",
    repository: "https://github.com/modelcontextprotocol/servers/tree/HEAD/src/sequentialthinking",
    mcpServers: {
      "sequential-thinking": {
        command: "npx",
        args: ["-y", "mcp-server-sequential-thinking"]
      }
    }
  },
  "gemini-cli": {
    name: "gemini-cli",
    description: "Integrate with Gemini CLI for large-scale file analysis, secure code execution, and advanced context control using Google's powerful tools.",
    version: "1.0.0",
    author: {
      name: "context"
    },
    homepage: "https://github.com/jamubc/gemini-mcp-tool",
    repository: "https://github.com/jamubc/gemini-mcp-tool",
    mcpServers: {
      "gemini-cli": {
        command: "npx",
        args: ["-y", "mcp-server-gemini-cli"]
      }
    }
  },
  "docs-crawler": {
    name: "docs-crawler",
    description: "Query documentation using semantic search via Gemini File Search. Provides list_stores and query_docs tools.",
    version: "1.0.0",
    author: {
      name: "kedia"
    },
    homepage: "https://github.com/dolphinsue319/docs_crawler",
    repository: "https://github.com/dolphinsue319/docs_crawler",
    mcpServers: {
      "docs-crawler": {
        type: "http",
        url: "https://docs-mcp.incandgold.cc/mcp"
      }
    }
  }
}

const app = new Hono()

// Enable CORS for all routes
app.use('*', cors())

// GET / - Return marketplace.json
app.get('/', (c) => c.json(marketplace))

// GET /plugins - Return list of all plugin names
app.get('/plugins', (c) => c.json(Object.keys(plugins)))

// GET /plugins/:name - Return specific plugin.json
app.get('/plugins/:name', (c) => {
  const name = c.req.param('name')
  const plugin = plugins[name]

  if (!plugin) {
    return c.json({ error: 'Plugin not found' }, 404)
  }

  return c.json(plugin)
})

export default app
