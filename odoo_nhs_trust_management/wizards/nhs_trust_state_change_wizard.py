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
from odoo.exceptions import ValidationError

class NhsTrustStateChangeWizard(models.TransientModel):
    _name = 'nhs.trust.state.change.wizard'
    _description = 'NHS Trust Workflow State Change Confirmation'

    trust_id = fields.Many2one('nhs.trust', string='NHS Trust Reference', required=True)
    # Selection is inherited from the related field (trust_id.state); redefining
    # it here is ignored by Odoo 19, so we keep only the relation.
    current_state = fields.Selection(related='trust_id.state', string='Current State', readonly=True)
    new_state = fields.Selection([
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('special_measures', 'Special Measures'),
        ('suspended', 'Suspended'),
        ('merging', 'Merging'),
        ('dissolved', 'Dissolved'),
    ], string='Target State', required=True)
    reason = fields.Text(string='Justification Reason / Auditable Narrative', required=True)

    @api.constrains('reason')
    def _check_reason(self):
        for wiz in self:
            if not wiz.reason or len(wiz.reason.strip()) < 5:
                raise ValidationError('A minimum of 5 characters is required for state change justification!')

    @api.constrains('new_state', 'trust_id')
    def _check_state_transition(self):
        allowed_transitions = {
            'draft': ['under_review'],
            'under_review': ['active'],
            'active': ['special_measures', 'suspended', 'merging', 'dissolved'],
            'special_measures': ['active', 'suspended', 'merging', 'dissolved'],
            'suspended': ['active', 'special_measures', 'merging', 'dissolved'],
            'merging': ['dissolved'],
            'dissolved': [],
        }
        for wiz in self:
            if not wiz.current_state or not wiz.new_state or wiz.new_state == wiz.current_state:
                continue
            allowed = allowed_transitions.get(wiz.current_state, [])
            if wiz.trust_id.health_system == 'nhs_scotland':
                allowed = [s for s in allowed if s != 'special_measures']
                if wiz.new_state == 'special_measures':
                    raise ValidationError("NHS Scotland Trusts cannot be placed in Special Measures!")
            if wiz.new_state not in allowed:
                state_labels = {
                    'draft': 'Draft',
                    'under_review': 'Under Review',
                    'active': 'Active',
                    'special_measures': 'Special Measures',
                    'suspended': 'Suspended',
                    'merging': 'Merging',
                    'dissolved': 'Dissolved',
                }
                allowed_str = [state_labels.get(s, s) for s in allowed]
                current_label = state_labels.get(wiz.current_state, wiz.current_state)
                new_label = state_labels.get(wiz.new_state, wiz.new_state)
                raise ValidationError(
                    f"Invalid state transition from '{current_label}' to '{new_label}'! "
                    f"Permitted target states from '{current_label}' are: {', '.join(allowed_str)}."
                )

    def action_confirm(self):
        self.ensure_one()
        if self.new_state == self.current_state:
            raise ValidationError('The new state must be different from the current state!')
        
        # 1. Add immutable audit trail entry
        self.env['nhs.trust.state.log'].create({
            'trust_id': self.trust_id.id,
            'from_state': self.current_state,
            'to_state': self.new_state,
            'reason': self.reason,
            'user_id': self.env.user.id,
            'change_date': fields.Datetime.now(),
        })

        # 2. Update the trust model state bypassing direct block via context
        self.trust_id.with_context(approved_state_change=True).write({
            'state': self.new_state
        })

        return {'type': 'ir.actions.act_window_close'}
