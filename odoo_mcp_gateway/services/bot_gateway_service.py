# -*- coding: utf-8 -*-
"""
BotGatewayService — Central dispatch layer for the bot integration.

Flow:
  1. Load conversation memory from DB.
  2. LLMRouter converts natural language → (tool_name, parameters).
     └─ Falls back to KeywordRouter on any LLM error.
  3. MCPConnector calls /mcp_gateway with the resolved tool + params.
  4. If the tool returned raw ORM data, humanize it through ask_ai.
  5. Persist user + assistant messages.
  6. Return unified response dict.
"""

import json
import logging
import re

import requests

_logger = logging.getLogger(__name__)


# ── KeywordRouter ─────────────────────────────────────────────────────────────

class KeywordRouter:
    """
    Safe fallback router used when LLMRouter fails (e.g. provider rate-limit).

    ORM tools (search_records, create_record, etc.) require structured
    parameters that only an LLM can produce from natural language.  Routing
    to them without proper parameters causes validation errors, so this router
    always falls back to ask_ai for a meaningful conversational reply.
    """

    @classmethod
    def route(cls, text: str, _history: list) -> tuple:
        """Return ('ask_ai', {'prompt': text}) unconditionally."""
        _logger.debug(
            "KeywordRouter: LLM unavailable — routing '%s' → ask_ai", text[:60]
        )
        return 'ask_ai', {'prompt': text}


# ── LLMRouter ─────────────────────────────────────────────────────────────────

class LLMRouter:
    """
    Converts a natural-language user message into a structured (tool, parameters)
    pair by asking the configured AI provider to interpret the intent.

    Priority chain for provider selection:
      1. ask_ai tool's default_provider_id / default_model_id.
      2. First active provider ordered by priority (asc).

    Falls back to KeywordRouter on any error so the bot always responds.
    """

    _SYSTEM_PROMPT = (
        'You are an Odoo ERP assistant that converts user messages into tool calls.\n\n'
        'AVAILABLE TOOLS:\n{tools}\n\n'
        'AVAILABLE ODOO MODELS:\n{models}\n\n'
        'INSTRUCTIONS:\n'
        '- Analyse the user message and return ONLY a valid JSON object — no markdown, no explanation.\n'
        '- Format: {{"tool": "<tool_name>", "parameters": {{...}}}}\n\n'
        'PARAMETER RULES:\n'
        '- ask_ai          → {{"prompt": "<user message>"}}\n'
        '- search_records  → {{"model": "<odoo.model.name>", "domain": [...], "limit": 10}}\n'
        '- create_record   → {{"model": "<odoo.model.name>", "values": {{...}}}}\n'
        '- update_record   → {{"model": "<odoo.model.name>", "res_id": <int>, "values": {{...}}}}\n'
        '- delete_record   → {{"model": "<odoo.model.name>", "res_id": <int>}}\n'
        '- analyze_records → {{"model": "<odoo.model.name>", "question": "<question>", "domain": [], "limit": 20}}\n\n'
        'DOMAIN SYNTAX: list of [field, operator, value] triples.\n'
        'Examples:\n'
        '  [["customer_rank", ">", 0]]\n'
        '  [["state", "=", "sale"], ["date_order", ">=", "2026-01-01"]]\n'
        '  [["payment_state", "=", "not_paid"]]\n\n'
        'DECISION GUIDE:\n'
        '- Greetings / general questions / anything unclear  → ask_ai\n'
        '- "show/find/list/search <something>"               → search_records\n'
        '- "create/add/register a <something>"               → create_record\n'
        '- "update/change/edit <something>"                  → update_record\n'
        '- "delete/remove <something>"                       → delete_record\n'
        '- "analyze/summarize/report on <something>"         → analyze_records\n\n'
        'Return ONLY the JSON object.'
    )

    def __init__(self, env):
        """Initialise the router with an Odoo Environment."""
        self.env = env

    def route(self, text: str, history: list) -> tuple:
        """
        Convert *text* into a (tool_name, parameters) pair.

        Never raises — falls back to KeywordRouter on any error.
        """
        try:
            return self._llm_route(text, history)
        except Exception as exc:
            _logger.warning(
                'LLMRouter: error (%s) — falling back to KeywordRouter', exc
            )
            return KeywordRouter.route(text, history)

    def _llm_route(self, text: str, history: list) -> tuple:
        """Run the LLM routing call and parse the response."""
        provider, model_name = self._routing_provider()
        system = self._SYSTEM_PROMPT.format(
            tools=self._tools_description(),
            models=self._models_description(),
        )
        messages = [{'role': 'system', 'content': system}]
        for msg in (history or [])[-4:]:
            messages.append({'role': msg['role'], 'content': msg['content']})
        messages.append({'role': 'user', 'content': text})

        extra = {'json_mode': True} if provider.service == 'ollama' else {}
        raw = provider.chat(messages, model=model_name, **extra)
        _logger.debug('LLMRouter raw: %s', raw[:400])

        parsed = self._extract_json(raw)
        tool = parsed.get('tool', 'ask_ai')
        params = parsed.get('parameters', {})

        if not isinstance(params, dict):
            params = {}
        if tool == 'ask_ai' and not params.get('prompt'):
            params['prompt'] = text

        _logger.info("LLMRouter: '%s' → %s %s", text[:60], tool, params)
        return tool, params

    def _routing_provider(self) -> tuple:
        """
        Resolve the provider used by LLMRouter to parse intent.

        Priority:
          1. ask_ai tool's default_provider_id — only if it has active chat models.
          2. Walk all active providers ordered by priority and pick the first with
             at least one active chat model.
        """
        ask_ai = self.env['ai.tool'].sudo().search(
            [('name', '=', 'ask_ai'), ('active', '=', True)], limit=1
        )
        if ask_ai and ask_ai.default_provider_id:
            provider = ask_ai.default_provider_id
            active_chat = provider.model_ids.filtered(
                lambda m: m.active and m.model_use == 'chat'
            )
            if active_chat:
                model = (
                    ask_ai.default_model_id.name
                    if ask_ai.default_model_id
                    else active_chat.filtered(lambda m: m.default)[:1].name
                    or active_chat[0].name
                )
                return provider, model

        providers = self.env['ai.provider'].sudo().search([('active', '=', True)])
        for provider in providers:
            active_chat = provider.model_ids.filtered(
                lambda m: m.active and m.model_use == 'chat'
            )
            if active_chat:
                default = active_chat.filtered(lambda m: m.default)
                model_name = default[0].name if default else active_chat[0].name
                return provider, model_name

        raise RuntimeError('No active AI provider with models configured')

    def _tools_description(self) -> str:
        """Build a newline-separated list of tool names and descriptions."""
        tools = self.env['ai.tool'].sudo().search([('active', '=', True)])
        return (
            '\n'.join(f'- {t.name}: {t.description}' for t in tools)
            or '- ask_ai: General AI assistant'
        )

    def _models_description(self) -> str:
        """Build a newline-separated list of exposed Odoo models."""
        resources = self.env['ai.resource'].sudo().search([('active', '=', True)])
        if resources:
            return '\n'.join(f'- {r.model_name}: {r.name}' for r in resources)
        return (
            '- res.partner: Contacts and Customers\n'
            '- sale.order: Sales Orders\n'
            '- account.move: Invoices and Bills\n'
            '- product.product: Products\n'
            '- purchase.order: Purchase Orders\n'
            '- stock.picking: Inventory Transfers\n'
            '- hr.employee: Employees'
        )

    @staticmethod
    def _extract_json(text: str) -> dict:
        """Extract the first JSON object from an LLM response string."""
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f'No JSON in LLM response: {text[:200]}')


# ── MCPConnector ──────────────────────────────────────────────────────────────

class MCPConnector:
    """
    Thin JSON-RPC client that calls the /mcp_gateway endpoint over loopback HTTP.

    Using loopback HTTP keeps the MCP layer fully decoupled: auth checks,
    consent checks, and logging all happen inside MCPController exactly as they
    do for any external MCP client.
    """

    def __init__(self, env):
        """Initialise the connector, reading the base URL and API key from system parameters."""
        self.env = env
        base_url = env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'http://localhost:8069'
        ).rstrip('/')
        self.endpoint = f'{base_url}/mcp_gateway'
        self.api_key = env['ir.config_parameter'].sudo().get_param(
            'bot_gateway.mcp_api_key', ''
        )

    def call_tool(self, tool_name: str, arguments: dict, request_id: int = 1) -> str:
        """
        Invoke an MCP tool and return the text content as a string.

        Never raises — returns a human-readable error string instead so the
        bot always produces a reply.

        Args:
            tool_name: Technical name of the ai.tool to call.
            arguments: Input parameters for the tool.
            request_id: JSON-RPC request id (for logging correlation).

        Returns:
            The tool's text output, or an error message string.
        """
        if not self.api_key:
            _logger.error(
                "MCPConnector: 'bot_gateway.mcp_api_key' is not set. "
                'Cannot call MCP tools.'
            )
            return (
                'Bot gateway is not fully configured. '
                'Please ask an administrator to generate the MCP API Key in Settings.'
            )

        payload = {
            'jsonrpc': '2.0',
            'method': 'tools/call',
            'id': request_id,
            'params': {'name': tool_name, 'arguments': arguments},
        }
        try:
            resp = requests.post(
                self.endpoint,
                json=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {self.api_key}',
                    'X-Odoo-MCP-Source': 'bot',
                },
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()

            if 'error' in data:
                err = data['error']
                _logger.warning(
                    'MCPConnector: MCP error %s — %s',
                    err.get('code'), err.get('message'),
                )
                return f"[Error] {err.get('message', 'Unknown MCP error')}"

            content_blocks = data.get('result', {}).get('content', [])
            text_parts = [
                block.get('text', '')
                for block in content_blocks
                if block.get('type') == 'text'
            ]
            return ' '.join(text_parts).strip() or '(empty response)'

        except requests.exceptions.Timeout:
            _logger.error('MCPConnector: request timed out → %s', self.endpoint)
            return 'The request timed out. Please try again.'
        except Exception:
            _logger.exception('MCPConnector: unexpected error')
            return 'An unexpected error occurred. Please try again later.'


# ── BotGatewayService ─────────────────────────────────────────────────────────

# Tools whose output is already human-readable — skip the humanize step.
_TEXT_TOOLS = {'ask_ai', 'analyze_records'}


class BotGatewayService:
    """
    Orchestrates the full request–response cycle for a single bot message.

    Usage::

        response = BotGatewayService(request.env).process(bot_message)
    """

    def __init__(self, env):
        """Initialise the service with an Odoo Environment."""
        self.env = env

    def process(self, bot_message: dict) -> dict:
        """
        Accept a unified BotMessage dict, run the full pipeline, and return a response.

        Args:
            bot_message: Unified message dict produced by a platform adapter.

        Returns:
            dict with keys ``text`` (str) and ``metadata`` (dict).
        """
        platform       = bot_message.get('platform', 'web')
        uid            = bot_message.get('platform_user_id', 'anonymous')
        text           = (bot_message.get('text') or '').strip()
        meta           = bot_message.get('metadata', {})
        username       = meta.get('username', '') or meta.get('display_phone', '') or ''
        bot_channel_id = meta.get('bot_channel_id', False)

        if not text:
            return {'text': 'Please send a text message.', 'metadata': {'tool': None}}

        conv = self.env['ai.bot.conversation'].sudo().get_or_create(
            platform, uid,
            platform_user_name=username,
            bot_channel_id=bot_channel_id,
        )
        history = conv.get_recent_messages(limit=10)

        tool_name, tool_args = LLMRouter(self.env).route(text, history)
        _logger.info(
            'BotGateway: platform=%s uid=%s tool=%s args=%s',
            platform, uid, tool_name, tool_args,
        )

        raw_result = MCPConnector(self.env).call_tool(tool_name, tool_args)

        if tool_name not in _TEXT_TOOLS and not raw_result.startswith('[Error]'):
            reply_text = self._humanize(text, tool_name, raw_result)
        else:
            reply_text = raw_result

        conv.sudo().add_message('user', text, None)
        conv.sudo().add_message('assistant', reply_text, tool_name)

        return {'text': reply_text, 'metadata': {'tool': tool_name}}

    def _humanize(self, original_text: str, tool_name: str, raw_result: str) -> str:
        """
        Convert raw ORM tool output into a friendly natural-language reply.

        Calls ask_ai directly via the ORM to avoid the MCPConnector 120 s timeout
        for slow providers like Ollama.  Falls back to the raw result on failure.

        Args:
            original_text: The user's original message.
            tool_name: Name of the tool that produced *raw_result*.
            raw_result: Raw JSON string returned by the tool.

        Returns:
            A friendly reply string, or *raw_result* if the AI call fails.
        """
        prompt = (
            f'The user asked: "{original_text}"\n\n'
            f'The system ran "{tool_name}" and got this result:\n'
            f'{raw_result}\n\n'
            'Write a clear, concise, friendly response to the user based on this data. '
            'Use bullet points for lists. Keep it conversational. '
            'Do not repeat the raw JSON — summarize it in plain language.'
        )
        ask_ai = self.env['ai.tool'].sudo().search(
            [('name', '=', 'ask_ai'), ('active', '=', True)], limit=1
        )
        if not ask_ai:
            return raw_result
        try:
            return ask_ai.execute({'prompt': prompt})
        except Exception:
            _logger.warning('BotGateway: humanize failed, returning raw result')
            return raw_result
