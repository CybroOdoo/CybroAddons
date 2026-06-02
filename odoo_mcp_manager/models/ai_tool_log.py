# -*- coding: utf-8 -*-
from odoo import models, fields


class AiToolLog(models.Model):
    """Immutable execution log record written after every tool invocation."""

    _name = 'ai.tool.log'
    _description = 'AI Tool Execution Log'
    _order = 'timestamp desc'

    tool_id = fields.Many2one('ai.tool', string='Tool', ondelete='cascade')
    user_id = fields.Many2one('res.users', string='Executed By')
    timestamp = fields.Datetime(default=fields.Datetime.now, string='Execution Time')
    execution_time_ms = fields.Float(string='Duration (ms)')
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error'),
    ], string='Status')
    input_params = fields.Text(string='Input Parameters')
    result_preview = fields.Text(
        string='Result Preview',
        help='First 500 characters of the successful response.',
    )
    provider_name = fields.Char(string='Provider Used')
    model_used = fields.Char(string='Model Used')
    source = fields.Selection([
        ('mcp', 'MCP Gateway'),
        ('rpc', 'Direct RPC'),
        ('bot', 'Bot'),
    ], string='Source', default='mcp')
    call_label = fields.Char(string='Action')
    error_message = fields.Text(string='Error Message')
    error_traceback = fields.Text(
        string='Full Traceback',
        help='Complete Python traceback for debugging.',
    )

    def name_get(self) -> list:
        return [(rec.id, f'{rec.tool_id.name} - {rec.timestamp}') for rec in self]
