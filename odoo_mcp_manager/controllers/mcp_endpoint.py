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
import json
import logging
from odoo import http, api, _
from odoo.exceptions import UserError
from odoo.http import request
from .. import utils
from ..utils.bot_auth import check_rate_limit

_logger = logging.getLogger(__name__)

# Reject JSON-RPC bodies larger than this (bytes) before parsing, to bound memory.
_MAX_BODY_BYTES = 512 * 1024

_CORS_HEADERS = [
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
    ('Access-Control-Allow-Headers',
     'Content-Type, Authorization, X-Odoo-MCP-Source, Mcp-Session-Id'),
    ('Access-Control-Max-Age', '86400'),
]


class MCPController(http.Controller):
    """JSON-RPC endpoint implementing the MCP Streamable HTTP transport."""

    _handlers_cache = {}
    @http.route(
        '/mcp_gateway',
        type='http', auth='public',
        methods=['POST', 'GET', 'OPTIONS'],
        csrf=False,
    )
    def mcp_endpoint(self, **kwargs) -> object:
        """Main MCP JSON-RPC endpoint — supports Streamable HTTP transport."""
        http_method = request.httprequest.method
        if http_method == 'OPTIONS':
            return request.make_response(
                '', headers=[('Content-Type', 'application/json')] + _CORS_HEADERS
            )
        if http_method == 'GET':
            return request.make_response(
                json.dumps({
                    'jsonrpc': '2.0',
                    'error': {'code': -32000, 'message': 'Use POST for MCP requests'},
                    'id': None,
                }),
                headers=[
                    ('Content-Type', 'application/json'),
                    ('Allow', 'POST, OPTIONS'),
                ] + _CORS_HEADERS,
                status=405,
            )

        # Basic abuse protection: per-IP rate limit and body-size cap.
        if not check_rate_limit(request.httprequest.remote_addr):
            return self._make_error_response(-32000, 'Too many requests')
        content_length = request.httprequest.content_length
        raw_body = request.httprequest.data or b''
        if (content_length is not None and content_length > _MAX_BODY_BYTES) \
                or len(raw_body) > _MAX_BODY_BYTES:
            return self._make_error_response(-32600, 'Request body too large')

        try:
            data = json.loads(raw_body)
        except json.JSONDecodeError as e:
            _logger.error('MCP Parse error: %s', str(e))
            return self._make_error_response(-32700, 'Parse error')

        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        _logger.info('MCP Request: %s | method=%s', request.httprequest.url, method)
        user_id = self._authenticate(
            request.httprequest.headers.get('Authorization'),
            request.httprequest.args.get('api_key', ''),
        )
        if not user_id:
            _logger.warning('MCP Unauthorized request for method: %s', method)
            return self._make_error_response(-32001, 'Unauthorized', request_id)

        # Build a proper environment scoped to the authenticated user so that all
        # ORM operations (including relational field reads like message_partner_ids)
        # execute with that user's access rights — not the Public user (id=3).
        user_env = request.env(user=user_id)
        user = user_env['res.users'].browse(user_id)

        handler = self._get_handler(method)
        if not handler:
            _logger.warning('Unrecognized MCP method: %s', method)
            self._log_mcp_call(
                user, method, params,
                status='error', error_message=f'Method {method} not found',
            )
            return self._make_error_response(
                -32601, f'Method {method} not found', request_id
            )

        _logger.info('MCP Dispatching: %s for user %s', method, user.name)
        try:
            result = handler(user, params)
            if request_id is None:
                self._log_mcp_call(user, method, params, status='success')
                return request.make_response(
                    '', headers=[('Content-Type', 'application/json')] + _CORS_HEADERS
                )
            self._log_mcp_call(user, method, params, status='success')
            return self._make_success_response(result, request_id)
        except UserError as e:
            # UserError messages are meant for the caller (validation, consent,
            # not-found, permission) — safe to surface verbatim.
            _logger.info('MCP Handler UserError for %s: %s', method, e)
            self._log_mcp_call(user, method, params, status='error', error_message=str(e))
            return self._make_error_response(-32603, str(e), request_id)
        except Exception as e:
            # Unexpected internal error — log full detail server-side but return a
            # generic message so model/field/stack internals are not leaked.
            _logger.exception('MCP Handler Error for %s', method)
            self._log_mcp_call(user, method, params, status='error', error_message=str(e))
            return self._make_error_response(
                -32603, 'Internal server error', request_id
            )


    def _authenticate(self, auth_header: str, api_key_param: str = '') -> int | None:
        """
        Resolve an Odoo user ID from the request credentials.

        Accepts:
          1. ``Authorization: Bearer <token>`` header (standard MCP / Claude Desktop).
          2. ``?api_key=<token>`` query parameter (Claude.ai remote URLs).

        Returns:
            int user ID on success, None on failure.
        """
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ', 1)[1].strip()
        elif api_key_param:
            token = api_key_param.strip()

        if not token:
            _logger.debug('MCP Auth: no token provided')
            return None
        try:
            user_id = request.env['res.users.apikeys'].sudo()._check_credentials(
                scope='rpc', key=token
            )
            if user_id:
                _logger.debug('MCP Auth: resolved user_id=%s from API key', user_id)
                return user_id
        except Exception as e:
            _logger.error('MCP Auth Error: %s', str(e))
        _logger.warning('MCP Auth: invalid token')
        return None


    def _get_handler(self, method: str) -> object:
        """Look up and cache the handler method for a given MCP method name."""
        if method in self._handlers_cache:
            return self._handlers_cache[method]
        handler = getattr(self, f'_mcp_{method.replace("/", "_")}', None)
        if handler:
            self._handlers_cache[method] = handler
        return handler

    def _mcp_initialize(self, user, params: dict) -> dict:
        """
        Handle the MCP initialize handshake with full client identification.

        Identification strategy (in priority order):
          1. Mcp-Session-Id header  → reconnect, reuse existing session (no new record)
          2. mcp-remote-fallback-test → probe request, skip session creation
          3. (user_id, mcp_source, client_name) triplet → new session per distinct client
        """
        Session = request.env['ai.session'].sudo()
        protocol_version = params.get('protocolVersion') or '2024-11-05'

        # ── 1. Transport channel (X-Odoo-MCP-Source header) ─────────────────
        mcp_source = request.httprequest.headers.get('X-Odoo-MCP-Source', 'mcp')

        # ── 2. Extract & normalize clientInfo from MCP initialize payload ────
        client_info = params.get('clientInfo') or {}
        raw_client_name = (client_info.get('name') or '').strip()
        client_version = (client_info.get('version') or '').strip()
        user_agent = (request.httprequest.headers.get('User-Agent') or '')[:255]

        # Normalize client name to a clean display label
        client_name = self._normalize_client_name(raw_client_name, mcp_source)

        # ── 3. Filter mcp-remote connectivity probes ─────────────────────────
        # mcp-remote fires a 'mcp-remote-fallback-test' probe before connecting the
        # real client. We respond normally (so it passes) but don't create a session.
        if raw_client_name == 'mcp-remote-fallback-test':
            _logger.debug(
                'MCP: connectivity probe from mcp-remote (fallback-test) — no session created'
            )
            return {
                'protocolVersion': protocol_version,
                'capabilities': {'tools': {}, 'resources': {}, 'logging': {}},
                'serverInfo': {'name': 'Odoo MCP Gateway', 'version': '1.0.0'},
            }

        # ── 4. Check Mcp-Session-Id header for reconnects ────────────────────
        # When a client reconnects it sends back the session_id we returned earlier.
        incoming_session_id = request.httprequest.headers.get('Mcp-Session-Id', '')
        if incoming_session_id:
            existing = Session.search([
                ('session_id', '=', incoming_session_id),
                ('user_id', '=', user.id),
                ('active', '=', True),
            ], limit=1)
            if existing:
                existing.write({
                    'protocol_version': protocol_version,
                    'client_version': client_version,
                    'user_agent': user_agent,
                })
                _logger.info(
                    'MCP Session reconnected | user=%s client=%s session_id=%s',
                    user.name, client_name, incoming_session_id,
                )
                return self._build_initialize_response(protocol_version, existing.session_id)

        # ── 5. Look for an existing active session by (user, source, client) ─
        # Migration-safe: only filter by client_name if the column already exists
        # in the database (handles the case where module upgrade hasn't run yet).
        has_client_fields = self._session_has_client_fields(Session)

        base_domain = [
            ('user_id', '=', user.id),
            ('mcp_source', '=', mcp_source),
            ('state', '=', 'initialized'),
            ('active', '=', True),
        ]
        if has_client_fields:
            base_domain.append(('client_name', '=', client_name))

        existing = Session.search(base_domain, limit=1, order='write_date desc')

        if existing:
            write_vals = {'protocol_version': protocol_version}
            if has_client_fields:
                write_vals.update({
                    'client_version': client_version,
                    'user_agent': user_agent,
                })
            existing.write(write_vals)
            _logger.info(
                'MCP Session reused | user=%s source=%s client=%s',
                user.name, mcp_source, client_name,
            )
            return self._build_initialize_response(protocol_version, existing.session_id)

        # ── 6. Create a new session ───────────────────────────────────────────
        create_vals = {
            'user_id': user.id,
            'mcp_source': mcp_source,
            'state': 'initialized',
            'protocol_version': protocol_version,
        }
        if has_client_fields:
            create_vals.update({
                'client_name': client_name,
                'client_version': client_version,
                'user_agent': user_agent,
            })
        new_session = Session.create(create_vals)
        _logger.info(
            'MCP Session created | user=%s source=%s client=%s v%s | session_id=%s',
            user.name, mcp_source, client_name, client_version, new_session.session_id,
        )
        return self._build_initialize_response(protocol_version, new_session.session_id)

    @staticmethod
    def _session_has_client_fields(Session) -> bool:
        """
        Return True if the ai_session table already has the client_name column.

        This guard prevents crashes on servers where the module was updated in
        Python but the database migration (odoo-bin -u) hasn't run yet.
        The check is fast — it queries information_schema once and the result
        is cached implicitly by the DB query planner.
        """
        try:
            Session.env.cr.execute(
                "SELECT 1 FROM information_schema.columns "
                "WHERE table_name = 'ai_session' AND column_name = 'client_name' LIMIT 1"
            )
            return bool(Session.env.cr.fetchone())
        except Exception:
            return False



    @staticmethod
    def _normalize_client_name(raw_name: str, mcp_source: str) -> str:
        """
        Normalize the raw clientInfo.name into a clean display label.

        Examples:
          'antigravity-client (via mcp-remote 0.1.37)' → 'Antigravity'
          'Anthropic/ClaudeAI'                          → 'Claude AI'
          'Odoo Telegram Bot'                            → 'Telegram Bot'
          ''                                             → 'MCP Client'
        """
        if not raw_name:
            return mcp_source.capitalize() + ' Client' if mcp_source != 'mcp' else 'MCP Client'

        name = raw_name

        # Strip mcp-remote wrapper: 'xxx-client (via mcp-remote x.x.x)' → 'xxx'
        import re
        name = re.sub(r'\s*\(via mcp-remote[^)]*\)', '', name, flags=re.IGNORECASE).strip()
        name = re.sub(r'-client$', '', name, flags=re.IGNORECASE).strip()

        # Known name mappings
        _NAME_MAP = {
            'anthropic/claudeai': 'Claude AI',
            'claudeai': 'Claude AI',
            'claude': 'Claude AI',
            'antigravity': 'Antigravity',
            'cursor': 'Cursor',
            'odoo telegram bot': 'Telegram Bot',
            'odoo whatsapp bot': 'WhatsApp Bot',
            'odoo discord bot': 'Discord Bot',
            'odoo web chat': 'Web Chat',
            'odoo bot gateway': 'Bot Gateway',
        }
        mapped = _NAME_MAP.get(name.lower())
        if mapped:
            return mapped

        # Capitalize cleanly
        return name.title() if name else 'MCP Client'

    @staticmethod
    def _build_initialize_response(protocol_version: str, session_id: str) -> dict:
        """Build the standard MCP initialize response, including sessionId."""
        return {
            'protocolVersion': protocol_version,
            'sessionId': session_id,          # returned so client can track reconnects
            'capabilities': {
                'tools': {},
                'resources': {'subscribe': False, 'listChanged': False},
                'resourceTemplates': [{
                    'uriTemplate': 'odoo://{model}',
                    'name': 'Odoo Model Resource',
                    'description': 'Access any Odoo model as a resource',
                    'mimeType': 'application/json',
                }],
                'logging': {},
            },
            'serverInfo': {'name': 'Odoo MCP Gateway', 'version': '1.0.0'},
        }



    def _mcp_notifications_initialized(self, _user, _params) -> None:
        """Acknowledge the notifications/initialized notification (no response body)."""
        return None

    def _mcp_tools_list(self, _user, _params) -> dict:
        """Return the list of all active MCP tool definitions."""
        tools = request.env['ai.tool'].sudo().search([('active', '=', True)])
        return {'tools': [t.get_tool_definition() for t in tools]}

    def _mcp_tools_call(self, user, params: dict) -> dict:
        """Execute the named tool after checking consent requirements."""
        name = params.get('name')
        arguments = params.get('arguments', {})
        tool = request.env['ai.tool'].sudo().search(
            [('name', '=', name), ('active', '=', True)], limit=1
        )
        if not tool:
            raise UserError(_("Tool '%s' not found") % name)
        if tool.requires_user_consent:
            self._check_or_request_consent(tool, user, arguments)

        mcp_source = request.httprequest.headers.get('X-Odoo-MCP-Source', 'mcp')
        # The tool *config* is read with elevated rights (the route runs as the
        # Public user), but the authenticated user is passed via mcp_user_id so
        # that ai.tool.execute() performs the actual data operations AS THAT USER
        # — enforcing their ACLs and record rules (see AiTool._user_model).
        result = tool.sudo().with_context(
            mcp_source=mcp_source,
            mcp_user_id=user.id,
        ).execute(arguments)
        return {
            'content': [{
                'type': 'text',
                'text': utils.dumps(result) if isinstance(result, (dict, list)) else str(result),
            }],
            'isError': False,
        }

    def _check_or_request_consent(self, tool, user, arguments: dict) -> None:
        """
        Enforce the consent gate for tools that require user approval.

        Raises an informative Exception when consent is missing, pending, or denied.
        Resets a previously granted consent back to pending so each execution
        requires a fresh approval.
        """
        consent = request.env['ai.consent'].sudo().search([
            ('tool_id', '=', tool.id),
            ('user_id', '=', user.id),
            ('state', 'in', ['pending', 'granted', 'denied']),
        ], order='create_date desc', limit=1)

        if not consent:
            request.env['ai.consent'].sudo().create({
                'tool_id': tool.id,
                'user_id': user.id,
                'state': 'pending',
                'request_payload': json.dumps(arguments, indent=2, default=str),
            })
            raise UserError(_(
                "Consent required for tool '%s'. "
                'A request has been created in Odoo under MCP Gateway > Operations > '
                'AI Tool Consents. Please ask an approver to grant consent, then retry.'
            ) % tool.name)
        if consent.state == 'pending':
            raise UserError(_(
                "Consent for tool '%s' is still pending approval. "
                'Please ask a Consent Approver to review it in Odoo and retry once granted.'
            ) % tool.name)
        if consent.state == 'denied':
            raise UserError(_(
                "Consent for tool '%s' was denied by the approver. "
                'This action cannot be executed.'
            ) % tool.name)
        consent.sudo().write({
            'state': 'pending',
            'request_payload': json.dumps(arguments, indent=2, default=str),
        })

    def _mcp_resources_list(self, _user, _params) -> dict:
        """Return the list of all active MCP resource definitions."""
        resources = request.env['ai.resource'].sudo().search([('active', '=', True)])
        return {'resources': [r.mcp_definition() for r in resources]}

    def _mcp_resources_read(self, user, params: dict) -> dict:
        """Read records from the Odoo model addressed by the given odoo:// URI."""
        uri = params.get('uri', '')
        if not uri.startswith('odoo://'):
            raise UserError(_('Invalid resource URI'))
        model_name = uri[len('odoo://'):]
        if model_name not in request.env:
            raise UserError(_('Model %s not found') % model_name)

        # Coarse allow-list gate (same rules as the built-in read tool), layered
        # on top of the per-user ACL enforcement below.
        tool_model = request.env['ai.tool'].sudo()
        if tool_model._allowlist_enforced() and not \
                request.env['ai.tool.access'].is_allowed(model_name, 'read'):
            raise UserError(_(
                "Reading model '%s' via MCP resources is not allowed. An "
                "administrator can enable it under MCP Gateway → Configuration "
                "→ Tool Access Rules."
            ) % model_name)
        model_obj = request.env[model_name].with_user(user)
        fields_to_read = params.get('fields')
        if not fields_to_read:
            fields_to_read = [
                f for f, d in model_obj._fields.items()
                if d.type != 'binary' and not d.compute
            ]
            if len(fields_to_read) > 15:
                priority = ['display_name', 'id', 'write_date']
                fields_to_read = (
                    priority + [f for f in fields_to_read if f not in priority][:12]
                )

        data = model_obj.search([], limit=params.get('limit', 20)).read(fields_to_read)
        return {
            'contents': [{'uri': uri, 'mimeType': 'application/json', 'text': utils.dumps(data)}]
        }

    def _mcp_resources_templates_list(self, _user, _params) -> dict:
        """Return the static resource template descriptor."""
        return {'resourceTemplates': [{
            'uriTemplate': 'odoo://{model}',
            'name': 'Odoo Model Resource',
            'description': 'Access any Odoo model by its technical name',
            'mimeType': 'application/json',
        }]}

    def _mcp_ping(self, _user, _params) -> dict:
        """Respond to MCP ping with an empty result."""
        return {}

    @http.route('/mcp_gateway/health', type='http', auth='none', methods=['GET'], csrf=False)
    def mcp_health(self) -> object:
        """Public health-check endpoint — returns JSON 200 with server status."""
        return request.make_response(
            json.dumps({'status': 'healthy', 'server': 'Odoo MCP Gateway'}),
            headers=[('Content-Type', 'application/json')] + _CORS_HEADERS,
        )

    def _log_mcp_call(
        self,
        user,
        method: str,
        params: dict,
        status: str = 'success',
        error_message: str = None,
    ) -> None:
        """Write an MCP call log record in a separate cursor (always committed)."""
        if method == 'tools/call' and status == 'success':
            return  # already logged by ai.tool.execute

        mcp_source = request.httprequest.headers.get('X-Odoo-MCP-Source', 'mcp')
        label = params.get('name', method) if method == 'tools/call' else method
        user_id = user.id if user else request.env.user.id

        client_name = False
        if mcp_source == 'mcp' and user_id:
            try:
                Session = request.env['ai.session'].sudo()
                if self._session_has_client_fields(Session):
                    session = Session.search([
                        ('user_id', '=', user_id),
                        ('mcp_source', '=', 'mcp'),
                        ('active', '=', True),
                    ], limit=1, order='write_date desc')
                    if session and session.client_name:
                        client_name = session.client_name
            except Exception:
                pass

        log_vals = {
            'source': mcp_source,
            'client_name': client_name,
            'call_label': label[:50],
            'user_id': user_id,
            'input_params': json.dumps(
                {'method': method, 'params': params}, default=str
            )[:3000],
            'status': status,
        }
        if error_message:
            log_vals['error_message'] = str(error_message)
        try:
            with request.env.registry.cursor() as new_cr:
                api.Environment(new_cr, request.env.uid, {})['ai.tool.log'].sudo().create(
                    log_vals
                )
        except Exception:
            _logger.exception('MCP: failed to write log for %s', method)

    def _make_success_response(self, result, request_id) -> object:
        """Wrap *result* in a JSON-RPC 2.0 success response."""
        return request.make_response(
            json.dumps({'jsonrpc': '2.0', 'result': result, 'id': request_id}),
            headers=[('Content-Type', 'application/json')] + _CORS_HEADERS,
        )

    def _make_error_response(
        self, code: int, message: str, request_id=None
    ) -> object:
        """Wrap *message* in a JSON-RPC 2.0 error response."""
        return request.make_response(
            json.dumps({
                'jsonrpc': '2.0',
                'error': {'code': code, 'message': message},
                'id': request_id,
            }),
            headers=[('Content-Type', 'application/json')] + _CORS_HEADERS,
        )
