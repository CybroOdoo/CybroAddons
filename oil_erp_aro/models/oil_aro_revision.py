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

from odoo import fields, models

class OilAroRevision(models.Model):
    """Audit log of each estimate revision (IAS 37 remeasurement)."""
    _name = 'oil.aro.revision'
    _description = 'ARO Revision of Estimate'
    _order = 'revision_date desc, id desc'
    _rec_name = 'display_name'  # optional, for better representation

    display_name = fields.Char(compute='_compute_display_name', store=False, help="A unique name or reference identifier used to track this record in the system.")

    obligation_id = fields.Many2one('oil.aro.obligation', string='ARO Obligation', required=True,
                                    ondelete='cascade', index=True, help="Link this transaction or record to the corresponding 'aro obligation' reference.")
    revision_date = fields.Date(string='Revision Date', required=True, default=fields.Date.context_today, help="The date when this transaction, measurement, or event was officially recorded.")
    reason = fields.Selection([('cost_escalation', 'Cost Escalation'), ('regulatory_change', 'Regulatory Change'),
                               ('scope_change', 'Scope Change'), ('engineering_studies', 'Post-Studies Refinement'),
                               ('rate_change', 'Discount Rate Change'), ('timing_change', 'Abandonment Timing Change'),
                               ('other', 'Other'), ], string='Reason', required=True, help="Select the appropriate classification or category for 'reason'.")
    old_future_cost = fields.Monetary(string='Old Future Cost', currency_field='currency_id', help="The unit rate or total financial cost applied to this transaction.")
    new_future_cost = fields.Monetary(string='New Future Cost', currency_field='currency_id', help="The unit rate or total financial cost applied to this transaction.")
    old_discount_rate = fields.Monetary(string='Old Rate (%)', digits=(6, 4), help="Specify the numerical measurement, volume, or financial amount for 'old rate (%)'.")
    new_discount_rate = fields.Monetary(string='New Rate (%)', digits=(6, 4), help="Specify the numerical measurement, volume, or financial amount for 'new rate (%)'.")
    old_abandonment_date = fields.Date(string='Old Abandonment Date', help="The date when this transaction, measurement, or event was officially recorded.")
    new_abandonment_date = fields.Date(string='New Abandonment Date', help="The date when this transaction, measurement, or event was officially recorded.")
    old_liability = fields.Monetary(string='Old Liability', currency_field='currency_id', help="Specify the numerical measurement, volume, or financial amount for 'old liability'.")
    new_liability = fields.Monetary(string='New Liability', currency_field='currency_id', help="Specify the numerical measurement, volume, or financial amount for 'new liability'.")
    delta = fields.Monetary(string='Adjustment', currency_field='currency_id',
                            help='Positive = liability increased; Negative = liability decreased.')
    move_id = fields.Many2one('account.move', string='Adjustment Journal', readonly=True, help="Link this transaction or record to the corresponding 'adjustment journal' reference.")
    description = fields.Text(string='Explanation', help="Additional comments, details, or operational remarks about this record.")
    currency_id = fields.Many2one('res.currency', related='obligation_id.currency_id', store=True,
                                  readonly=True, help="Link this transaction or record to the corresponding 'currency id' reference.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="The company managing this operational record or transaction.")


    def _compute_display_name(self):
        """Calculates and updates the 'name' value automatically based on related operational inputs."""
        for rec in self:
            rec.display_name = f"{rec.revision_date}: {dict(rec._fields['reason'].selection).get(rec.reason, rec.reason)}"
