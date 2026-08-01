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
import inspect
import json
import logging
import time
import traceback as tb_module
from functools import wraps

try:
    from pydantic import create_model
    import pydantic
except ImportError:
    pydantic = None

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# Registry populated by the @ai_tool decorator
AI_TOOL_REGISTRY = {}


def ai_tool(name: str = None, description: str = None, requires_consent: bool = False):
    """
    Decorator that registers a model method as an MCP-callable AI tool.

    Args:
        name: Override the tool name (defaults to the function name).
        description: Human-readable description shown in the MCP tool list.
        requires_consent: When True, a Consent Approver must grant access before execution.
    """
    def decorator(func):
        func_name = name or func.__name__
        AI_TOOL_REGISTRY[func.__qualname__] = {
            'name': func_name,
            'description': description or func.__doc__ or f'Execute {func_name}',
            'func': func,
            'requires_consent': requires_consent,
        }

        @wraps(func)
        def wrapper(*args, **kwargs):
            """Thin passthrough wrapper preserving the original function's metadata."""
            return func(*args, **kwargs)
        return wrapper
    return decorator


class AiTool(models.Model):
    """
    Represents one callable MCP tool — backed by a decorated Odoo method,
    a built-in ORM operation, or an arbitrary Python snippet.
    """

    _name = 'ai.tool'
    _description = 'AI Tool'

    name = fields.Char(required=True, index=True)
    description = fields.Text(required=True)
    implementation = fields.Selection([
        ('decorator', 'Decorated Method (@ai_tool)'),
        ('builtin', 'Built-in Command'),
    ], default='decorator', required=True)
    active = fields.Boolean(default=True)
    requires_user_consent = fields.Boolean(default=False)
    # Users that must give consent before this tool can be executed
    required_consent_user_ids = fields.Many2many(
        'res.users',
        string='Consent Required Users',
        help='Select users whose consent is required to run this tool.'
    )
    decorator_model = fields.Char(string='Model Name')
    decorator_method = fields.Char(string='Method Name')
    default_provider_id = fields.Many2one(
        'ai.provider',
        string='Default AI Provider',
        domain=[('active', '=', True)],
        help='Provider used when no provider is specified in the request.',
    )
    default_model_id = fields.Many2one(
        'ai.model',
        string='Default Model',
        domain="[('provider_id', '=', default_provider_id)]",
        help='Model used when no model is specified in the request.',
    )
    input_schema = fields.Text(
        string='Input Schema (JSON)', help='Auto-generated from type hints'
    )
    tool_definition = fields.Text(
        string='MCP Definition', compute='_compute_tool_definition', store=True
    )

    @api.depends('name', 'description', 'input_schema')
    def _compute_tool_definition(self) -> None:
        """Serialize the MCP tool definition to JSON and store it for fast retrieval."""
        for rec in self:
            rec.tool_definition = json.dumps({
                'name': rec.name.replace('.', '_').replace(' ', '_'),
                'description': rec.description,
                'inputSchema': (
                    json.loads(rec.input_schema)
                    if rec.input_schema
                    else {'type': 'object', 'properties': {}}
                ),
            })

    def sync_tools(self) -> None:
        """Synchronize decorated methods from AI_TOOL_REGISTRY with DB records."""
        existing_tools = self.search([('implementation', '=', 'decorator')])
        tool_map = {(t.decorator_model, t.decorator_method): t for t in existing_tools}
        tools_to_create = []
        for qualname, info in AI_TOOL_REGISTRY.items():
            model_name, method_name = qualname.rsplit('.', 1)
            schema = self._generate_schema(info['func'])
            vals = {
                'name': info['name'],
                'description': info['description'],
                'implementation': 'decorator',
                'decorator_model': model_name,
                'decorator_method': method_name,
                'requires_user_consent': info['requires_consent'],
                'input_schema': json.dumps(schema) if schema else False,
            }
            tool = tool_map.get((model_name, method_name))
            if tool:
                if (
                    tool.name != vals['name']
                    or tool.description != vals['description']
                    or tool.input_schema != vals['input_schema']
                ):
                    tool.write(vals)
            else:
                tools_to_create.append(vals)
        if tools_to_create:
            self.create(tools_to_create)

    def _generate_schema(self, func) -> dict:
        """Generate a JSON Schema dict from function type hints using Pydantic."""
        if not pydantic:
            return None
        sig = inspect.signature(func)
        fields_map = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            annotation = (
                param.annotation if param.annotation != inspect.Parameter.empty else str
            )
            default = (
                param.default if param.default != inspect.Parameter.empty else ...
            )
            fields_map[param_name] = (annotation, default)
        if not fields_map:
            return {'type': 'object', 'properties': {}}
        try:
            dynamic_model = create_model('DynamicToolParams', **fields_map)
            return dynamic_model.model_json_schema()
        except Exception as e:
            _logger.warning('Failed to generate schema for %s: %s', func.__name__, str(e))
            return None

    def execute(self, parameters: dict):
        """Validate and execute the tool, writing a log record regardless of outcome."""
        self.ensure_one()
        _logger.info("Executing AI Tool '%s' | parameters: %s", self.name, parameters)
        effective_uid = self.env.context.get('mcp_user_id', self.env.user.id)
        mcp_source = self.env.context.get('mcp_source', 'mcp')
        client_name = False
        if mcp_source == 'mcp' and effective_uid:
            try:
                session = self.env['ai.session'].sudo().search([
                    ('user_id', '=', effective_uid),
                    ('mcp_source', '=', 'mcp'),
                    ('active', '=', True),
                ], limit=1, order='write_date desc')
                if session and session.client_name:
                    client_name = session.client_name
            except Exception:
                pass

        log_vals = {
            'tool_id': self.id,
            'call_label': self.name,
            'user_id': effective_uid,
            'source': mcp_source,
            'client_name': client_name,
            'input_params': json.dumps(parameters, indent=2, default=str),
            'status': 'success',
        }
        start = time.perf_counter()
        try:
            if self.implementation == 'decorator':
                # Execute the decorated method AS THE AUTHENTICATED USER so the
                # caller's access rights and record rules are enforced (the tool
                # config itself is still read with elevated rights).
                target = self._user_model(self.decorator_model)
                result = getattr(target, self.decorator_method)(**parameters)
            elif self.implementation == 'builtin':
                result = self._execute_builtin(parameters)
            else:
                # 'python' snippet execution was removed for safety; any legacy
                # record with that implementation is rejected here.
                raise UserError(
                    _("Implementation '%s' is not supported.") % self.implementation
                )
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log_vals.update({
                'execution_time_ms': elapsed_ms,
                'result_preview': str(result)[:500] if result is not None else '',
            })
            _logger.info("AI Tool '%s' succeeded in %s ms", self.name, elapsed_ms)
            return result
        except UserError as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            _logger.warning("AI Tool `%s` FAILED in %s ms | error: %s", self.name, elapsed_ms, str(e))
            log_vals.update({
                'status': 'error',
                'execution_time_ms': elapsed_ms,
                'error_message': str(e),
            })
            raise e
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            full_tb = tb_module.format_exc()
            _logger.error(
                "AI Tool '%s' FAILED in %s ms | error: %s\n%s",
                self.name, elapsed_ms, str(e), full_tb,
            )
            log_vals.update({
                'status': 'error',
                'execution_time_ms': elapsed_ms,
                'error_message': str(e),
                'error_traceback': full_tb,
            })
            raise UserError(_('Tool Execution Failed: %s') % str(e))
        finally:
            self._write_execution_log(log_vals, parameters)

    def _write_execution_log(self, log_vals: dict, parameters: dict) -> None:
        """
        Persist the execution log in a separate DB cursor to ensure the record
        is always committed, even if the outer transaction is rolled back due to
        a tool error.

        For AI tools (ask_ai, analyze_records) the provider and model used are
        resolved and appended to the log values before writing.
        """
        if self.name in ('ask_ai', 'analyze_records'):
            try:
                provider, model_used = self._resolve_ai_provider(parameters)
                log_vals['provider_name'] = (
                    provider.name if provider else 'No active provider'
                )
                log_vals['model_used'] = model_used or '(default)'
            except Exception:
                _logger.debug('AiTool: could not resolve provider info for log')
        from odoo import tools
        if tools.config['test_enable']:
            # In test mode, separate cursors cannot see uncommitted records from the test transaction.
            # We use the current environment to avoid ForeignKeyViolation.
            self.env['ai.tool.log'].sudo().create(log_vals)
            return

        try:
            with self.env.registry.cursor() as new_cr:
                api.Environment(new_cr, self.env.uid, {})['ai.tool.log'].sudo().create(log_vals)
        except Exception as create_err:
            _logger.warning(
                'AiTool: log creation failed (%s) — retrying without provider fields', create_err
            )
            minimal = {k: v for k, v in log_vals.items() if k not in ('provider_name', 'model_used')}
            try:
                with self.env.registry.cursor() as new_cr2:
                    api.Environment(new_cr2, self.env.uid, {})['ai.tool.log'].sudo().create(minimal)
            except Exception:
                _logger.exception("AiTool: failed to write execution log for '%s'", self.name)

    def _resolve_ai_provider(self, parameters: dict, model_key: str = 'model') -> tuple:
        """
        Determine the AI provider and model name to use for an AI-powered tool call.

        Resolution order:
          1. Explicit ``provider`` key in *parameters*.
          2. Default provider configured on this tool record (if it has active chat models).
          3. Highest-priority active provider in the system.

        Args:
            parameters: The tool call parameters dict (may contain 'provider' / *model_key*).
            model_key:  The parameter key that holds the requested model name.

        Returns:
            Tuple of (ai.provider record, model_name string).

        Raises:
            UserError: When no active provider with chat models is found.
        """
        param_provider = parameters.get('provider')
        param_model = parameters.get(model_key) or (
            parameters.get('model') if model_key == 'model' else None
        )
        # Provider records hold the (group_system-restricted) API key, so they
        # are always resolved with elevated rights regardless of the caller.
        if param_provider:
            provider = self.env['ai.provider'].sudo().search(
                [('active', '=', True), ('name', 'ilike', param_provider)], limit=1
            )
            if provider:
                return provider, param_model or (
                    self.default_model_id.name if self.default_model_id else None
                )
        default_provider = self.default_provider_id.sudo()
        if default_provider and self._provider_has_active_models(default_provider):
            model_name = (
                param_model
                or (self.default_model_id.name if self.default_model_id else None)
                or self._get_default_model_name(default_provider)
            )
            return default_provider, model_name
        provider, model_name = self._resolve_by_priority(param_model)
        if provider:
            return provider, model_name
        raise UserError(_(
            'No active AI provider with models found. '
            'Configure one under MCP Gateway → Configuration → Providers.'
        ))

    def _provider_has_active_models(self, provider) -> bool:
        """Return True if *provider* has at least one active chat-completion model."""
        return bool(provider.model_ids.filtered(lambda m: m.active and m.model_use == 'chat'))

    def _get_default_model_name(self, provider) -> str:
        """
        Return the name of the default (or first active) chat model for *provider*.

        Prefers models explicitly marked as default; falls back to the first active
        chat model if no default is set.
        """
        active_chat = provider.model_ids.filtered(lambda m: m.active and m.model_use == 'chat')
        default = active_chat.filtered(lambda m: m.default)
        target = default[0] if default else (active_chat[0] if active_chat else None)
        return target.name if target else None

    def _resolve_by_priority(self, param_model: str = None) -> tuple:
        """
        Walk all active providers ordered by priority and return the first one that
        has at least one active chat model.

        Returns:
            Tuple of (provider record, model_name) or (None, None) if none found.
        """
        for provider in self.env['ai.provider'].sudo().search([('active', '=', True)]):
            if self._provider_has_active_models(provider):
                return provider, param_model or self._get_default_model_name(provider)
        return None, None

    def _sanitize_domain(self, domain: list, model) -> list:
        """
        Remove domain leaves that reference fields that do not exist on *model*.

        Invalid leaves are logged as warnings and silently dropped so that
        a partially incorrect domain still returns useful results.
        """
        if not domain:
            return domain
        valid_fields = set(model._fields)
        clean = []
        for leaf in domain:
            if isinstance(leaf, (list, tuple)) and len(leaf) == 3:
                if leaf[0] not in valid_fields:
                    _logger.warning(
                        "search_records: dropping invalid domain leaf %s — "
                        "field '%s' does not exist on model '%s'",
                        leaf, leaf[0], model._name,
                    )
                    continue
            clean.append(leaf)
        return clean

    # Maps each generic built-in tool to the access-control operation it performs.
    _BUILTIN_OPERATION = {
        'search_records': 'read',
        'create_record': 'create',
        'update_record': 'update',
        'delete_record': 'delete',
        'unlink_record': 'unlink',
    }

    def _allowlist_enforced(self) -> bool:
        """Return True unless an administrator has disabled allow-list enforcement."""
        param = self.env['ir.config_parameter'].sudo().get_param(
            'mcp_gateway.enforce_allowlist', 'True'
        )
        return str(param).lower() not in ('false', '0', '')

    def _check_model_access(self, model_name: str, operation: str) -> None:
        """Raise UserError unless *operation* on *model_name* is allow-listed.

        This is the coarse allow-list gate for the generic built-in tools; it is
        layered on top of the per-user ACL/record-rule enforcement (with_user).
        """
        if not self._allowlist_enforced():
            return
        if not self.env['ai.tool.access'].is_allowed(model_name, operation):
            raise UserError(_(
                "AI tools are not allowed to '%(op)s' records of model "
                "'%(model)s'. An administrator can enable it under MCP Gateway "
                "→ Configuration → Tool Access Rules."
            ) % {'op': operation, 'model': model_name})

    def _effective_uid(self) -> int:
        """Return the id of the user the tool acts on behalf of.

        On MCP/bot routes the authenticated user is passed in the context as
        ``mcp_user_id`` (the route env is the Public/superuser one). Elsewhere it
        is simply the current user.
        """
        return self.env.context.get('mcp_user_id') or self.env.uid

    def _user_model(self, model_name: str):
        """Return *model_name* bound to the effective user, enforcing that
        user's access rights and record rules on all ORM operations."""
        return self.env[model_name].with_user(self._effective_uid())

    def _execute_builtin(self, parameters: dict):
        """
        Dispatch execution to the correct built-in handler based on the tool name.

        Built-in tools are implemented directly in Python for common ORM operations
        (search, create, update, delete, unlink) and AI queries (ask_ai, analyze_records).

        Raises:
            UserError: When a required parameter is missing or the model is not found.
        """
        if self.name == 'ask_ai':
            return self._builtin_ask_ai(parameters)
        if self.name == 'analyze_records':
            return self._builtin_analyze_records(parameters)
        model_name = parameters.get('model')
        if not model_name:
            raise UserError(_('Model name is required for built-in tools'))
        if model_name not in self.env:
            raise UserError(_('Model %s not found') % model_name)
        # Coarse allow-list gate (admin-configured) before anything else.
        operation = self._BUILTIN_OPERATION.get(self.name)
        if operation:
            self._check_model_access(model_name, operation)
        # Bind the model to the authenticated user so create/update/delete/search
        # are subject to that user's ACLs and record rules (no more superuser).
        model = self._user_model(model_name)
        dispatch = {
            'search_records': self._builtin_search_records,
            'create_record':  self._builtin_create_record,
            'update_record':  self._builtin_update_record,
            'delete_record':  self._builtin_delete_record,
            'unlink_record':  self._builtin_unlink_record,
        }
        handler = dispatch.get(self.name)
        if handler:
            return handler(model, parameters)
        raise UserError(_('Built-in tool %s not implemented') % self.name)

    def _builtin_ask_ai(self, parameters: dict) -> str:
        """
        Send a free-form prompt to the configured AI provider and return the text reply.

        Requires 'prompt' in parameters.
        """
        prompt = parameters.get('prompt')
        if not prompt:
            raise UserError(_("'prompt' is required for ask_ai"))
        provider, model_name = self._resolve_ai_provider(parameters)
        return provider.chat([{'role': 'user', 'content': prompt}], model=model_name)

    def _builtin_search_records(self, model, parameters: dict) -> list:
        """
        Search *model* using the provided domain and return matching records as dicts.

        Binary fields are excluded from the result to keep payloads small.
        Defaults to a limit of 5 records.
        """
        domain = self._sanitize_domain(parameters.get('domain', []), model)
        safe_fields = [f for f, d in model._fields.items() if d.type != 'binary']
        return model.search(domain, limit=parameters.get('limit', 5)).read(safe_fields)

    def _builtin_create_record(self, model, parameters: dict) -> dict:
        """
        Create a new record in *model* using the 'values' dict from parameters.

        Returns a dict with the new record's id and display_name.
        """
        record = model.create(parameters.get('values', {}))
        return {'id': record.id, 'display_name': record.display_name}

    def _builtin_update_record(self, model, parameters: dict) -> bool:
        """
        Write the 'values' dict onto the record identified by 'res_id'.

        Returns True on success. Raises UserError if the record does not exist.
        """
        res_id = parameters.get('res_id')
        record = model.browse(res_id)
        if not record.exists():
            raise UserError(_('Record %s not found') % res_id)
        record.write(parameters.get('values', {}))
        return True

    def _builtin_delete_record(self, model, parameters: dict) -> dict:
        """
        Permanently delete the record identified by 'res_id' from *model*.

        Requires 'res_id' in parameters. Returns a dict confirming the deletion
        with the original display_name preserved for audit purposes.

        Raises:
            UserError: When 'res_id' is missing or the record does not exist.
        """
        res_id = parameters.get('res_id')
        if not res_id:
            raise UserError(_("'res_id' is required for delete_record"))
        record = model.browse(res_id)
        if not record.exists():
            raise UserError(
                _('Record with ID %s does not exist in model %s') % (res_id, model._name)
            )
        display_name = record.display_name
        record.unlink()
        return {
            'deleted': True,
            'model': model._name,
            'res_id': res_id,
            'display_name': display_name,
            'message': "Record '%s' (ID: %s) has been permanently deleted." % (display_name, res_id),
        }

    def _builtin_unlink_record(self, model, parameters: dict) -> dict:
        """
        Unlink a related record from a relational field without deleting either record.

        Supported field types:
            many2many -- removes the specified 'related_ids' from the relation.
            many2one  -- sets the field to False (clears the link).

        Required parameters: 'res_id', 'field'.
        For many2many: 'related_ids' is also required.

        Raises:
            UserError: When the field type is not supported or parameters are missing.
        """
        res_id = parameters.get('res_id')
        field = parameters.get('field')
        related = parameters.get('related_ids', [])
        record = model.browse(res_id)
        if not record.exists():
            raise UserError(_('Record %s not found in model %s') % (res_id, model._name))
        if field not in model._fields:
            raise UserError(_("Field '%s' does not exist on model %s") % (field, model._name))
        field_def = model._fields[field]
        if field_def.type == 'many2many':
            if not related:
                raise UserError(_("'related_ids' is required to unlink many2many records"))
            record.write({field: [(3, rid, 0) for rid in related]})
            return {'unlinked_ids': related, 'from_record': res_id, 'field': field}
        if field_def.type == 'many2one':
            record.write({field: False})
            return {'field': field, 'record_id': res_id, 'unlinked': True}
        raise UserError(
            _("Field '%s' is of type '%s'. Only many2many and many2one fields support unlinking.")
            % (field, field_def.type)
        )

    def _builtin_analyze_records(self, parameters: dict) -> str:
        """
        Fetch records from an Odoo model and ask the configured AI to analyse them.

        The method reads up to *limit* records from *model*, serialises them to
        JSON, and submits them together with the user's *question* as a prompt to
        the AI provider.  The AI's plain-text answer is returned directly.

        Required parameters:
            question  -- natural-language question about the data
            model     -- Odoo model technical name (e.g. 'sale.order')

        Optional parameters:
            fields    -- list of field names to read (auto-selected if omitted)
            domain    -- Odoo domain to filter records (default: [])
            limit     -- maximum number of records to fetch (default: 20)
            provider  -- AI provider name override
            ai_model  -- AI model name override

        Returns:
            The AI's plain-text response string.

        Raises:
            UserError: When 'question' or 'model' are missing, or the model is not found.
        """
        question = parameters.get('question')
        model_name = parameters.get('model')
        if not question:
            raise UserError(_("'question' is required for analyze_records"))
        if not model_name:
            raise UserError(_("'model' is required for analyze_records"))
        if model_name not in self.env:
            raise UserError(_("Odoo model '%s' not found") % model_name)
        self._check_model_access(model_name, 'read')
        # Read records as the authenticated user so their record rules apply.
        record_obj = self._user_model(model_name)
        fields_to_read = parameters.get('fields', [])
        if not fields_to_read:
            fields_to_read = [
                f for f, d in record_obj._fields.items()
                if d.type != 'binary' and not d.compute
            ]
            if len(fields_to_read) > 15:
                priority = ['id', 'display_name', 'name', 'write_date']
                fields_to_read = priority + [f for f in fields_to_read if f not in priority][:11]
        records = record_obj.search(
            parameters.get('domain', []), limit=parameters.get('limit', 20)
        )
        if not records:
            return 'No records found matching the given domain.'
        data = records.read(fields_to_read)
        prompt = (
            f'You are an assistant analyzing data from the Odoo ERP system.\n'
            f'Model: {model_name} | Records: {len(data)}\n\n'
            f'Data:\n{json.dumps(data, indent=2, default=str)}\n\n'
            f'Question: {question}'
        )
        provider, ai_model_name = self._resolve_ai_provider(parameters, model_key='ai_model')
        return provider.chat([{'role': 'user', 'content': prompt}], model=ai_model_name)

    def get_tool_definition(self) -> dict:
        """
        Return the MCP tool definition dict for this record.

        Uses the precomputed stored JSON if available; otherwise builds the
        structure on the fly from the record's fields.
        """
        self.ensure_one()
        if self.tool_definition:
            return json.loads(self.tool_definition)
        return {
            'name': self.name.replace('.', '_').replace(' ', '_'),
            'description': self.description,
            'inputSchema': {'type': 'object', 'properties': {}},
        }
