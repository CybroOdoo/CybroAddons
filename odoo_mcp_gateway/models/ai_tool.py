# -*- coding: utf-8 -*-
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

from odoo import models, fields, api, _
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
        ('python', 'Python Snippet (High Risk)'),
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
        """Synchronise decorated methods from AI_TOOL_REGISTRY with DB records."""
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
        log_vals = {
            'tool_id': self.id,
            'call_label': self.name,
            'user_id': self.env.user.id,
            'source': self.env.context.get('mcp_source', 'mcp'),
            'input_params': json.dumps(parameters, indent=2, default=str),
            'status': 'success',
        }
        start = time.perf_counter()
        try:
            if self.implementation == 'decorator':
                result = getattr(
                    self.env[self.decorator_model], self.decorator_method
                )(**parameters)
            elif self.implementation == 'builtin':
                result = self._execute_builtin(parameters)
            else:
                raise UserError(
                    _('Implementation %s not yet supported') % self.implementation
                )
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
            log_vals.update({
                'execution_time_ms': elapsed_ms,
                'result_preview': str(result)[:500] if result is not None else '',
            })
            _logger.info("AI Tool '%s' succeeded in %s ms", self.name, elapsed_ms)
            return result
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
        if self.name in ('ask_ai', 'analyze_records'):
            try:
                provider, model_used = self._resolve_ai_provider(parameters)
                log_vals['provider_name'] = (
                    provider.name if provider else 'No active provider'
                )
                log_vals['model_used'] = model_used or '(default)'
            except Exception:
                _logger.debug('AiTool: could not resolve provider info for log')
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
        param_provider = parameters.get('provider')
        param_model = parameters.get(model_key) or parameters.get('model')
        if param_provider:
            provider = self.env['ai.provider'].search(
                [('active', '=', True), ('name', 'ilike', param_provider)], limit=1
            )
            if provider:
                return provider, param_model or (
                    self.default_model_id.name if self.default_model_id else None
                )
        if self.default_provider_id and self._provider_has_active_models(self.default_provider_id):
            model_name = (
                param_model
                or (self.default_model_id.name if self.default_model_id else None)
                or self._get_default_model_name(self.default_provider_id)
            )
            return self.default_provider_id, model_name
        provider, model_name = self._resolve_by_priority(param_model)
        if provider:
            return provider, model_name
        raise UserError(_(
            'No active AI provider with models found. '
            'Configure one under MCP Gateway → Configuration → Providers.'
        ))

    def _provider_has_active_models(self, provider) -> bool:
        return bool(provider.model_ids.filtered(lambda m: m.active and m.model_use == 'chat'))

    def _get_default_model_name(self, provider) -> str:
        active_chat = provider.model_ids.filtered(lambda m: m.active and m.model_use == 'chat')
        default = active_chat.filtered(lambda m: m.default)
        target = default[0] if default else (active_chat[0] if active_chat else None)
        return target.name if target else None

    def _resolve_by_priority(self, param_model: str = None) -> tuple:
        for provider in self.env['ai.provider'].search([('active', '=', True)]):
            if self._provider_has_active_models(provider):
                return provider, param_model or self._get_default_model_name(provider)
        return None, None

    def _sanitize_domain(self, domain: list, model) -> list:
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

    def _execute_builtin(self, parameters: dict):
        if self.name == 'ask_ai':
            return self._builtin_ask_ai(parameters)
        if self.name == 'analyze_records':
            return self._builtin_analyze_records(parameters)
        model_name = parameters.get('model')
        if not model_name:
            raise UserError(_('Model name is required for built-in tools'))
        if model_name not in self.env:
            raise UserError(_('Model %s not found') % model_name)
        model = self.env[model_name]
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
        prompt = parameters.get('prompt')
        if not prompt:
            raise UserError(_("'prompt' is required for ask_ai"))
        provider, model_name = self._resolve_ai_provider(parameters)
        return provider.chat([{'role': 'user', 'content': prompt}], model=model_name)

    def _builtin_search_records(self, model, parameters: dict) -> list:
        domain = self._sanitize_domain(parameters.get('domain', []), model)
        safe_fields = [f for f, d in model._fields.items() if d.type != 'binary']
        return model.search(domain, limit=parameters.get('limit', 5)).read(safe_fields)

    def _builtin_create_record(self, model, parameters: dict) -> dict:
        record = model.create(parameters.get('values', {}))
        return {'id': record.id, 'display_name': record.display_name}

    def _builtin_update_record(self, model, parameters: dict) -> bool:
        res_id = parameters.get('res_id')
        record = model.browse(res_id)
        if not record.exists():
            raise UserError(_('Record %s not found') % res_id)
        record.write(parameters.get('values', {}))
        return True

    def _builtin_delete_record(self, model, parameters: dict) -> dict:
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
        question = parameters.get('question')
        model_name = parameters.get('model')
        if not question:
            raise UserError(_("'question' is required for analyze_records"))
        if not model_name:
            raise UserError(_("'model' is required for analyze_records"))
        if model_name not in self.env:
            raise UserError(_("Odoo model '%s' not found") % model_name)
        record_obj = self.env[model_name]
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
        self.ensure_one()
        if self.tool_definition:
            return json.loads(self.tool_definition)
        return {
            'name': self.name.replace('.', '_').replace(' ', '_'),
            'description': self.description,
            'inputSchema': {'type': 'object', 'properties': {}},
        }
