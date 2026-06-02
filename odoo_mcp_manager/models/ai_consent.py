# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError


class AiConsent(models.Model):
    """Consent request raised when a tool marked require_user_consent is invoked."""

    _name = 'ai.consent'
    _description = 'AI Tool Consent'
    _order = 'create_date desc'

    name = fields.Char(compute='_compute_name', store=True)
    tool_id = fields.Many2one(
        'ai.tool', string='Tool', required=True, ondelete='cascade'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user,
    )
    state = fields.Selection([
        ('pending', 'Pending'),
        ('granted', 'Granted'),
        ('denied', 'Denied'),
    ], default='pending', required=True)
    request_payload = fields.Text(string='Request Details (JSON)')
    response_metadata = fields.Text(string='Response Metadata')

    @api.depends('tool_id', 'user_id')
    def _compute_name(self) -> None:
        for rec in self:
            rec.name = _('Consent for %s (%s)') % (rec.tool_id.name, rec.user_id.name)

    def _check_approver_group(self) -> None:
        if not self.env.user.has_group('odoo_mcp_manager.group_mcp_consent_approver'):
            raise AccessError(
                _("Only users in the 'Consent Approver' group can grant or deny consent requests.")
            )

    def action_grant(self) -> None:
        self._check_approver_group()
        self.write({'state': 'granted'})

    def action_deny(self) -> None:
        self._check_approver_group()
        self.write({'state': 'denied'})
