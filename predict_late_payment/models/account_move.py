# -- coding: utf-8 --
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
from odoo import api, fields, models, _


class AccountMove(models.Model):
    """
    Extend account.move to display customer payment risk information
    directly on invoices.
    """
    _inherit = 'account.move'

    invoice_payment_risk_score = fields.Float(
        string='Customer Risk Score',
        compute='_compute_invoice_risk', store=False, digits=(5, 2),
        help='AI-calculated payment risk score of the customer based on their payment history.')
    invoice_payment_risk_level = fields.Selection(
        [('low', 'Low Risk'), ('medium', 'Medium Risk'),
         ('high', 'High Risk'), ('critical', 'Critical Risk')],
        string='Customer Risk Level',
        compute='_compute_invoice_risk', store=False,
        help='Risk category of the customer determined from the payment risk score.')
    invoice_payment_risk_color = fields.Char(
        string='Risk Color', compute='_compute_invoice_risk', store=False,
        help='Color code used to visually represent the customer’s payment risk level.')
    invoice_days_overdue = fields.Integer(
        string='Days Overdue', compute='_compute_invoice_risk', store=False,
        help='Number of days the invoice payment is overdue based on the due date.')

    @api.depends('partner_id', 'invoice_date_due', 'payment_state')
    def _compute_invoice_risk(self):
        """
        Compute the payment risk score, level, color, and overdue days
        for invoices based on the partner's risk scoring record.
        """
        today = fields.Date.today()
        for move in self:
            partner = move.partner_id
            if partner and move.move_type == 'out_invoice':
                score_rec = self.env['payment.risk.score'].search([
                    ('partner_id', '=', partner.id),
                    ('company_id', '=', move.company_id.id),
                ], limit=1)
                if score_rec:
                    move.invoice_payment_risk_score = score_rec.score
                    move.invoice_payment_risk_level = score_rec.risk_level
                    move.invoice_payment_risk_color = score_rec.risk_color
                else:
                    move.invoice_payment_risk_score = 0.0
                    move.invoice_payment_risk_level = False
                    move.invoice_payment_risk_color = '#6c757d'
            else:
                move.invoice_payment_risk_score = 0.0
                move.invoice_payment_risk_level = False
                move.invoice_payment_risk_color = '#6c757d'
            # Days overdue
            if (move.invoice_date_due
                    and move.payment_state not in ('paid', 'in_payment')
                    and move.invoice_date_due < today):
                move.invoice_days_overdue = (today - move.invoice_date_due).days
            else:
                move.invoice_days_overdue = 0

    def _get_last_payment_date(self):
        """
        Return the date of the last reconciled payment for this invoice.
        Used by the risk scoring engine.
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda l: l.account_id.reconcile)
        pay_dates = []
        for line in lines:
            for partial in line.matched_credit_ids + line.matched_debit_ids:
                other = partial.credit_move_id if line in partial.debit_move_id else partial.debit_move_id
                if other.date:
                    pay_dates.append(other.date)
        return max(pay_dates) if pay_dates else None

    def action_compute_partner_risk(self):
        """Button on the invoice to refresh the partner's risk score."""
        for move in self:
            if move.partner_id:
                self.env['payment.risk.score'].compute_for_partner(
                    move.partner_id.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Score Updated'),
                'message': _('Partner payment risk score recalculated.'),
                'sticky': False,
                'type': 'success',
            },
        }
