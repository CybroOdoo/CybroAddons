# Odoo MCP Server — Configuration Guide

---

## Table of Contents

1. [Connecting MCP Platforms](#section-1-connecting-mcp-platforms)
   - 1.1 [What You Need Before Starting](#11-what-you-need-before-starting)
   - 1.2 [Claude Desktop](#12-claude-desktop)
   - 1.3 [Claude Code CLI](#13-claude-code-cli)
   - 1.4 [claude.ai (Cloud)](#14-claudeai-cloud)
   - 1.5 [OpenAI Codex CLI](#15-openai-codex-cli)
2. [Connecting AI Providers](#section-2-connecting-ai-providers)
   - 2.1 [OpenAI](#21-openai)
   - 2.2 [Anthropic (Claude)](#22-anthropic-claude)
   - 2.3 [Google Gemini](#23-google-gemini)
   - 2.4 [Ollama (Local)](#24-ollama-local)
   - 2.5 [Custom OpenAI-Compatible Provider](#25-custom-openai-compatible-provider)
   - 2.6 [Adding Models](#26-adding-models)
3. [Connecting Chat Bots](#section-3-connecting-chat-bots)
   - 3.1 [Required Settings Before Any Bot](#31-required-settings-before-any-bot)
   - 3.2 [Telegram Bot](#32-telegram-bot)
   - 3.3 [WhatsApp Bot](#33-whatsapp-bot)
   - 3.4 [Discord Bot](#34-discord-bot)
   - 3.5 [Web Chat Widget](#35-web-chat-widget)

---

---

# Section 1: Connecting MCP Platforms

The MCP (Model Context Protocol) gateway exposes your Odoo database as a live data source that external AI tools — Claude Desktop, Claude Code CLI, claude.ai, and OpenAI Codex — can read and write through. Once connected, those tools can search records, create entries, ask questions about your data, and more, all without any custom integration code.

---

## 1.1 What You Need Before Starting

Before connecting any platform you need two things from Odoo:

### A — The MCP Server URL

Your MCP endpoint is always:

```
https://your-odoo-domain.com/mcp_gateway
```

Replace `your-odoo-domain.com` with the actual domain or IP where Odoo is running. The URL must be reachable from the machine running the AI client.

### B — An MCP API Key

Each user who connects a platform needs their own API key. To generate one:

1. Go to **MCP Gateway → Dashboard**.
2. In the **MCP Server Status** card, click the **New MCP Key** button.
3. In the wizard that opens:
   - Choose the **Platform** you want to connect (Claude Desktop, Claude Cloud, Claude Code CLI, or OpenAI Codex CLI).
   - Optionally change the **Key Description** — this is just a label to help you identify the key later.
   - Click **Generate Key**.
4. The wizard shows:
   - **Generated Key** — copy this immediately. It is shown only once and cannot be retrieved again.
   - **MCP Server URL** — pre-filled with your Odoo URL.
   - **Platform Configuration** — the exact snippet you paste into the client.
   - **Setup Instructions** — step-by-step guide for the selected platform.

> If you lose the key, you must generate a new one. Old keys remain active until manually revoked from Settings → Technical → API Keys.

---

## 1.2 Claude Desktop

### What it does

Claude Desktop is Anthropic's native desktop app for macOS, Windows, and Linux. Once configured with the MCP gateway, Claude can see and call all active Odoo tools directly from your chat — searching partners, reading sales orders, creating records, and so on.

### Prerequisites

- Claude Desktop installed and signed in.
- Node.js and `npx` installed on your machine. Verify: `npx --version`

### Configuration Structure

The connection is defined in a JSON config file. The structure is:

```json
{
  "mcpServers": {
    "odoo-ai-hub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "<MCP_SERVER_URL>",
        "--header",
        "Authorization: Bearer <YOUR_MCP_KEY>"
      ],
      "env": {
        "MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

| Placeholder | Replace with |
|---|---|
| `<MCP_SERVER_URL>` | Your Odoo MCP URL, e.g. `https://odoo.mycompany.com/mcp_gateway` |
| `<YOUR_MCP_KEY>` | The key you generated in Section 1.1 |

### Step-by-Step Setup

**Step 1.** Generate an MCP key (Section 1.1) and select **Claude Desktop** as the platform. The wizard renders the full config block with your URL and key already filled in. Copy it.

**Step 2.** Open the Claude Desktop configuration file. The file location depends on your OS:

| OS | Config file path |
|---|---|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

If the file does not exist yet, create it. If it already exists, open it in any text editor.

**Step 3.** Paste the config block. If the file already has an `"mcpServers"` object, merge the `"odoo-ai-hub"` key into the existing object — do not replace the whole file.

**Example — new file:**

```json
{
  "mcpServers": {
    "odoo-ai-hub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://odoo.mycompany.com/mcp_gateway",
        "--header",
        "Authorization: Bearer 1a2b3c4d5e6f7g8h9i0j"
      ],
      "env": {
        "MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

**Example — file already has other servers:**

```json
{
  "mcpServers": {
    "some-other-server": { "..." : "..." },
    "odoo-ai-hub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://odoo.mycompany.com/mcp_gateway",
        "--header",
        "Authorization: Bearer 1a2b3c4d5e6f7g8h9i0j"
      ],
      "env": {
        "MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

**Step 4.** Save the file and **restart Claude Desktop**.

### Verifying the Connection

After restarting Claude Desktop:

1. Look for a **hammer / tools icon** at the bottom of the chat input area. Click it — you should see a list of Odoo tools (`search_records`, `create_record`, `ask_ai`, etc.).
2. Start a conversation and ask: *"Use the search_records tool to find the first 3 contacts in Odoo."* Claude should return real data from your database.
3. If the tools do not appear:
   - Open a terminal and run: `npx --version` — if this fails, install Node.js from nodejs.org.
   - Validate your JSON file with a linter (jsonlint.com) — a missing comma or bracket will silently break the config.
   - Run the underlying command manually to see raw errors:
     ```bash
     npx -y mcp-remote https://odoo.mycompany.com/mcp_gateway \
       --header "Authorization: Bearer YOUR_KEY"
     ```

---

## 1.3 Claude Code CLI

### What it does

Claude Code is Anthropic's command-line coding assistant. Adding the MCP gateway lets it read your Odoo data while helping you build features, write queries, or debug — without switching context to another tool.

### Prerequisites

- Claude Code CLI installed: `claude --version`
- Node.js and `npx` installed: `npx --version`

### Configuration Structure

The connection is registered with a single shell command. The structure of the JSON payload is:

```json
{
  "type": "stdio",
  "command": "npx",
  "args": [
    "-y",
    "mcp-remote",
    "<MCP_SERVER_URL>",
    "--header",
    "Authorization: Bearer <YOUR_MCP_KEY>"
  ],
  "env": {
    "MCP_TRANSPORT": "streamable-http"
  }
}
```

### Step-by-Step Setup

**Step 1.** Generate an MCP key (Section 1.1) and select **Claude Code CLI**. The wizard renders a ready-to-run shell command with your URL and key already filled in. Copy it.

**Step 2.** Open a terminal and paste the full command. It looks like this:

```bash
claude mcp add-json odoo-ai-hub '{
  "type": "stdio",
  "command": "npx",
  "args": [
    "-y",
    "mcp-remote",
    "https://odoo.mycompany.com/mcp_gateway",
    "--header",
    "Authorization: Bearer 1a2b3c4d5e6f7g8h9i0j"
  ],
  "env": {
    "MCP_TRANSPORT": "streamable-http"
  }
}'
```

Run the command. No file editing is required — `claude mcp add-json` handles registration automatically.

**Step 3.** Verify the server is registered:

```bash
claude mcp list
```

You should see `odoo-ai-hub` in the output.

**Step 4.** Restart Claude Code for the tools to activate.

### Verifying the Connection

In a Claude Code session, run:

```
/mcp
```

The output lists all connected MCP servers and their status. `odoo-ai-hub` should show as **connected** with the list of available tools.

To do a live test, ask:

```
Use the Odoo search_records tool to find all customers.
```

Claude Code should return real records from your database. If it cannot connect:

```bash
# Test the underlying connection directly
npx -y mcp-remote https://odoo.mycompany.com/mcp_gateway \
  --header "Authorization: Bearer YOUR_KEY"
```

Any authentication or network error will be visible in the terminal output.

---

## 1.4 claude.ai (Cloud)

### What it does

The claude.ai web interface supports remote MCP servers through the Integrations settings. Once added, every conversation in claude.ai can access your Odoo tools — useful for users who work in the browser rather than the desktop app.

### Prerequisites

- A claude.ai account with MCP integration access (Pro or Team plan).
- Your Odoo server must be reachable from the internet over HTTPS.

### Configuration Structure

For claude.ai the connection is a single URL with the API key embedded as a query parameter:

```
https://<your-odoo-domain>/mcp_gateway?api_key=<YOUR_MCP_KEY>
```

Alternatively, if the integration supports custom headers:

```
URL:    https://<your-odoo-domain>/mcp_gateway
Header: Authorization: Bearer <YOUR_MCP_KEY>
```

### Step-by-Step Setup

**Step 1.** Generate an MCP key (Section 1.1) and select **Claude Cloud (claude.ai)**. The wizard shows the full URL with the key embedded, e.g.:

```
https://odoo.mycompany.com/mcp_gateway?api_key=1a2b3c4d5e6f7g8h9i0j
```

Copy the URL.

**Step 2.** In claude.ai, go to **Settings → Integrations → Add custom integration**.

**Step 3.** Paste the full URL into the **MCP Server URL** field. The API key is already in the URL — leave the Authorization header field blank.

**Step 4.** Click **Save**.

**Step 5.** Start a **new conversation**. The Odoo tools will be available in that session.

### Verifying the Connection

In a new claude.ai conversation, type:

```
What Odoo tools do you have access to?
```

Claude should list the available tools (`search_records`, `create_record`, `ask_ai`, etc.). To do a live test:

```
Use search_records to find the top 5 sales orders in Odoo.
```

If the tools are not visible, confirm that:
- Your Odoo server is publicly reachable: `curl https://odoo.mycompany.com/mcp_gateway/health`
- The API key in the URL is valid and belongs to an active user.

---

## 1.5 OpenAI Codex CLI

### What it does

OpenAI Codex CLI is a terminal coding assistant. Adding the MCP gateway lets it pull live Odoo data into its context — useful when building Odoo integrations or querying ERP data from the command line.

### Prerequisites

- Codex CLI installed.
- Node.js and `npx` installed.

### Configuration Structure

The connection is added to `~/.codex/config.json` under an `"mcpServers"` key:

```json
{
  "mcpServers": {
    "odoo-ai-hub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "<MCP_SERVER_URL>",
        "--header",
        "Authorization: Bearer <YOUR_MCP_KEY>"
      ],
      "env": {
        "MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

### Step-by-Step Setup

**Step 1.** Generate an MCP key (Section 1.1) and select **OpenAI Codex CLI**. Copy the generated config block.

**Step 2.** Open `~/.codex/config.json` (create it if it does not exist).

**Step 3.** Add the `"mcpServers"` block. Full example:

```json
{
  "mcpServers": {
    "odoo-ai-hub": {
      "type": "stdio",
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://odoo.mycompany.com/mcp_gateway",
        "--header",
        "Authorization: Bearer 1a2b3c4d5e6f7g8h9i0j"
      ],
      "env": {
        "MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

**Step 4.** Start Codex. The Odoo tools are listed automatically at startup.

### Verifying the Connection

Codex prints the list of connected MCP servers and tools when it starts. Look for `odoo-ai-hub` and the tool names in the startup output.

To do a live test, ask Codex:

```
Search for all partners with customer_rank > 0 using the Odoo search_records tool.
```

---

### MCP Gateway Health Check (All Platforms)

Regardless of which platform you are connecting, you can always verify the gateway itself is running with a simple HTTP call — no API key required:

```bash
curl https://odoo.mycompany.com/mcp_gateway/health
```

**Success response (HTTP 200):**

```json
{"status": "healthy", "server": "Odoo MCP Gateway"}
```

To verify that your API key is valid, send an authenticated `initialize` call:

```bash
curl -X POST https://odoo.mycompany.com/mcp_gateway \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_MCP_KEY" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {"protocolVersion": "2024-11-05"},
    "id": 1
  }'
```

**Success response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}, "resources": {}},
    "serverInfo": {"name": "Odoo MCP Gateway", "version": "1.0.0"}
  },
  "id": 1
}
```

| Response | What it means |
|---|---|
| `{"status": "healthy"}` | Gateway is up and running |
| `"serverInfo"` in result | Key is valid — authentication succeeded |
| `"error": {"code": -32001}` | Key is missing or invalid |
| HTTP 405 | You used GET instead of POST on the main endpoint |
| Connection refused | Odoo is not running or the URL is wrong |

---

---

# Section 2: Connecting AI Providers

AI providers supply the intelligence behind the MCP tools and the chat bots. The gateway supports OpenAI, Anthropic, Google Gemini, Ollama (local), and any OpenAI-compatible endpoint. You can configure multiple providers and the system picks the highest-priority one automatically, with fallback to the next provider if the primary fails.

---

## 2.1 OpenAI

### What it does

Connects the gateway to OpenAI's API for chat completion (GPT-4o, GPT-3.5, etc.) and text embeddings.

### Step 1 — Get Your API Key

1. Go to [platform.openai.com](https://platform.openai.com) and sign in (or create an account).
2. Click your profile icon → **API Keys → Create new secret key**.
3. Give the key a name, click **Create**, and copy the key immediately — it is shown only once.

### Step 2 — Create the Provider in Odoo

Go to **MCP Gateway → Configuration → Providers → New** and fill in:

| Field | Value |
|---|---|
| Name | Any label, e.g. `OpenAI` |
| Service | `OpenAI` |
| API Key | Paste the key copied from platform.openai.com |
| Base URL | Leave blank — defaults to `https://api.openai.com/v1` |
| Priority | `10` (lower number = higher priority over other providers) |

Click **Save**, then click **Fetch Models** to auto-import all available models.

### Configuration Example

```
Name:     OpenAI
Service:  OpenAI
API Key:  sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Base URL: (blank)
Priority: 10
Active:   ✓
```

### Verifying the Connection

1. After clicking **Fetch Models**, a list of models (gpt-4o, gpt-4o-mini, etc.) appears in the **Models** tab of the provider record. If the list is empty or an error appears, the API key is wrong or has no credits.
2. Go to **MCP Gateway → Tools**, find the `ask_ai` tool, and click **Test Tool**. Enter a simple prompt like `"Say hello"`. A response from OpenAI confirms the provider is working.

---

## 2.2 Anthropic (Claude)

### What it does

Connects the gateway to Anthropic's Claude models (Opus, Sonnet, Haiku) for chat completion. Claude models support up to 200k token context windows — ideal for analyzing large Odoo datasets.

### Step 1 — Get Your API Key

1. Go to [console.anthropic.com](https://console.anthropic.com) and sign in.
2. In the left sidebar click **API Keys → Create Key**.
3. Give it a name and copy the key immediately.

### Step 2 — Create the Provider in Odoo

Go to **MCP Gateway → Configuration → Providers → New** and fill in:

| Field | Value |
|---|---|
| Name | Any label, e.g. `Anthropic` |
| Service | `Anthropic` |
| API Key | Paste the key from console.anthropic.com |
| Base URL | Leave blank — defaults to `https://api.anthropic.com/v1` |
| Priority | e.g. `20` |

Click **Save**. **Do not click Fetch Models** — Anthropic does not expose a model list API. Add models manually (see Section 2.6).

### Configuration Example

```
Name:     Anthropic
Service:  Anthropic
API Key:  sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxx
Base URL: (blank)
Priority: 20
Active:   ✓
```

### Recommended Model IDs (add manually)

| Model ID | Best for |
|---|---|
| `claude-opus-4-7` | Complex multi-step reasoning |
| `claude-sonnet-4-6` | Balanced speed and intelligence (recommended default) |
| `claude-haiku-4-5-20251001` | Fast, high-volume, simpler tasks |

### Verifying the Connection

1. Add at least one model record (Section 2.6) and mark it as **Default for Use**.
2. Test the `ask_ai` tool with a simple prompt. A valid response from Claude confirms the key is working.

---

## 2.3 Google Gemini

### What it does

Connects the gateway to Google's Gemini models for chat and multimodal tasks. Gemini 2.5 Flash supports a 1 million token context window.

### Step 1 — Get Your API Key

1. Go to [aistudio.google.com](https://aistudio.google.com) and sign in with a Google account.
2. Click **Get API Key → Create API Key in new project** (or select an existing project).
3. Copy the key shown.

### Step 2 — Create the Provider in Odoo

Go to **MCP Gateway → Configuration → Providers → New** and fill in:

| Field | Value |
|---|---|
| Name | Any label, e.g. `Google Gemini` |
| Service | `Google Gemini` |
| API Key | Paste the key from AI Studio |
| Base URL | Leave blank — defaults to `https://generativelanguage.googleapis.com/v1beta` |
| Priority | e.g. `30` |

Click **Save**, then click **Fetch Models** to auto-import available Gemini models.

### Configuration Example

```
Name:     Google Gemini
Service:  Google Gemini
API Key:  AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Base URL: (blank)
Priority: 30
Active:   ✓
```

### Recommended Model IDs

| Model ID | Best for |
|---|---|
| `gemini-2.5-flash` | Fast, cost-efficient, 1M context |
| `gemini-2.5-pro` | Most capable Gemini model |
| `gemini-2.0-flash` | High-speed multimodal tasks |

### Verifying the Connection

After **Fetch Models**, Gemini models appear in the Models tab. Test with the `ask_ai` tool — a successful response confirms the key is valid.

> Note: Google Gemini authenticates using `?key=YOUR_API_KEY` as a query parameter, not a Bearer token. The gateway handles this automatically — you do not need to change anything.

---

## 2.4 Ollama (Local)

### What it does

Ollama lets you run open-source models (Llama 3, Mistral, Gemma, Phi-4, etc.) entirely on your own hardware — no API key, no internet required, full privacy. The gateway connects to Ollama's local HTTP server.

### Step 1 — Install and Run Ollama

```bash
# Download and install from https://ollama.com
# Start the Ollama service (runs on port 11434 by default)
ollama serve

# Pull a model (run this in a separate terminal)
ollama pull llama3
```

Verify Ollama is running:

```bash
curl http://localhost:11434/api/tags
```

You should see a JSON response listing your downloaded models.

### Step 2 — Create the Provider in Odoo

Go to **MCP Gateway → Configuration → Providers → New** and fill in:

| Field | Value |
|---|---|
| Name | Any label, e.g. `Local Ollama` |
| Service | `Ollama` |
| API Key | Leave blank — Ollama has no auth by default |
| Base URL | `http://localhost:11434` |
| Priority | e.g. `5` (set lower to prefer Ollama over cloud providers) |

> **Docker note:** If Odoo runs inside Docker on Linux, `localhost` inside the container is not your host machine. Use the host's LAN IP (e.g. `http://192.168.1.10:11434`). On Mac/Windows Docker Desktop, use `http://host.docker.internal:11434`.

Click **Save**, then click **Fetch Models**. Odoo reads `/api/tags` from Ollama and imports all downloaded models automatically.

### Configuration Example

```
Name:     Local Ollama
Service:  Ollama
API Key:  (blank)
Base URL: http://localhost:11434
Priority: 5
Active:   ✓
```

### Recommended Models to Pull

```bash
ollama pull llama3        # Meta Llama 3 8B — strong general reasoning
ollama pull mistral       # Mistral 7B — fast and efficient
ollama pull gemma3        # Google Gemma 3 — compact and capable
ollama pull phi4          # Microsoft Phi-4 — excellent reasoning at small size
ollama pull nomic-embed-text  # Embedding model for semantic search
```

### Verifying the Connection

1. After **Fetch Models**, the models you pulled appear in the Models tab.
2. Test with the `ask_ai` tool. If you get a timeout, increase the timeout or check that `ollama serve` is still running.
3. If Fetch Models returns an error like *"Failed to fetch Ollama models"*:
   ```bash
   # Verify Ollama is reachable from Odoo's perspective
   curl http://localhost:11434/api/tags
   # Should return: {"models": [...]}
   ```

---

## 2.5 Custom OpenAI-Compatible Provider

### What it does

Connects the gateway to any server that implements the OpenAI chat completion API — including LM Studio, Groq, Together AI, Azure OpenAI, and vLLM. If the server speaks `/v1/chat/completions`, it works.

### Step 1 — Know Your Endpoint

Find your service's base URL from its documentation:

| Service | Base URL |
|---|---|
| LM Studio | `http://localhost:1234/v1` |
| Groq | `https://api.groq.com/openai/v1` |
| Together AI | `https://api.together.xyz/v1` |
| Azure OpenAI | `https://<resource>.openai.azure.com/openai/deployments/<deployment>` |
| vLLM (self-hosted) | `http://your-server:8000/v1` |

### Step 2 — Create the Provider in Odoo

Go to **MCP Gateway → Configuration → Providers → New** and fill in:

| Field | Value |
|---|---|
| Name | Any label, e.g. `LM Studio` or `Groq` |
| Service | `Custom (OpenAI Compatible)` |
| API Key | Required for Groq, Together AI, Azure — leave blank for local services |
| Base URL | Full base URL from the table above |
| Priority | Your preferred priority number |

Click **Save**. Click **Fetch Models** if your service supports `GET /models` — if not, add models manually (Section 2.6).

### Configuration Example — Groq

```
Name:     Groq
Service:  Custom (OpenAI Compatible)
API Key:  gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
Base URL: https://api.groq.com/openai/v1
Priority: 15
Active:   ✓
```

### Configuration Example — LM Studio (Local)

```
Name:     LM Studio
Service:  Custom (OpenAI Compatible)
API Key:  (blank)
Base URL: http://localhost:1234/v1
Priority: 8
Active:   ✓
```

### Verifying the Connection

1. After **Fetch Models** (or adding models manually), test with the `ask_ai` tool.
2. If the test fails, confirm the base URL is correct by checking it directly:
   ```bash
   curl http://localhost:1234/v1/models
   # or for cloud providers:
   curl -H "Authorization: Bearer YOUR_KEY" https://api.groq.com/openai/v1/models
   ```

---

## 2.6 Adding Models

After creating a provider, you need at least one model record before the gateway can make AI calls.

Go to **MCP Gateway → Configuration → Models → New**:

| Field | Description |
|---|---|
| Name | Exact model ID as expected by the provider API |
| Provider | Select the parent provider |
| Use Type | `Chat Completion`, `Text Embedding`, or `Multimodal / Vision` |
| Default for Use | Check this to make it the automatic selection for this provider + use type. Only one active default is allowed per provider per use type |
| Active | Uncheck to disable a model without deleting it |

### Model ID Reference

| Provider | Chat Model IDs | Embedding Model IDs |
|---|---|---|
| OpenAI | `gpt-4o` `gpt-4o-mini` `gpt-4-turbo` `gpt-3.5-turbo` | `text-embedding-3-small` `text-embedding-3-large` |
| Anthropic | `claude-opus-4-7` `claude-sonnet-4-6` `claude-haiku-4-5-20251001` | *(not supported)* |
| Google Gemini | `gemini-2.5-flash` `gemini-2.5-pro` `gemini-2.0-flash` | `text-embedding-004` |
| Ollama | `llama3` `mistral` `gemma3` `phi4` `qwen2.5` | `nomic-embed-text` `mxbai-embed-large` |
| Groq | `llama-3.3-70b-versatile` `mixtral-8x7b-32768` | — |

### Setting a Default Model

Mark at least one chat model as **Default for Use = true** per provider. Without a default, the gateway must guess which model to use.

### Verifying Provider + Model Setup

Go to **MCP Gateway → Tools**, find **ask_ai**, click **Test Tool**, and enter:

```
Hello, which AI model are you?
```

The tool log (MCP Gateway → Tool Logs) shows the **Provider Used** and **Model Used** fields for each call, confirming exactly which model answered.

---

---

# Section 3: Connecting Chat Bots

The bot gateway lets users on Telegram, WhatsApp, Discord, and a custom web widget send natural-language messages to Odoo. The bot understands the message, calls the appropriate Odoo tool, and replies in plain language — all automatically.

---

## 3.1 Required Settings Before Any Bot

Two values must be configured in Odoo **Settings → MCP Gateway** before any bot channel will work.

### Webhook Secret

The webhook secret is a random token appended to every bot webhook URL as `?secret=SECRET`. Any incoming request that does not include this secret is rejected with HTTP 401. This prevents unauthorized actors from sending fake messages to your bots.

**How to configure:**

1. Go to **Settings → MCP Gateway** (scroll to the Bot Gateway section).
2. Click **Generate Webhook Secret**.
3. The secret is saved automatically to Odoo's system parameters.

> The secret is also auto-generated the first time you click **Connect** on any bot channel, so this step is optional — but doing it explicitly gives you visibility of the value before setting up webhooks.

> **Warning:** If you click Generate Webhook Secret again later, every existing bot webhook URL immediately becomes invalid. You must disconnect and reconnect all bot channels to register the new secret with each platform.

### Bot MCP API Key

The bot gateway calls `/mcp_gateway` over HTTP (loopback) to execute tools. It authenticates using an Odoo API key stored in system parameters.

**How to configure:**

1. In the same Settings section, click **Generate Bot MCP API Key**.
2. The key is created and saved automatically.

> Without this key, all bot messages receive the reply: *"Bot gateway is not fully configured. Please ask an administrator to generate the MCP API Key in Settings."*

---

## 3.2 Telegram Bot

### How it works

You create a Telegram bot via @BotFather, paste the bot token into Odoo, and click **Connect**. Odoo calls the Telegram API to register a webhook URL — from that point, every message sent to your bot is forwarded to Odoo, processed by AI, and replied to automatically.

### Step 1 — Create the Bot on Telegram

1. Open Telegram and search for **@BotFather**.
2. Send the command `/newbot`.
3. Follow the prompts: choose a display name and a username (must end in `bot`, e.g. `MyOdooBot`).
4. BotFather replies with an **API token** in the format `123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxx`. Copy it.

### Step 2 — Create the Channel in Odoo

Go to **MCP Gateway → Bot Channels → New** and fill in:

| Field | Value | Notes |
|---|---|---|
| Name | Any label, e.g. `My Telegram Bot` | Auto-updated to `@username` on connect |
| Platform | `Telegram` | |
| Bot Token / API Key | The token from BotFather | |
| Public HTTPS Base URL | e.g. `https://odoo.mycompany.com` | Leave blank if `web.base.url` in Settings → Technical → System Parameters is already a public HTTPS URL. Required for local/HTTP setups. |

### Configuration Example

```
Name:                  My Telegram Bot
Platform:              Telegram
Bot Token / API Key:   123456789:AAFxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Public HTTPS Base URL: https://odoo.mycompany.com
```

### Step 3 — Connect

Click **Connect**. Odoo performs two operations:

1. **Token validation:** calls `https://api.telegram.org/bot{TOKEN}/getMe`. If the token is invalid, an error message appears on the channel record.
2. **Webhook registration:** calls `https://api.telegram.org/bot{TOKEN}/setWebhook` with the URL:
   ```
   https://odoo.mycompany.com/bot/telegram?secret=YOUR_WEBHOOK_SECRET
   ```

On success:
- The channel **Status** changes to **Connected**.
- The **Bot Username** field is filled in (e.g. `MyOdooBot`).
- A success notification appears showing the webhook URL and a direct link to the bot (`https://t.me/MyOdooBot`).

### Local Development — Using ngrok

Telegram requires a public HTTPS URL. If Odoo is running on localhost:

```bash
# Install ngrok from ngrok.com, then:
ngrok http 8018
```

ngrok prints a URL like `https://a1b2c3d4.ngrok.io`. Paste this into **Public HTTPS Base URL** on the channel record before clicking **Connect**.

### Verifying the Connection

| Check | How to verify |
|---|---|
| Channel Status = Connected | Visible in the Bot Channels list |
| Bot Username is filled | Appears on the channel form after Connect |
| Live message test | Send any message to the bot in Telegram — you should get an AI reply within a few seconds |
| Odoo server log | Look for: `BotGateway: telegram \| user=123456 \| text=...` |
| Webhook confirmed | Check in Telegram: `https://api.telegram.org/bot{TOKEN}/getWebhookInfo` — `"url"` should match and `"last_error_message"` should be empty |

**Common errors:**

| Error on channel record | Cause | Fix |
|---|---|---|
| "Telegram rejected the token" | Token is invalid or revoked | Go to @BotFather → /mybots → select bot → API Token → Revoke and copy a new one |
| "Webhook registration failed" | Odoo URL is HTTP or not publicly reachable | Provide a valid public HTTPS URL in Public HTTPS Base URL |
| Status stays at "Not Connected" | Connect was not clicked | Click the **Connect** button |

---

## 3.3 WhatsApp Bot

### How it works

WhatsApp Cloud API (Meta) uses a two-step webhook setup: first you configure the channel in Odoo (Odoo side), then you register the webhook URL in the Meta Developer Console (Meta side). Meta sends a verification request to confirm the URL is real before activating it.

### Step 1 — Meta Developer Setup

1. Go to [developers.facebook.com](https://developers.facebook.com) and log in with a Facebook / Meta account.
2. Click **My Apps → Create App**.
3. Choose app type **Business** and fill in the details.
4. On the app dashboard, click **Add Product** and select **WhatsApp**.
5. In **WhatsApp → API Setup**:
   - Under **Phone numbers**, copy the **Phone Number ID** (a long numeric string — this is NOT the display phone number like +1-555-0100, it is an internal ID like `123456789012345`).
   - Click **Generate Token** (or set up a **System User Token** for permanent access). Copy the access token.

### Step 2 — Create the Channel in Odoo

Go to **MCP Gateway → Bot Channels → New** and fill in:

| Field | Value | Notes |
|---|---|---|
| Name | Any label, e.g. `WhatsApp Support` | |
| Platform | `WhatsApp` | |
| Bot Token / API Key | The access token from Meta | Use a permanent System User token for production |
| Phone Number ID | The numeric ID from Meta API Setup | Not the display phone number |
| Public HTTPS Base URL | e.g. `https://odoo.mycompany.com` | Must be public HTTPS |

### Configuration Example

```
Name:                  WhatsApp Support
Platform:              WhatsApp
Bot Token / API Key:   EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Phone Number ID:       123456789012345
Public HTTPS Base URL: https://odoo.mycompany.com
```

### Step 3 — Connect (Odoo Side)

Click **Connect**. Odoo validates the credentials and sets the status to **Connected**. A success notification appears with three critical values — copy all three:

```
Verify URL:    https://odoo.mycompany.com/bot/whatsapp/verify
Webhook URL:   https://odoo.mycompany.com/bot/whatsapp?secret=YOUR_WEBHOOK_SECRET
Verify Token:  YOUR_WEBHOOK_SECRET   (same as the webhook secret in Settings)
```

### Step 4 — Register the Webhook in Meta Console

1. In the Meta Developer Console, go to **WhatsApp → Configuration → Webhooks**.
2. Click **Edit**.
3. Fill in:

| Field | Value |
|---|---|
| Callback URL | `https://odoo.mycompany.com/bot/whatsapp?secret=YOUR_WEBHOOK_SECRET` |
| Verify Token | The webhook secret value from the Odoo notification |

4. Click **Verify and Save**.
   - Meta sends a GET request to `https://odoo.mycompany.com/bot/whatsapp/verify?hub.mode=subscribe&hub.challenge=RANDOM&hub.verify_token=YOUR_SECRET`.
   - Odoo checks that the verify token matches and echoes the challenge value.
   - If the token matches, Meta confirms the webhook with a green checkmark.
5. Under **Webhook Fields**, click **Manage** and subscribe to the **messages** field.

### Verifying the Connection

| Check | How to verify |
|---|---|
| Channel Status = Connected | Visible in the Bot Channels list |
| Meta webhook shows green checkmark | In Meta Console → WhatsApp → Configuration → Webhooks |
| Live message test | Send a WhatsApp message to your business phone number — you should receive an AI reply |
| Odoo server log | Look for: `BotGateway: whatsapp \| user=+1234567890 \| text=...` |

**Common errors:**

| Problem | Cause | Fix |
|---|---|---|
| Webhook verification fails in Meta | Verify token does not match | Check **Settings → MCP Gateway** for the exact webhook secret and re-enter it in Meta Console |
| No reply after sending message | messages webhook field not subscribed | In Meta Console → Webhooks → Manage → enable messages |
| Temporary token expired | Using a short-lived token | Generate a System User Token (permanent) from Meta Business Manager |

---

## 3.4 Discord Bot

### How it works

Discord uses an "Interactions Endpoint URL" — instead of polling for events, Discord sends a POST to your URL every time a user triggers a slash command or sends a message in a channel the bot monitors. Odoo handles the request and replies via Discord's REST API.

### Step 1 — Create the Bot in the Discord Developer Portal

1. Go to [discord.com/developers/applications](https://discord.com/developers/applications).
2. Click **New Application**, give it a name (e.g. `Odoo Assistant`), and click **Create**.
3. In the left sidebar, click **Bot**.
4. Click **Reset Token**, confirm the prompt, and copy the bot token. Store it safely.
5. Under **Privileged Gateway Intents**, enable **Message Content Intent** if you want the bot to read regular channel messages (not just slash commands).
6. Go to **OAuth2 → URL Generator**.
   - Scopes: check `bot`.
   - Bot Permissions: check `Send Messages`.
   - Copy the generated URL and open it in a browser to invite the bot to your Discord server.

### Step 2 — Create the Channel in Odoo

Go to **MCP Gateway → Bot Channels → New** and fill in:

| Field | Value | Notes |
|---|---|---|
| Name | Any label, e.g. `Discord Odoo Bot` | |
| Platform | `Discord` | |
| Bot Token / API Key | The bot token from the Discord Developer Portal | |
| Public HTTPS Base URL | e.g. `https://odoo.mycompany.com` | Must be public HTTPS |

### Configuration Example

```
Name:                  Discord Odoo Bot
Platform:              Discord
Bot Token / API Key:   MTIzNDU2Nzg5MDEy.xxxxxxxxxx.yyyyyyyyyyyyyyy
Public HTTPS Base URL: https://odoo.mycompany.com
```

### Step 3 — Connect (Odoo Side)

Click **Connect**. Odoo sets the channel status to **Connected** and shows the Interactions Endpoint URL in the success notification:

```
https://odoo.mycompany.com/bot/discord?secret=YOUR_WEBHOOK_SECRET
```

Copy this URL.

### Step 4 — Register the Interactions Endpoint in Discord

1. In the Discord Developer Portal, go to **General Information**.
2. Find the **Interactions Endpoint URL** field.
3. Paste the URL from the Odoo notification.
4. Click **Save Changes**.

Discord immediately sends a verification PING (a POST with `{"type": 1}`) to the URL. Odoo responds with `{"type": 1}` (PONG) without requiring authentication. Discord shows a green checkmark when the PONG is received.

### Step 5 — Register Slash Commands (Optional)

To allow users to invoke the bot with `/ask` or similar slash commands, you can register them via the Discord API or a bot framework. This is optional — the bot also responds to regular channel messages.

### Verifying the Connection

| Check | How to verify |
|---|---|
| Channel Status = Connected | Visible in the Bot Channels list |
| Discord shows green checkmark | In Discord Developer Portal → General Information → Interactions Endpoint URL |
| Live message test | Send a message in a channel where the bot is present — you should receive an AI reply |
| Odoo server log | Look for: `BotGateway: Discord PING received — responding with PONG` then `BotGateway: discord \| user=... \| text=...` |

**Common errors:**

| Problem | Cause | Fix |
|---|---|---|
| Discord rejects the Interactions Endpoint URL | URL is HTTP or not reachable | Must be public HTTPS — use ngrok for local testing |
| "Invalid interaction" errors | Secret in URL does not match stored secret | Disconnect, regenerate webhook secret in Settings if needed, reconnect |
| Bot is in the server but not responding | Message Content Intent not enabled | Enable it in Discord Developer Portal → Bot → Privileged Gateway Intents |

---

## 3.5 Web Chat Widget

### How it works

The web adapter accepts plain JSON POST requests. There is no platform account to create — you just create the channel in Odoo, get the endpoint URL, and start sending requests from any client (website, mobile app, custom frontend, or `curl`).

### Step 1 — Create the Channel in Odoo

Go to **MCP Gateway → Bot Channels → New** and fill in:

| Field | Value | Notes |
|---|---|---|
| Name | Any label, e.g. `Website Chat` | |
| Platform | `Web Widget` | |
| Public HTTPS Base URL | e.g. `https://odoo.mycompany.com` | Optional if `web.base.url` is already correct |

Click **Connect**. The success notification shows the endpoint:

```
https://odoo.mycompany.com/bot/web?secret=YOUR_WEBHOOK_SECRET
```

### Configuration Example

```
Name:                  Website Chat
Platform:              Web Widget
Public HTTPS Base URL: https://odoo.mycompany.com

→ Endpoint: https://odoo.mycompany.com/bot/web?secret=abc123xyz
```

### Sending Messages

You can pass the secret in the URL (as shown above) or in an HTTP header. Both approaches work:

**Option A — Secret in URL:**

```bash
curl -X POST "https://odoo.mycompany.com/bot/web?secret=YOUR_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user-alice",
    "message": "Show me all open sales orders"
  }'
```

**Option B — Secret in Header:**

```bash
curl -X POST https://odoo.mycompany.com/bot/web \
  -H "Content-Type: application/json" \
  -H "X-Bot-Secret: YOUR_WEBHOOK_SECRET" \
  -d '{
    "session_id": "user-alice",
    "message": "How many customers do we have?"
  }'
```

### Request Body Fields

| Field | Type | Required | Description |
|---|---|---|---|
| session_id | string | Yes | Unique identifier for the user or browser session. Conversations are stored per session_id so the bot remembers context. Use any string: UUID, username, cookie value, etc. |
| message | string | Yes | The user's message text |
| attachments | array | No | Optional list of file references |
| metadata | object | No | Optional passthrough data returned in the response |

### Response Format

```json
{
  "reply": "You have 23 open sales orders. The largest is SO/2026/0042 for Acme Corp...",
  "tool_used": "search_records",
  "session_id": "user-alice"
}
```

| Field | Description |
|---|---|
| reply | The AI-generated response in plain language |
| tool_used | The Odoo tool that was called to answer the question |
| session_id | Echo of the session_id from the request |

### Full Conversation Example

```bash
# First message
curl -X POST "https://odoo.mycompany.com/bot/web?secret=abc123" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user-bob", "message": "Hi, how many customers do we have?"}'

# Response:
# {"reply": "You currently have 342 active customers in Odoo.", "tool_used": "search_records", "session_id": "user-bob"}

# Follow-up — the bot remembers context from the previous message
curl -X POST "https://odoo.mycompany.com/bot/web?secret=abc123" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "user-bob", "message": "Which of them have not placed an order this year?"}'

# Response:
# {"reply": "I found 58 customers who have not placed any orders in 2026...", "tool_used": "analyze_records", "session_id": "user-bob"}
```

### Verifying the Connection

**Health check:**

```bash
curl https://odoo.mycompany.com/bot/health
```

**Expected response:**

```json
{
  "status": "ok",
  "gateway": "Bot Integration Layer",
  "platforms": ["telegram", "whatsapp", "web", "discord"]
}
```

**Live test:**

```bash
curl -X POST "https://odoo.mycompany.com/bot/web?secret=YOUR_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "test-session", "message": "Hello"}'
```

| Response | Meaning |
|---|---|
| JSON with `"reply"` field | Bot is working correctly |
| `{"error": "Unauthorized"}` | Webhook secret is wrong |
| `{"error": "Too many requests"}` | Rate limit hit — wait and try again |
| `"Bot gateway is not fully configured"` | Bot MCP API Key is missing — see Section 3.1 |
| Connection refused | Odoo is not running or the URL is wrong |

---

### Bot Channel Status Reference (All Platforms)

Go to **MCP Gateway → Bot Channels** to see the status of all channels.

| Status | Meaning |
|---|---|
| Not Connected | Channel was created but **Connect** has not been clicked, or it was disconnected |
| Connected | Webhook is registered and the channel is receiving messages |
| Error | The last **Connect** attempt failed — the **Error Message** field shows the reason |

To disconnect a channel, open it and click **Disconnect**. This removes the webhook from the platform (where supported) and sets the status back to **Not Connected**.
