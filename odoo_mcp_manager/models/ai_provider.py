# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AiProvider(models.Model):
    """
    Represents an external AI service (OpenAI, Anthropic, Google, Ollama, or a
    custom OpenAI-compatible endpoint).  Owns the API credentials, exposes a
    unified ``chat()`` / ``embedding()`` interface, and handles provider
    fallback chains automatically.
    """

    _name = 'ai.provider'
    _description = 'AI Provider'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority asc, name asc'

    name = fields.Char(required=True, tracking=True)
    priority = fields.Integer(
        default=10,
        tracking=True,
        help=(
            'Lower number = higher priority. When no provider is explicitly set, '
            'the system picks the highest-priority provider that has active models.'
        ),
    )
    service = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google Gemini'),
        ('ollama', 'Ollama'),
        ('custom', 'Custom (OpenAI Compatible)'),
    ], required=True, default='openai', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    api_key = fields.Char(
        groups='base.group_system',
        string='API Key / Token',
        help='Securely store API key',
    )
    api_base = fields.Char(string='Base URL', help='API Endpoint URL')
    model_ids = fields.One2many('ai.model', 'provider_id', string='Models')
    fallback_provider_ids = fields.Many2many(
        'ai.provider',
        'ai_provider_fallback_rel',
        'provider_id',
        'fallback_id',
        string='Fallback Providers',
        help='If the primary model fails, these providers will be tried in order.',
    )
    setup_guide = fields.Html(compute='_compute_setup_guide', string='Configuration Guide')

    # ── Connectivity status (updated by check_connection()) ─────────────────
    connection_status = fields.Selection([
        ('connected', 'Connected'),
        ('error', 'Error'),
        ('unchecked', 'Not Checked'),
    ], default='unchecked', string='Connection Status', readonly=True)
    connection_error = fields.Char(string='Last Error', readonly=True)
    last_checked = fields.Datetime(string='Last Checked', readonly=True)

    _SETUP_GUIDES = {
        'openai': """
            <div class="o_field_html">
                <h3>OpenAI Provider Setup</h3>
                <p>OpenAI provides industry-leading language models including GPT-4o, GPT-4 Turbo, and GPT-3.5 Turbo.</p>
                <h4>Step 1 — Get your API Key</h4>
                <ol>
                    <li>Go to <strong>platform.openai.com</strong> and sign in or create an account.</li>
                    <li>Navigate to <strong>API Keys</strong> under your profile settings.</li>
                    <li>Click <strong>Create new secret key</strong>, give it a name, and copy the key immediately (it won't be shown again).</li>
                </ol>
                <h4>Step 2 — Configure this Provider</h4>
                <ul>
                    <li><strong>API Key:</strong> Paste the key copied above.</li>
                    <li><strong>Base URL:</strong> Leave blank to use the default (<code>https://api.openai.com/v1</code>), or set a custom proxy if needed.</li>
                </ul>
                <h4>Step 3 — Add Models</h4>
                <p>Click <strong>Fetch Models</strong> to auto-populate available models, or add them manually:</p>
                <ul>
                    <li><code>gpt-4o</code> — Best for complex reasoning and multimodal tasks.</li>
                    <li><code>gpt-4o-mini</code> — Fast and cost-efficient for everyday tasks.</li>
                    <li><code>gpt-4-turbo</code> — High intelligence with a 128k context window.</li>
                    <li><code>text-embedding-3-small</code> — Lightweight embedding model.</li>
                    <li><code>text-embedding-3-large</code> — High-quality embedding model.</li>
                </ul>
                <h4>Pricing &amp; Limits</h4>
                <p>OpenAI charges per token. Monitor usage at <strong>platform.openai.com/usage</strong>. Set spending limits under <strong>Billing &gt; Usage limits</strong> to avoid unexpected charges.</p>
            </div>
        """,
        'anthropic': """
            <div class="o_field_html">
                <h3>Anthropic Provider Setup</h3>
                <p>Anthropic's Claude models are designed for safety, accuracy, and long-context reasoning.</p>
                <h4>Step 1 — Get your API Key</h4>
                <ol>
                    <li>Go to <strong>console.anthropic.com</strong> and sign in or create an account.</li>
                    <li>Navigate to <strong>API Keys</strong> in the left sidebar.</li>
                    <li>Click <strong>Create Key</strong>, name it, and copy the key immediately.</li>
                </ol>
                <h4>Step 2 — Configure this Provider</h4>
                <ul>
                    <li><strong>API Key:</strong> Paste the key copied above.</li>
                    <li><strong>Base URL:</strong> Leave blank (defaults to <code>https://api.anthropic.com</code>). Only change if using a proxy or AWS Bedrock endpoint.</li>
                </ul>
                <h4>Step 3 — Add Models</h4>
                <p>Add models manually using their official IDs:</p>
                <ul>
                    <li><code>claude-opus-4-7</code> — Most intelligent, best for complex tasks.</li>
                    <li><code>claude-sonnet-4-6</code> — Balanced performance and speed (recommended).</li>
                    <li><code>claude-haiku-4-5-20251001</code> — Fastest and most compact Claude model.</li>
                </ul>
                <h4>Notes</h4>
                <p>Anthropic does not expose a model list API, so <strong>Fetch Models</strong> is not available. Add model IDs manually from <strong>docs.anthropic.com/en/docs/about-claude/models</strong>.</p>
            </div>
        """,
        'ollama': """
            <div class="o_field_html">
                <h3>Ollama Provider Setup</h3>
                <p>Ollama lets you run open-source AI models (Llama, Mistral, Gemma, etc.) locally on your own hardware — no API key required.</p>
                <h4>Step 1 — Install Ollama</h4>
                <ol>
                    <li>Download and install Ollama from <strong>ollama.com</strong>.</li>
                    <li>Start the Ollama service: run <code>ollama serve</code> in a terminal (or it starts automatically on install).</li>
                    <li>Pull a model: <code>ollama pull llama3</code> or any model from <strong>ollama.com/library</strong>.</li>
                </ol>
                <h4>Step 2 — Configure this Provider</h4>
                <ul>
                    <li><strong>API Key:</strong> Leave blank — Ollama does not require authentication by default.</li>
                    <li><strong>Base URL:</strong> Set to <code>http://localhost:11434</code> (default Ollama port). If Odoo runs in Docker, use the host IP instead of <code>localhost</code>.</li>
                </ul>
                <h4>Step 3 — Add Models</h4>
                <p>Click <strong>Fetch Models</strong> to pull the list of models you have already downloaded, or add them manually:</p>
                <ul>
                    <li><code>llama3</code> — Meta's Llama 3 8B, strong general-purpose model.</li>
                    <li><code>mistral</code> — Mistral 7B, fast and efficient.</li>
                    <li><code>gemma3</code> — Google's Gemma 3, lightweight and capable.</li>
                    <li><code>nomic-embed-text</code> — Embedding model for semantic search.</li>
                </ul>
                <h4>Docker / Network Note</h4>
                <p>If Odoo runs inside Docker, Ollama must be reachable from inside the container. Use <code>http://host.docker.internal:11434</code> on Mac/Windows, or the host's LAN IP on Linux.</p>
            </div>
        """,
        'custom': """
            <div class="o_field_html">
                <h3>Custom (OpenAI-Compatible) Provider Setup</h3>
                <p>Use this type for any API that implements the OpenAI chat completion interface — such as LM Studio, vLLM, Together AI, Groq, Azure OpenAI, or a self-hosted gateway.</p>
                <h4>Configure this Provider</h4>
                <ul>
                    <li><strong>Base URL:</strong> Set the full base URL of the compatible endpoint, e.g.:<br/>
                        <code>http://localhost:1234/v1</code> (LM Studio)<br/>
                        <code>https://api.groq.com/openai/v1</code> (Groq)<br/>
                        <code>https://&lt;resource&gt;.openai.azure.com/openai/deployments/&lt;deployment&gt;</code> (Azure)
                    </li>
                    <li><strong>API Key:</strong> Required for cloud providers (Groq, Together, Azure). Leave blank for local services that have no auth.</li>
                </ul>
                <h4>Add Models</h4>
                <p>Click <strong>Fetch Models</strong> to list available models, or add model names manually matching the deployment or model ID used by your provider.</p>
                <h4>Common Compatible Services</h4>
                <ul>
                    <li><strong>LM Studio</strong> — Local GUI for running GGUF models. Base URL: <code>http://localhost:1234/v1</code></li>
                    <li><strong>Groq</strong> — Cloud inference at very high speed. API key from <strong>console.groq.com</strong>.</li>
                    <li><strong>Together AI</strong> — Fine-tuning + inference. API key from <strong>api.together.ai</strong>.</li>
                    <li><strong>vLLM</strong> — High-throughput self-hosted inference server.</li>
                </ul>
            </div>
        """,
        'google': """
            <div class="o_field_html">
                <h3>Google Gemini Provider Setup</h3>
                <p>Google Gemini provides powerful multimodal language models including Gemini 2.5 Flash and Gemini 2.0.</p>
                <h4>Step 1 — Get your API Key</h4>
                <ol>
                    <li>Go to <strong>aistudio.google.com</strong> and sign in.</li>
                    <li>Click <strong>Get API Key</strong> → <strong>Create API Key</strong>.</li>
                    <li>Copy the key (it is shown once, save it immediately).</li>
                </ol>
                <h4>Step 2 — Configure this Provider</h4>
                <ul>
                    <li><strong>API Key:</strong> Paste the key copied above.</li>
                    <li><strong>Base URL:</strong> Leave blank to use the default (<code>https://generativelanguage.googleapis.com/v1beta</code>).</li>
                </ul>
                <h4>Step 3 — Add Models</h4>
                <p>Click <strong>Fetch Models</strong> to auto-populate available models, or add them manually:</p>
                <ul>
                    <li><code>gemini-2.5-flash</code> — Fast, cost-efficient, 1M context.</li>
                    <li><code>gemini-2.5-pro</code> — Most capable Gemini model.</li>
                    <li><code>gemini-2.0-flash</code> — High-speed multimodal model.</li>
                </ul>
                <h4>Notes</h4>
                <p>Google Gemini uses <code>?key=YOUR_API_KEY</code> as a query parameter, not a Bearer token. This is handled automatically by the gateway.</p>
            </div>
        """,
    }

    @api.depends('service')
    def _compute_setup_guide(self) -> None:
        """Populate the HTML setup guide for the currently selected service."""
        for rec in self:
            rec.setup_guide = self._SETUP_GUIDES.get(
                rec.service,
                '<p>Select a service to see the configuration guide.</p>',
            )

    def action_fetch_models(self) -> dict:
        """Open the Fetch Models wizard pre-populated with this provider."""
        self.ensure_one()
        return {
            'name': _('Fetch Models from %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'ai.fetch.model.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_provider_id': self.id},
        }

    def write(self, vals: dict) -> bool:
        """Cascade active/inactive state to models; reset connection status when credentials change."""
        res = super().write(vals)
        if 'active' in vals:
            for provider in self:
                provider.with_context(active_test=False).model_ids.write(
                    {'active': vals['active']}
                )
        # Reset connection status when any credential-related field changes
        if any(k in vals for k in ('api_key', 'api_base', 'service', 'active')):
            self.write_connection_reset()
        return res

    def write_connection_reset(self) -> None:
        """Reset connection status to unchecked without triggering write() recursion."""
        self.env.cr.execute(
            "UPDATE ai_provider SET connection_status='unchecked', "
            "connection_error=NULL, last_checked=NULL WHERE id IN %s",
            (tuple(self.ids),)
        )
        self.invalidate_recordset(['connection_status', 'connection_error', 'last_checked'])

    def action_check_connection(self) -> dict:
        """Button action: check connectivity for all records in self and return a notification."""
        results = []
        for provider in self:
            ok, err = provider.check_connection()
            results.append((provider.name, ok, err))

        # Build a user-friendly summary message
        success = [n for n, ok, _ in results if ok]
        failed  = [n for n, ok, _ in results if not ok]
        if failed:
            msg = ', '.join(failed) + ' failed connectivity check.'
            msg_type = 'warning'
        else:
            msg = ', '.join(success) + ' connected successfully.'
            msg_type = 'success'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connectivity Check'),
                'message': msg,
                'type': msg_type,
                'sticky': False,
            },
        }

    def check_connection(self) -> tuple:
        """
        Perform a real lightweight HTTP call to verify this provider is reachable
        and the API key is accepted.

        Returns:
            (True, '') on success
            (False, error_message) on failure
        """
        self.ensure_one()
        try:
            ok, err = self._ping_service()
        except Exception as e:
            ok, err = False, str(e)

        self.env.cr.execute(
            "UPDATE ai_provider SET connection_status=%s, connection_error=%s, "
            "last_checked=%s WHERE id=%s",
            ('connected' if ok else 'error', err or None,
             fields.Datetime.now(), self.id)
        )
        self.invalidate_recordset(['connection_status', 'connection_error', 'last_checked'])
        return ok, err

    def _ping_service(self) -> tuple:
        """
        Make a minimal HTTP request to the provider API.
        HTTP 200 → connected.  HTTP 401/403 → bad key (endpoint reachable but auth failed).
        Network error / timeout → not reachable.
        """
        self.ensure_one()
        timeout = 8  # seconds — fast enough for a dashboard check

        service = self.service

        # ── OpenAI / Custom (OpenAI-compatible) ────────────────────────────
        if service in ('openai', 'custom'):
            base = (self.api_base or 'https://api.openai.com/v1').rstrip('/')
            headers = {'Content-Type': 'application/json'}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            resp = requests.get(f'{base}/models', headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return True, ''
            return False, f'HTTP {resp.status_code}: {resp.text[:120]}'

        # ── Anthropic ──────────────────────────────────────────────────────
        elif service == 'anthropic':
            if not self.api_key:
                return False, 'API key is not configured.'
            base = (self.api_base or 'https://api.anthropic.com/v1').rstrip('/')
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json',
            }
            # Anthropic has no public /models endpoint; send a minimal messages
            # request with max_tokens=1 — 200 means connected, 400 bad request
            # is also fine (means auth passed), anything else is an error.
            payload = {
                'model': 'claude-3-haiku-20240307',
                'max_tokens': 1,
                'messages': [{'role': 'user', 'content': 'ping'}],
            }
            resp = requests.post(
                f'{base}/messages', headers=headers,
                json=payload, timeout=timeout
            )
            if resp.status_code in (200, 400):  # 400 = bad request but auth ok
                return True, ''
            return False, f'HTTP {resp.status_code}: {resp.text[:120]}'

        # ── Google Gemini ──────────────────────────────────────────────────
        elif service == 'google':
            if not self.api_key:
                return False, 'API key is not configured.'
            base = (
                self.api_base or 'https://generativelanguage.googleapis.com/v1beta'
            ).rstrip('/')
            resp = requests.get(
                f'{base}/models', params={'key': self.api_key}, timeout=timeout
            )
            if resp.status_code == 200:
                return True, ''
            return False, f'HTTP {resp.status_code}: {resp.text[:120]}'

        # ── Ollama (local — no auth) ────────────────────────────────────────
        elif service == 'ollama':
            base = (self.api_base or 'http://localhost:11434').rstrip('/')
            url = f'{base}/tags' if base.endswith('/api') else f'{base}/api/tags'
            resp = requests.get(url, timeout=timeout)
            if resp.status_code == 200:
                return True, ''
            return False, f'HTTP {resp.status_code}: {resp.text[:120]}'

        return False, f'Unknown service type: {service}'

    # ── Dynamic Model Discovery ───────────────────────────────────────────────

    def fetch_available_models(self) -> list:
        """
        Fetch the list of models from the live provider API.
        Automatically updates ``connection_status`` to 'connected' on success
        or 'error' on failure — so fetching models doubles as a connectivity check.

        Returns:
            list[dict]: Each dict has keys ``name`` (str) and ``model_use`` (str).

        Raises:
            UserError: When the service does not support model listing.
        """
        self.ensure_one()
        handler = f'_fetch_models_{self.service}'
        if not hasattr(self, handler):
            raise UserError(_(
                "Model fetching is not supported for service '%s'."
            ) % self.service)
        try:
            result = getattr(self, handler)()
            # ✅ success → mark as connected
            self.env.cr.execute(
                "UPDATE ai_provider SET connection_status='connected', "
                "connection_error=NULL, last_checked=%s WHERE id=%s",
                (fields.Datetime.now(), self.id)
            )
            self.invalidate_recordset(['connection_status', 'connection_error', 'last_checked'])
            return result
        except Exception as e:
            # ❌ failure → mark as error and re-raise so the UI sees the error
            self.env.cr.execute(
                "UPDATE ai_provider SET connection_status='error', "
                "connection_error=%s, last_checked=%s WHERE id=%s",
                (str(e)[:255], fields.Datetime.now(), self.id)
            )
            self.invalidate_recordset(['connection_status', 'connection_error', 'last_checked'])
            raise

    def _classify_model_use(self, name: str) -> str:
        """Infer ``model_use`` from the model name/id string."""
        n = name.lower()
        if any(k in n for k in ('embed', 'embedding')):
            return 'embedding'
        if any(k in n for k in ('vision', 'llava', 'moondream', 'bakllava', '-vl', 'vl-')):
            return 'multimodal'
        return 'chat'

    def _fetch_openai_compat_models(self, base: str, require_key: bool = True) -> list:
        """Shared model listing for OpenAI-compatible ``/models`` endpoints."""
        if require_key and not self.api_key:
            raise UserError(_('API key is required to fetch models.'))
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        try:
            response = requests.get(f'{base}/models', headers=headers, timeout=15)
            response.raise_for_status()
            return sorted(
                [
                    {'name': item['id'], 'model_use': self._classify_model_use(item['id'])}
                    for item in response.json().get('data', [])
                    if item.get('id')
                ],
                key=lambda x: x['name'],
            )
        except UserError:
            raise
        except requests.RequestException as e:
            _logger.exception('%s model fetch error', self.service)
            raise UserError(_('Failed to fetch models: %s') % str(e))

    def _fetch_models_openai(self) -> list:
        """GET /models from the OpenAI API and return a classified model list."""
        self.ensure_one()
        if not self.api_key:
            raise UserError(_('OpenAI API key is required to fetch models.'))
        return self._fetch_openai_compat_models(
            (self.api_base or 'https://api.openai.com/v1').rstrip('/')
        )

    def _fetch_models_custom(self) -> list:
        """Custom (OpenAI-compatible) providers share the same /models endpoint."""
        self.ensure_one()
        base = (self.api_base or '').rstrip('/')
        if not base:
            raise UserError(_('Base URL is required for custom providers.'))
        return self._fetch_openai_compat_models(base, require_key=False)

    def _fetch_models_ollama(self) -> list:
        """GET /api/tags from Ollama (local); no auth required."""
        self.ensure_one()
        base = (self.api_base or 'http://localhost:11434').rstrip('/')
        url = f'{base}/tags' if base.endswith('/api') else f'{base}/api/tags'
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            result = [
                {'name': item['name'], 'model_use': self._classify_model_use(item['name'])}
                for item in response.json().get('models', [])
                if item.get('name')
            ]
            return sorted(result, key=lambda x: x['name'])
        except requests.RequestException as e:
            _logger.exception('Ollama model fetch error')
            raise UserError(_(
                'Failed to fetch Ollama models. Is Ollama running at %s? Error: %s'
            ) % (base, str(e)))

    def _fetch_models_anthropic(self) -> list:
        """Anthropic does not expose a model list API — raise a helpful error."""
        raise UserError(_(
            'Anthropic does not provide a model list API.\n'
            'Please add models manually using their official IDs from:\n'
            'https://docs.anthropic.com/en/docs/about-claude/models'
        ))

    def _fetch_models_google(self) -> list:
        """GET /models from the Google Gemini API using the ``?key=`` query parameter."""
        self.ensure_one()
        base = (
            self.api_base or 'https://generativelanguage.googleapis.com/v1beta'
        ).rstrip('/')
        if not self.api_key:
            raise UserError(_('Google Gemini API key is required to fetch models.'))
        try:
            response = requests.get(
                f'{base}/models', params={'key': self.api_key}, timeout=15
            )
            response.raise_for_status()
            result = []
            for item in response.json().get('models', []):
                full_name = item.get('name', '')
                short_name = full_name.split('/')[-1] if '/' in full_name else full_name
                if not short_name:
                    continue
                supported = item.get('supportedGenerationMethods', [])
                if 'generateContent' in supported:
                    model_use = 'multimodal' if 'vision' in short_name.lower() else 'chat'
                elif 'embedContent' in supported:
                    model_use = 'embedding'
                else:
                    continue
                result.append({'name': short_name, 'model_use': model_use})
            return sorted(result, key=lambda x: x['name'])
        except requests.RequestException as e:
            _logger.exception('Google Gemini model fetch error')
            raise UserError(_('Failed to fetch Google Gemini models: %s') % str(e))

    # ── Unified chat / embedding interface ────────────────────────────────────

    def chat(self, messages: list, model: str = None, stream: bool = False, **kwargs) -> str:
        """Send a chat completion request through this provider."""
        return self._dispatch('chat', messages, model=model, stream=stream, **kwargs)

    def embedding(self, text: str, model: str = None, **kwargs) -> list:
        """Send a text embedding request through this provider."""
        return self._dispatch('embedding', text, model=model, **kwargs)

    def _dispatch(self, method: str, *args, **kwargs) -> str:
        """
        Route a method call to the service-specific handler, with fallback chain.

        The ``_auto_fallback`` kwarg is an internal flag that prevents fallback
        providers from starting their own nested fallback chains.
        """
        is_auto_fallback = kwargs.pop('_auto_fallback', False)
        handler_name = f'_handle_{self.service}_{method}'
        if not hasattr(self, handler_name):
            raise UserError(_('Service %s does not support %s') % (self.service, method))
        try:
            return getattr(self, handler_name)(*args, **kwargs)
        except Exception as e:
            if is_auto_fallback:
                raise
            _logger.error(
                'AI Provider (%s) Error: %s. Trying fallbacks...', self.name, str(e)
            )
            return self._try_fallbacks(method, e, *args, **kwargs)

    def _try_fallbacks(
        self, method: str, original_error: Exception, *args, **kwargs
    ) -> str:
        """Walk configured and auto-discovered fallback providers until one succeeds."""
        fallback_kwargs = {k: v for k, v in kwargs.items() if k != 'model'}
        fallback_kwargs['_auto_fallback'] = True
        tried_ids = {self.id}

        for fallback in self.fallback_provider_ids:
            tried_ids.add(fallback.id)
            try:
                return fallback._dispatch(method, *args, **fallback_kwargs)
            except Exception as fe:
                _logger.warning('Fallback (%s) failed: %s', fallback.name, str(fe))

        for provider in self.search([('active', '=', True), ('id', 'not in', list(tried_ids))]):
            active_chat = provider.model_ids.filtered(
                lambda m: m.active and m.model_use == 'chat'
            )
            if not active_chat:
                continue
            _logger.info('AI Provider (%s) auto-fallback → %s', self.name, provider.name)
            try:
                return provider._dispatch(method, *args, **fallback_kwargs)
            except Exception as fe:
                _logger.warning('Auto-fallback (%s) failed: %s', provider.name, str(fe))

        raise UserError(
            _('AI Provider and all fallbacks failed: %s') % str(original_error)
        )

    # ── Service handlers ──────────────────────────────────────────────────────

    def _handle_openai_chat(self, messages: list, model: str = None, **kwargs) -> str:
        """Call the OpenAI (or compatible) chat completions endpoint."""
        self.ensure_one()
        base = (self.api_base or 'https://api.openai.com/v1').rstrip('/')
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        data = {
            'model': model or 'gpt-4o',
            'messages': messages,
            'stream': kwargs.get('stream', False),
        }
        try:
            response = requests.post(
                f'{base}/chat/completions', headers=headers, json=data, timeout=30
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except requests.RequestException as e:
            _logger.exception('OpenAI API Error')
            raise UserError(_('OpenAI API Error: %s') % str(e))

    def _handle_custom_chat(self, messages: list, model: str = None, **kwargs) -> str:
        """Custom (OpenAI-compatible) providers reuse the OpenAI handler."""
        return self._handle_openai_chat(messages, model=model, **kwargs)

    def _handle_google_chat(self, messages: list, model: str = None, **kwargs) -> str:
        """Call the Google Gemini generateContent endpoint."""
        self.ensure_one()
        base = (
            self.api_base or 'https://generativelanguage.googleapis.com/v1beta'
        ).rstrip('/')
        model_id = model or 'gemini-2.5-flash'
        contents = [
            {
                'role': 'model' if msg.get('role') in ('assistant', 'model') else 'user',
                'parts': [{'text': msg.get('content', '')}],
            }
            for msg in messages
        ]
        try:
            response = requests.post(
                f'{base}/models/{model_id}:generateContent',
                params={'key': self.api_key},
                json={'contents': contents},
                timeout=(10, 90),
            )
            response.raise_for_status()
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except requests.RequestException as e:
            _logger.exception('Google Gemini API Error')
            raise UserError(_('Google Gemini API Error: %s') % str(e))

    def _handle_anthropic_chat(self, messages: list, model: str = None, **kwargs) -> str:
        """Call the Anthropic Messages API."""
        self.ensure_one()
        base = (self.api_base or 'https://api.anthropic.com/v1').rstrip('/')
        headers = {
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01',
            'Content-Type': 'application/json',
        }
        data = {
            'model': model or 'claude-sonnet-4-6',
            'max_tokens': kwargs.get('max_tokens', 1024),
            'messages': messages,
        }
        try:
            response = requests.post(
                f'{base}/messages', headers=headers, json=data, timeout=30
            )
            response.raise_for_status()
            return response.json()['content'][0]['text']
        except requests.RequestException as e:
            _logger.exception('Anthropic API Error')
            raise UserError(_('Anthropic API Error: %s') % str(e))

    def _handle_ollama_chat(self, messages: list, model: str = None, **kwargs) -> str:
        """Call the Ollama /api/chat endpoint."""
        self.ensure_one()
        base = (self.api_base or 'http://localhost:11434/api').rstrip('/')
        data = {
            'model': model or 'llama3',
            'messages': messages,
            'stream': False,
        }
        if kwargs.get('json_mode'):
            data['format'] = 'json'
        try:
            response = requests.post(f'{base}/chat', json=data, timeout=180)
            response.raise_for_status()
            return response.json()['message']['content']
        except requests.RequestException as e:
            _logger.exception('Ollama API Error')
            raise UserError(_('Ollama API Error: %s') % str(e))
