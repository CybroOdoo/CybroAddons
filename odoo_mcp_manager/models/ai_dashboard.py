from odoo import models, fields, api, _


class AiDashboard(models.Model):
    """Singleton dashboard record that surfaces live MCP Gateway status counters."""

    _name = 'ai.dashboard'
    _description = 'MCP Gateway Dashboard'

    name = fields.Char(default='MCP Gateway Dashboard')
    provider_count = fields.Integer(compute='_compute_counts')
    tool_count = fields.Integer(compute='_compute_counts')
    session_count = fields.Integer(compute='_compute_counts')
    mcp_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        default='active',
    )

    def _compute_counts(self) -> None:
        """Populate provider, tool and active-session counters for the dashboard."""
        for rec in self:
            rec.provider_count = self.env['ai.provider'].search_count([])
            rec.tool_count = self.env['ai.tool'].search_count([])
            rec.session_count = self.env['ai.session'].search_count(
                [('state', '=', 'initialized')]
            )

    @api.model
    def action_open_dashboard(self) -> dict:
        """Open (or create) the singleton dashboard record and return its window action."""
        dashboard = self.search([], limit=1)
        if not dashboard:
            dashboard = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': _('MCP Gateway Dashboard'),
            'res_model': 'ai.dashboard',
            'res_id': dashboard.id,
            'view_mode': 'form',
            'target': 'main',
        }
