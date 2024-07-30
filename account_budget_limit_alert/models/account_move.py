# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    """Inherited to add extra fields and functions"""
    _inherit = "account.move"

    budget_warning = fields.Text(string='Warning',
                                 help='The warning message to be displayed'
                                      ' on the screen.',
                                 compute="_compute_budget_warning")
    budget_alert = fields.Boolean(string="Alert",
                                  help="True if need to raise budget alert",
                                  compute="_compute_budget_warning")
    alert_message = fields.Text(string='Alert Warning',
                                help='The alert message to be displayed on'
                                     ' the popup.',
                                compute="_compute_budget_warning")

    @api.depends('line_ids.price_total', 'line_ids.analytic_distribution')
    def _compute_budget_warning(self):
        """Function for computing values of budget_warning, budget_alert and
         alert_message"""
        for rec in self:
            rec.budget_warning = ""
            rec.budget_alert = False
            rec.alert_message = ""
            for line in rec.line_ids:
                if line.analytic_distribution:
                    account_ids = [int(account_id) for key in
                                   line.analytic_distribution.keys() for
                                   account_id in
                                   key.split(',')]
                    for acc in account_ids:
                        alert_line = self.env['budget.lines'].search(
                            [('analytic_account_id', '=', acc),
                             ('planned_amount', '<', line.price_total),
                             ('alert_type', '=', 'stop')],
                            order='planned_amount', limit=1)
                        if alert_line:
                            rec.budget_alert = True
                            rec.alert_message = (rec.alert_message +
                                                 ("Account %s - %s Exceeds %s%.2f\n" % (
                                                     alert_line.analytic_account_id.name,
                                                     alert_line.analytic_account_id.partner_id.name,
                                                     rec.currency_id.symbol,
                                                     round(
                                                         line.price_total - alert_line.planned_amount,
                                                         2))))
                            rec.budget_warning = rec.budget_warning + (
                                    "Account %s - %s Exceeds %s%.2f\n" % (
                                alert_line.analytic_account_id.name,
                                alert_line.analytic_account_id.partner_id.name,
                                rec.currency_id.symbol,
                                round(
                                    line.price_total - alert_line.planned_amount,
                                    2)))
                        else:
                            warning_line = self.env['budget.lines'].search(
                                [('analytic_account_id', '=', acc),
                                 ('planned_amount', '<', line.price_total),
                                 ('alert_type', '=', 'warning')],
                                order='planned_amount', limit=1)
                            if warning_line:
                                rec.budget_warning = (rec.budget_warning +
                                                      (
                                                              "Account %s - %s Exceeds %s%.2f\n" % (
                                                          warning_line.analytic_account_id.name,
                                                          warning_line.analytic_account_id.partner_id.name,
                                                          rec.currency_id.symbol,
                                                          round(
                                                              line.price_total - warning_line.planned_amount,
                                                              2))))

    def action_post(self):
        """Override to check the budget limit"""
        moves_with_payments = self.filtered('payment_id')
        other_moves = self - moves_with_payments
        if self.budget_alert:
            raise ValidationError("%s" % self.alert_message)
        else:
            if moves_with_payments:
                moves_with_payments.payment_id.action_post()
            if other_moves:
                other_moves._post(soft=False)
        return False
