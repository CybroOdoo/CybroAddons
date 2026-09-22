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
from odoo import _, api,fields, models
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
        """Compute a human-readable name combining the tool and requesting user."""
        for rec in self:
            rec.name = _('Consent for %s (%s)') % (rec.tool_id.name, rec.user_id.name)

    def _check_approver_group(self) -> None:
        """
        Raise an AccessError if the current user is not a Consent Approver.

        This guard is called before every state transition so that only
        authorised users can grant or deny consent requests.
        """
        if not self.env.user.has_group('odoo_mcp_manager.group_mcp_consent_approver'):
            raise AccessError(
                _("Only users in the 'Consent Approver' group can grant or deny consent requests.")
            )

    def action_grant(self) -> None:
        """Grant this consent request, allowing the AI tool to proceed."""
        self._check_approver_group()
        self.write({'state': 'granted'})

    def action_deny(self) -> None:
        """Deny this consent request, blocking the AI tool from executing."""
        self._check_approver_group()
        self.write({'state': 'denied'})
