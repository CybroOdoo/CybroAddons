.. image:: https://img.shields.io/badge/licence-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

Odoo MCP Server
================
Unified AI Provider & MCP Tool Gateway for Odoo — connect external AI assistants
(Claude Desktop, Claude Code, claude.ai, Cursor, OpenAI Codex) and chat bots
(Telegram, WhatsApp, Discord, Web) to your Odoo data through a single, secure
gateway.

Overview
========
The MCP Gateway turns Odoo into a live, tool-enabled data source for AI clients
using the Model Context Protocol (MCP). It also ships a bot integration layer so
end users can talk to Odoo in natural language from popular chat platforms. A
unified provider layer (OpenAI, Anthropic, Google Gemini, Ollama, or any
OpenAI-compatible endpoint) powers the built-in AI tools, with automatic
priority-based fallback between providers.

Key Features
============
* **Full MCP server** — a Streamable-HTTP JSON-RPC endpoint (``/mcp_gateway``)
  implementing ``initialize``, ``tools/list``, ``tools/call``,
  ``resources/list``, ``resources/read`` and ``ping``.
* **Unified AI providers & models** — configure OpenAI, Anthropic, Google
  Gemini, Ollama and custom OpenAI-compatible providers; auto-fetch models where
  supported; priority ordering with automatic fallback.
* **Tool framework** — expose Odoo operations as AI tools via the ``@ai_tool``
  decorator or the generic built-ins (``search_records``, ``create_record``,
  ``update_record``, ``delete_record``, ``unlink_record``, ``ask_ai``,
  ``analyze_records``).
* **Bot integration layer** — Telegram, WhatsApp Cloud API, Discord and a
  generic Web widget, with per-conversation chat memory and LLM-based intent
  routing.
* **AI Hub dashboard** — live counts of providers, tools, sessions, keys,
  consents and recent activity.
* **Tool logging & sessions** — every tool invocation is logged (user, source,
  client, duration, status); MCP protocol sessions are tracked per client.
* **User consent gate** — flag sensitive tools to require explicit approval from
  a Consent Approver before they can run.

Security
========
* **Per-user execution** — tool calls run with the authenticated user's access
  rights and record rules (no blanket superuser access). Provider secrets and
  audit logs remain protected.
* **Model & operation allow-list** — an administrator controls exactly which
  models the generic built-in tools and the MCP resource reader may touch, and
  which operations (read / create / update / delete / unlink) are permitted.
  Reads are seeded for common models; destructive operations are **off by
  default** and must be enabled explicitly (MCP Gateway → Configuration →
  Tool Access Rules). Enforcement can be toggled in Settings.
* **Authenticated endpoints** — MCP requests authenticate with an Odoo API key;
  bot webhooks authenticate with a shared secret (Discord additionally verifies
  the Ed25519 request signature). Secret comparisons are constant-time.
* **Protected credentials** — provider API keys, bot tokens and gateway secrets
  are restricted to the System group.
* **Abuse protection** — per-IP rate limiting and request body-size caps on the
  gateway and webhook endpoints.

Required Python Packages
========================
Install the external dependencies used by the gateway::

    pip3 install pydantic
    pip3 install mcp
    pip3 install jinja2
    pip3 install requests

Installation
============
- Install the required Python packages listed above.
- Install the module from the Apps menu.

Configuration
=============
- Open **MCP Gateway → Configuration** and add at least one AI **Provider**
  (with its API key) and one **Model**.
- Generate an **MCP API Key** (Dashboard → New MCP Key) for each external AI
  client you connect.
- To use chat bots, generate the **Webhook Secret** and **Bot MCP API Key** in
  **Settings → MCP Gateway**, then create a **Bot Channel** per platform.
- Review **Configuration → Tool Access Rules** to enable any additional models
  or destructive operations you want the AI tools to perform.

See ``DOCUMENTATION.md`` for step-by-step setup guides for every AI client,
provider and bot platform.

License
=======
GNU Lesser General Public License, Version 3 (LGPL v3).
(https://www.gnu.org/licenses/lgpl-3.0-standalone.html)

Credits
=======
Developers: Cybrosys Techno Solutions <https://www.cybrosys.com>

Bug Tracker
===========
Bugs are tracked on GitHub. In case of trouble, please check there whether your
issue has already been reported.

Maintainer
==========
.. image:: https://cybrosys.com/images/logo.png
   :target: https://cybrosys.com

This module is maintained by Cybrosys Technologies.

For support and more information, please visit `Our Website <https://cybrosys.com/>`__
