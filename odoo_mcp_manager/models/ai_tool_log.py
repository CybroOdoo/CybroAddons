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
from odoo import api, fields, models


class AiToolLog(models.Model):
    """Immutable execution log record written after every tool invocation."""

    _name = 'ai.tool.log'
    _description = 'AI Tool Execution Log'
    _order = 'timestamp desc'

    display_name = fields.Char(compute='_compute_display_name')
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
    client_name = fields.Char(string='Client Name')
    source = fields.Selection([
        ('mcp', 'MCP Client'),
        ('rpc', 'Direct RPC'),
        ('bot', 'Bot (Generic)'),
        ('telegram', 'Telegram Bot'),
        ('whatsapp', 'WhatsApp Bot'),
        ('discord', 'Discord Bot'),
        ('web', 'Web Chat'),
    ], string='Source', default='mcp')
    call_label = fields.Char(string='Action')
    error_message = fields.Text(string='Error Message')
    error_traceback = fields.Text(
        string='Full Traceback',
        help='Complete Python traceback for debugging.',
    )

    @api.depends('tool_id.name', 'timestamp')
    def _compute_display_name(self) -> None:
        """Display name combining tool name and execution timestamp (Odoo 19)."""
        for rec in self:
            rec.display_name = f'{rec.tool_id.name} - {rec.timestamp}'
