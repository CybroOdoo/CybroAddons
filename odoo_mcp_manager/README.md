# Odoo MCP Server

A single, turnkey solution for connecting AI assistants (Claude Desktop, Cursor, etc.) or Odoo's internal AI features to your business data.

## Features

- **Unified AI Provider & Model Management**: Centralized configuration for OpenAI, Anthropic, Ollama, and more.
- **Advanced Tool Framework**: Use the `@ai_tool` decorator to turn Odoo methods into AI-callable tools with automatic schema generation.
- **Full MCP Server Implementation**: official Model Context Protocol (MCP) server endpoints at `/mcp`.
- **AI-Ready Messaging**: Extensions for `mail.message` to support structured AI interactions.
- **AI Hub Dashboard**: Monitoring and management from a single interface.
- **Execution Tracking**: Detailed logs for all AI tool invocations.

## Installation

1. Copy the `odoo_mcp_gateway` folder to your Odoo custom addons directory.
2. Install external Python dependencies:
   ```bash
   pip install pydantic mcp jinja2
   ```
3. Update the app list and install **AI Connector Hub** in the Odoo interface.

## Quick Setup (Claude Desktop)

1. **Configure a Provider**: Navigate to *AI Hub > Configuration > Providers*. Create a new provider (e.g., OpenAI), enter your API key, and click **Fetch Models**.
2. **Set Default Model**: In the models list, mark your preferred chat model as "Default".
3. **Generate MCP Key**: Go to your User Profile (click avatar > My Profile) and click the **New MCP Key** button.
4. **Configure Claude**: Copy the generated configuration snippet and paste it into your `claude_desktop_config.json`.
5. **Restart Claude**: You're all set! Claude can now access your Odoo data via its built-in tools.

## Documentation

For more detailed information, see the [Features & Configuration Guide](https://github.com/google-deepmind/antigravity).
