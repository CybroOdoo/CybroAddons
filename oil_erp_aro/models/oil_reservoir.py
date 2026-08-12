# -*- coding: utf-8 -*-
#############################################################################
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

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class OilReservoir(models.Model):
    """Extend oil.reservoir to surface ARO summary at the well/reservoir level."""
    _inherit = 'oil.reservoir'

    aro_required = fields.Boolean( string='ARO Required', default=True,
                                   help='Uncheck only for wells exempt from retirement obligations.')
    aro_obligation_ids = fields.One2many('oil.aro.obligation', 'reservoir_id',
                                         string='ARO Obligations', help="Link this transaction or record to the corresponding 'aro obligations' reference.")
    aro_count = fields.Integer( compute='_compute_aro_count', string='ARO Count', help="Specify the numerical measurement, volume, or financial amount for 'aro count'.")
    aro_current_liability = fields.Monetary( string='ARO Liability', compute='_compute_aro_summary',
                                             currency_field='company_currency_id', help="Specify the numerical measurement, volume, or financial amount for 'aro liability'.")
    company_currency_id = fields.Many2one( 'res.currency', related='company_id.currency_id',
                                           string='Company Currency', readonly=True, help="Link this transaction or record to the corresponding 'company currency' reference.")
    estimated_decom_cost_fv = fields.Monetary( string='Estimated Decom Cost (FV)', currency_field='company_currency_id',
                                               help='Nominal future-value abandonment cost estimate.')
    estimated_abandonment_date = fields.Date( string='Estimated Abandonment Date', help="The date when this transaction, measurement, or event was officially recorded.")

    @api.depends('aro_obligation_ids')
    def _compute_aro_count(self):
        """Calculates and updates the 'count' value automatically based on related operational inputs."""
        for rec in self:
            rec.aro_count = len(rec.aro_obligation_ids)

    @api.depends('aro_obligation_ids.current_liability_balance')
    def _compute_aro_summary(self):
        """Calculates and updates the 'summary' value automatically based on related operational inputs."""
        for rec in self:
            rec.aro_current_liability = sum(
                rec.aro_obligation_ids.mapped('current_liability_balance'))

    def action_view_aro(self):
        """Triggers the transition of the record to proceed with the 'view aro' step in the workflow."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('ARO Obligations'),
            'res_model': 'oil.aro.obligation',
            'view_mode': 'list,form',
            'domain': [('reservoir_id', '=', self.id)],
            'context': {
                'default_reservoir_id': self.id,
                'default_asset_kind': 'reservoir',
            },
        }

    def bulk_schedule_execute(self, template, line=None):
        """Target 1 (create) — recognise an ARO obligation from a reservoir."""
        if template.target_model_name == 'oil.aro.obligation':
            return self._bulk_create_aro_obligation(template)
        return super().bulk_schedule_execute(template, line)

    def _bulk_create_aro_obligation(self, template):
        """Executes the 'bulk create aro obligation' process within the operational workflow."""
        self.ensure_one()
        config = template.aro_template_id
        if not config:
            raise UserError(_(
                'Set an ARO Configuration Template on the bulk schedule '
                'template before creating obligations.',
            ))
        if not self.estimated_abandonment_date:
            raise UserError(_(
                'Reservoir %s has no Estimated Abandonment Date — cannot '
                'recognise an obligation.',
            ) % self.display_name)
        return self.env['oil.aro.obligation'].create({
            'asset_kind': 'reservoir',
            'reservoir_id': self.id,
            'description': _('Bulk ARO — %s') % self.display_name,
            'future_cost': self.estimated_decom_cost_fv or 0.0,
            'abandonment_date': self.estimated_abandonment_date,
            'recognition_date': fields.Date.context_today(self),
            'discount_rate': config.discount_rate,
            'accretion_frequency': config.accretion_frequency,
            'template_id': config.id,
            'aro_asset_account_id': config.aro_asset_account_id.id,
            'liability_account_id': config.liability_account_id.id,
            'accretion_expense_account_id':
                config.accretion_expense_account_id.id,
            'wip_account_id': config.wip_account_id.id,
            'settlement_gain_account_id':
                config.settlement_gain_account_id.id or False,
            'settlement_loss_account_id':
                config.settlement_loss_account_id.id or False,
            'journal_id': config.journal_id.id,
            'company_id': self.company_id.id,
        })

