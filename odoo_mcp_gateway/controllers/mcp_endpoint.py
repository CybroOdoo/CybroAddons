import json
import logging
from odoo import http, api
from odoo.http import request
from .. import utils

_logger = logging.getLogger(__name__)

_CORS_HEADERS = [
    ('Access-Control-Allow-Origin', '*'),
    ('Access-Control-Allow-Methods', 'POST, GET, OPTIONS'),
    ('Access-Control-Allow-Headers',
     'Content-Type, Authorization, X-Odoo-MCP-Source, mcp-session-id'),
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
        try:
            data = json.loads(request.httprequest.data)
        except json.JSONDecodeError as e:
            _logger.error('MCP Parse error: %s', str(e))
            return self._make_error_response(-32700, 'Parse error')

        method = data.get('method')
        params = data.get('params', {})
        request_id = data.get('id')
        _logger.info('MCP Request: %s | method=%s', request.httprequest.url, method)
        user = self._authenticate(
            request.httprequest.headers.get('Authorization'),
            request.httprequest.args.get('api_key', ''),
        )
        if not user:
            _logger.warning('MCP Unauthorized request for method: %s', method)
            return self._make_error_response(-32001, 'Unauthorized', request_id)

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
        except Exception as e:
            _logger.exception('MCP Handler Error for %s', method)
            self._log_mcp_call(user, method, params, status='error', error_message=str(e))
            return self._make_error_response(-32603, str(e), request_id)


    def _authenticate(self, auth_header: str, api_key_param: str = '') -> object:
        """
        Resolve an Odoo user from the request credentials.

        Accepts:
          1. ``Authorization: Bearer <token>`` header (standard MCP / Claude Desktop).
          2. ``?api_key=<token>`` query parameter (Claude.ai remote URLs).

        Returns:
            res.users record on success, None on failure.
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
                return request.env['res.users'].sudo().browse(user_id)
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
        """Handle the MCP initialize handshake, reusing or creating a session record."""
        Session = request.env['ai.session'].sudo()
        protocol_version = params.get('protocolVersion') or '2024-11-05'

        existing = Session.search([
            ('user_id', '=', user.id),
            ('state', '=', 'initialized'),
            ('active', '=', True),
        ], limit=1, order='write_date desc')
        if existing:
            existing.write({'protocol_version': protocol_version})
            _logger.info('MCP Session reused for user: %s', user.name)
        else:
            Session.create({
                'user_id': user.id,
                'state': 'initialized',
                'protocol_version': protocol_version,
            })
            _logger.info('MCP Session initialized for user: %s', user.name)
        return {
            'protocolVersion': '2024-11-05',
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
            raise Exception(f"Tool '{name}' not found")
        if tool.requires_user_consent:
            self._check_or_request_consent(tool, user, arguments)

        mcp_source = request.httprequest.headers.get('X-Odoo-MCP-Source', 'mcp')
        result = tool.with_user(user).with_context(mcp_source=mcp_source).execute(arguments)
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
            raise Exception(
                f"Consent required for tool '{tool.name}'. "
                'A request has been created in Odoo under MCP Gateway > Operations > '
                'AI Tool Consents. Please ask an approver to grant consent, then retry.'
            )
        if consent.state == 'pending':
            raise Exception(
                f"Consent for tool '{tool.name}' is still pending approval. "
                'Please ask a Consent Approver to review it in Odoo and retry once granted.'
            )
        if consent.state == 'denied':
            raise Exception(
                f"Consent for tool '{tool.name}' was denied by the approver. "
                'This action cannot be executed.'
            )
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
            raise Exception('Invalid resource URI')
        model_name = uri[len('odoo://'):]
        if model_name not in request.env:
            raise Exception(f'Model {model_name} not found')

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
        log_vals = {
            'source': mcp_source,
            'call_label': label[:50],
            'user_id': user.id if user else request.env.user.id,
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
