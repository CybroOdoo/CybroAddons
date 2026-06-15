# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models, fields, api
from odoo.exceptions import UserError

class NhsTrustStateLog(models.Model):
    _name = 'nhs.trust.state.log'
    _description = 'NHS Trust Workflow State Change Log'
    _order = 'change_date desc'
    _rec_name = 'display_name'

    trust_id = fields.Many2one('nhs.trust', string='Trust Reference',
                               required=True, ondelete='cascade', index=True)
    from_state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('special_measures', 'Special Measures'),
        ('suspended', 'Suspended'),
        ('merging', 'Merging'),
        ('dissolved', 'Dissolved'),
    ], string='From State')
    to_state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('special_measures', 'Special Measures'),
        ('suspended', 'Suspended'),
        ('merging', 'Merging'),
        ('dissolved', 'Dissolved'),
    ], string='To State', required=True)
    reason = fields.Text(string='Justification Reason', required=True)
    user_id = fields.Many2one('res.users', string='Changed By', required=True,
                              default=lambda self: self.env.user, index=True)
    change_date = fields.Datetime(string='Change Date & Time', required=True, default=fields.Datetime.now, index=True)
    display_name = fields.Char(string='Description', compute='_compute_display_name')

    @api.depends('trust_id', 'to_state', 'change_date')
    def _compute_display_name(self):
        for log in self:
            trust_name = log.trust_id.name or 'Unknown Trust'
            state_label = dict(self._fields['to_state'].selection).get(log.to_state, log.to_state)
            log.display_name = f"{trust_name} → {state_label}"

    def write(self, vals):
        raise UserError('Workflow change logs are immutable audit records and '
                        'cannot be modified under any circumstances!')

    def unlink(self):
        if not self.env.user.has_group('base.group_system'):
            raise UserError('Only System Administrators have permissions to delete workflow change audit records!')
        return super(NhsTrustStateLog, self).unlink()
