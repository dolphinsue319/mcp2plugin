# mcp2plugin

將 MCP (Model Context Protocol) 伺服器轉換為 Claude Code Plugin 格式的命令列工具。

## 功能特色

- 支援 [fastmcp.me](https://fastmcp.me) 和 [smithery.ai](https://smithery.ai) 兩大 MCP 來源
- 自動產生 Claude Code 相容的 plugin.json 設定
- 內建 marketplace 管理系統
- 可選的 Gemini LLM 增強解析（更準確的描述和工具識別）

## 安裝

### 需求

- Python 3.12+
- uv 或 pip

```bash
git clone https://github.com/dolphinsue319/mcp2plugin.git
cd mcp2plugin
```

使用 `uv run` 可直接執行，無需額外安裝步驟。

## 環境設定

### Gemini API Key（可選）

如需使用 LLM 增強解析功能，請設定 Gemini API Key：

1. 前往 [Google AI Studio](https://aistudio.google.com/apikey) 取得 API Key
2. 建立 `.env` 檔案：

```bash
cp .env.example .env
```

3. 編輯 `.env` 填入 API Key：

```
GEMINI_API_KEY=your-api-key-here
```

> 若不設定 API Key，工具仍可正常運作，但解析結果可能較不精確。

## 使用方式

### 初始化 Marketplace

在使用前，先初始化 marketplace：

```bash
uv run mcp2plugin init
```

這會建立以下結構：

```
./
├── .claude-plugin/
│   └── marketplace.json
└── plugins/
```

可自訂 marketplace 名稱和擁有者：

```bash
uv run mcp2plugin init --name "my-plugins" --owner "username"
```

### 轉換 MCP 為 Plugin

從 fastmcp.me 轉換：

```bash
uv run mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix
```

從 smithery.ai 轉換：

```bash
uv run mcp2plugin convert https://smithery.ai/server/slack
```

#### 選項

- `-o, --output PATH`：指定輸出目錄（預設：`./plugins`）
- `--no-llm`：停用 LLM 增強（較快但可能較不精確）

```bash
# 指定輸出目錄
uv run mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix -o /path/to/output

# 停用 LLM 增強
uv run mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix --no-llm
```

### 查看 MCP 資訊

在轉換前，可先查看 MCP 的詳細資訊：

```bash
uv run mcp2plugin info https://fastmcp.me/MCP/Details/217/repomix
```

輸出包含：

- MCP 名稱和描述
- 作者資訊
- 連線類型（stdio/http）
- 安裝指令
- 可用的工具列表
- 所需環境變數

### 列出已轉換的 Plugins

```bash
uv run mcp2plugin list
```

指定 marketplace 目錄：

```bash
uv run mcp2plugin list -m /path/to/marketplace
```

## 在 Claude Code 中使用

### 步驟 1：新增 Marketplace

在 Claude Code 中執行：

```
/plugin marketplace add dolphinsue319/mcp2plugin
```

或使用遠端 API：

```
/plugin marketplace add https://marketplace.incandgold.cc
```

或使用本地路徑：

```
/plugin marketplace add /path/to/mcp2plugin
```

### 步驟 2：安裝 Plugin

```
/plugin install <plugin-name>@mcp2plugin-marketplace
```

例如：

```
/plugin install repomix@mcp2plugin-marketplace
```

## 完整使用範例

```bash
# 1. 進入專案目錄
cd ~/my-plugins

# 2. 初始化 marketplace
uv run mcp2plugin init --name "my-mcp-plugins"

# 3. 轉換想要的 MCP
uv run mcp2plugin convert https://fastmcp.me/MCP/Details/217/repomix
uv run mcp2plugin convert https://smithery.ai/server/slack

# 4. 查看已轉換的 plugins
uv run mcp2plugin list

# 5. 在 Claude Code 中使用
# /plugin marketplace add dolphinsue319/mcp2plugin
# /plugin install repomix@mcp2plugin-marketplace
```

## 支援的 URL 格式

### fastmcp.me

```
https://fastmcp.me/MCP/Details/{id}/{name}
```

範例：
- `https://fastmcp.me/MCP/Details/217/repomix`
- `https://fastmcp.me/MCP/Details/123/my-server`

### smithery.ai

```
https://smithery.ai/server/{name}
```

範例：
- `https://smithery.ai/server/slack`
- `https://smithery.ai/server/google-drive`

## 產生的檔案結構

```
marketplace-root/
├── .claude-plugin/
│   └── marketplace.json      # Marketplace 設定
└── plugins/
    └── plugin-name/
        └── .claude-plugin/
            └── plugin.json   # Plugin 設定
```

### plugin.json 範例

```json
{
  "name": "repomix",
  "description": "將程式碼庫打包成 AI 友好的格式",
  "version": "1.0.0",
  "author": {
    "name": "yamadashy"
  },
  "homepage": "https://github.com/yamadashy/repomix",
  "mcpServers": {
    "repomix": {
      "command": "npx",
      "args": ["-y", "repomix"]
    }
  }
}
```

## Marketplace API

Marketplace 也提供 HTTP API 供遠端存取：

| 端點 | 說明 |
|------|------|
| `GET /` | 返回 marketplace.json |
| `GET /plugins` | 返回所有 plugin 名稱列表 |
| `GET /plugins/:name` | 返回特定 plugin 的 plugin.json |

API URL: https://marketplace.incandgold.cc

## 授權

MIT License
