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
# ############################################################################

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

class OilAroRevisionWizard(models.TransientModel):
    """Wizard to revise the ARO estimate (future cost, discount rate, or abandonment date)."""
    _name = 'oil.aro.revision.wizard'
    _description = 'ARO Revision of Estimate Wizard'

    obligation_id = fields.Many2one(
        'oil.aro.obligation', string='ARO Obligation', required=True, help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    reason = fields.Selection([('cost_escalation', 'Cost Escalation'),
                               ('regulatory_change', 'Regulatory Change'), ('scope_change', 'Scope Change'),
                               ('engineering_studies', 'Post-Studies Refinement'),
                               ('rate_change', 'Discount Rate Change'), ('timing_change', 'Abandonment Timing Change'),
                               ('other', 'Other'), ], string='Reason', required=True, help="Select the appropriate classification or category for 'reason'.")
    description = fields.Text(string='Explanation', required=True, help="Additional comments, details, or operational remarks about this record.")

    new_future_cost = fields.Monetary(string='New Future Cost', currency_field='currency_id', help="The unit rate or total financial cost applied to this transaction.")
    new_discount_rate = fields.Float(string='New Discount Rate (%)', digits=(6, 4), help="Specify the numerical measurement, volume, or financial amount for 'new discount rate (%)'.")
    new_abandonment_date = fields.Date(string='New Abandonment Date', help="The date when this transaction, measurement, or event was officially recorded.")

    # Read-only previews
    old_future_cost = fields.Monetary(string='Current Future Cost', currency_field='currency_id',
                                      compute='_compute_olds', help="The unit rate or total financial cost applied to this transaction.")
    old_discount_rate = fields.Float(string='Current Rate (%)', digits=(6, 4), compute='_compute_olds', help="Specify the numerical measurement, volume, or financial amount for 'current rate (%)'.")
    old_abandonment_date = fields.Date(string='Current Abandonment Date', compute='_compute_olds', help="The date when this transaction, measurement, or event was officially recorded.")
    old_liability = fields.Monetary(string='Current Liability', currency_field='currency_id', compute='_compute_olds', help="Specify the numerical measurement, volume, or financial amount for 'current liability'.")
    new_liability_preview = fields.Monetary(string='New Liability (PV)', currency_field='currency_id',
                                            compute='_compute_new_liability', help="Specify the numerical measurement, volume, or financial amount for 'new liability (pv)'.")
    delta_preview = fields.Monetary(string='Adjustment (+ve = increase)', currency_field='currency_id',
                                    compute='_compute_new_liability', help="Specify the numerical measurement, volume, or financial amount for 'adjustment (+ve = increase)'.")
    currency_id = fields.Many2one(related='obligation_id.currency_id', readonly=True, help="Link this transaction or record to the corresponding 'currency id' reference.")

    @api.depends('obligation_id')
    def _compute_olds(self):
        """Calculates and updates the '' value automatically based on related operational inputs."""
        for rec in self:
            ob = rec.obligation_id
            rec.old_future_cost = ob.future_cost
            rec.old_discount_rate = ob.discount_rate
            rec.old_abandonment_date = ob.abandonment_date
            rec.old_liability = ob.current_liability_balance

    @api.depends('new_future_cost', 'new_discount_rate',
                 'new_abandonment_date', 'obligation_id')
    def _compute_new_liability(self):
        """Calculates and updates the 'liability' value automatically based on related operational inputs."""
        for rec in self:
            ob = rec.obligation_id
            fv = rec.new_future_cost if rec.new_future_cost is not None else ob.future_cost
            r = (rec.new_discount_rate if rec.new_discount_rate is not None else ob.discount_rate) / 100.0
            ab_date = rec.new_abandonment_date or ob.abandonment_date
            ref_date = fields.Date.context_today(rec)
            if ab_date and ab_date > ref_date and r > 0:
                n = (ab_date - ref_date).days / 365.25
                pv = fv / ((1 + r) ** n)
                rec.new_liability_preview = pv
                rec.delta_preview = pv - ob.current_liability_balance
            else:
                rec.new_liability_preview = ob.current_liability_balance
                rec.delta_preview = 0.0

    def action_apply_revision(self):
        """Triggers the transition of the record to proceed with the 'apply revision' step in the workflow."""
        self.ensure_one()
        ob = self.obligation_id
        old_liab = ob.current_liability_balance
        new_liab = self.new_liability_preview
        delta = self.delta_preview

        # Validate accounts
        if not ob.aro_asset_account_id:
            raise UserError(_('ARO Asset Account not configured on the obligation.'))
        if not ob.liability_account_id:
            raise UserError(_('ARO Liability Account not configured.'))

        move = None
        if abs(delta) > 0.01:  # only post journal if material
            lines = []
            if delta > 0:
                # Increase liability: Dr ARO Asset / Cr ARO Liability
                lines = [
                    (0, 0, {
                        'name': _('ARO Revision — Asset increase'),
                        'account_id': ob.aro_asset_account_id.id,
                        'debit': delta,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': _('ARO Revision — Liability increase'),
                        'account_id': ob.liability_account_id.id,
                        'debit': 0.0,
                        'credit': delta,
                    }),
                ]
            else:
                abs_delta = abs(delta)
                lines = [
                    (0, 0, {
                        'name': _('ARO Revision — Liability decrease'),
                        'account_id': ob.liability_account_id.id,
                        'debit': abs_delta,
                        'credit': 0.0,
                    }),
                    (0, 0, {
                        'name': _('ARO Revision — Asset decrease'),
                        'account_id': ob.aro_asset_account_id.id,
                        'debit': 0.0,
                        'credit': abs_delta,
                    }),
                ]

            move = self.env['account.move'].create({
                'journal_id': ob.journal_id.id,
                'date': fields.Date.context_today(self),
                'ref': _('ARO Revision: %s') % ob.name,
                'move_type': 'entry',
                'line_ids': lines,
            })
            move.action_post()

        # Always create a revision record (even if delta = 0)
        revision_vals = {
            'obligation_id': ob.id,
            'revision_date': fields.Date.context_today(self),
            'reason': self.reason,
            'old_future_cost': ob.future_cost,
            'new_future_cost': self.new_future_cost or ob.future_cost,
            'old_discount_rate': ob.discount_rate,
            'new_discount_rate': self.new_discount_rate or ob.discount_rate,
            'old_abandonment_date': ob.abandonment_date,
            'new_abandonment_date': self.new_abandonment_date or ob.abandonment_date,
            'old_liability': old_liab,
            'new_liability': new_liab,
            'delta': delta,
            'move_id': move.id if move else False,
            'description': self.description,
        }
        self.env['oil.aro.revision'].create(revision_vals)

        # Update obligation fields
        update_vals = {'current_liability_balance': new_liab}
        if self.new_future_cost is not None:
            update_vals['future_cost'] = self.new_future_cost
        if self.new_discount_rate is not None:
            update_vals['discount_rate'] = self.new_discount_rate
        if self.new_abandonment_date:
            update_vals['abandonment_date'] = self.new_abandonment_date
        ob.write(update_vals)

        ob.message_post(body=_(
            'ARO revised. Reason: %(r)s. Adjustment: %(adj)s.',
            r=dict(self._fields['reason'].selection).get(self.reason, self.reason),
            adj=delta))

        # Close wizard and refresh form
        return {'type': 'ir.actions.act_window_close'}
