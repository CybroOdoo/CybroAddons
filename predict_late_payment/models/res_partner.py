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


class ResPartner(models.Model):
    """
    Extend res.partner to display payment risk information computed
    by the AI-powered payment risk scoring system.
    """
    _inherit = 'res.partner'

    risk_score_id = fields.One2many(
        'payment.risk.score', 'partner_id', string='Risk Scores',
        help='Payment risk score records calculated for this customer.')
    payment_risk_score = fields.Float(
        string='Payment Risk Score', compute='_compute_payment_risk_fields',
        store=False, digits=(5, 2),
        help='Overall payment risk score calculated from the customer’s payment history.')
    payment_risk_level = fields.Selection(
        [('low', 'Low Risk'), ('medium', 'Medium Risk'),
         ('high', 'High Risk'), ('critical', 'Critical Risk')],
        string='Payment Risk Level', compute='_compute_payment_risk_fields',
        store=False,
        help='Risk category derived from the customer’s payment risk score.')
    payment_risk_color = fields.Char(
        string='Risk Color', compute='_compute_payment_risk_fields',
        store=False,
        help='Color indicator used to visually represent the customer’s payment risk level.')
    payment_avg_delay = fields.Float(
        string='Avg Payment Delay (days)',
        compute='_compute_payment_risk_fields',
        store=False, digits=(6, 1),
        help='Average number of days the customer delays payments beyond the due date.')
    payment_overdue_amount = fields.Monetary(
        string='Total Overdue Amount', compute='_compute_payment_risk_fields',
        store=False, currency_field='currency_id',
        help='Total outstanding amount from invoices that are currently overdue.')
    payment_last_computed = fields.Datetime(
        string='Score Last Computed', compute='_compute_payment_risk_fields',
        store=False,
        help='Date and time when the payment risk score was last calculated.')
    payment_followup_suggestion = fields.Text(
        string='Follow-up Suggestion', compute='_compute_payment_risk_fields',
        store=False,
        help='Suggested follow-up action for the finance team based on the customer’s payment behavior.')
    currency_id = fields.Many2one(
        'res.currency', compute='_compute_currency', string='Currency',
        help='Currency used to display the overdue amount for this customer.')

    def _compute_currency(self):
        """
        Compute the currency used for displaying monetary risk fields.
        """
        for rec in self:
            rec.currency_id = self.env.company.currency_id

    @api.depends('risk_score_id', 'risk_score_id.score',
                 'risk_score_id.risk_level', 'risk_score_id.risk_color')
    def _compute_payment_risk_fields(self):
        """
        Compute payment risk information for the partner from the
        related payment risk score record.
        """
        for partner in self:
            score_rec = partner.risk_score_id.filtered(
                lambda r: r.company_id == self.env.company
            )[:1]
            if score_rec:
                partner.payment_risk_score = score_rec.score
                partner.payment_risk_level = score_rec.risk_level
                partner.payment_risk_color = score_rec.risk_color
                partner.payment_avg_delay = score_rec.avg_delay_days
                partner.payment_overdue_amount = score_rec.total_overdue_amount
                partner.payment_last_computed = score_rec.last_computed
                partner.payment_followup_suggestion = score_rec.followup_suggestion
            else:
                partner.payment_risk_score = 0.0
                partner.payment_risk_level = False
                partner.payment_risk_color = '#6c757d'
                partner.payment_avg_delay = 0.0
                partner.payment_overdue_amount = 0.0
                partner.payment_last_computed = False
                partner.payment_followup_suggestion = False

    def action_compute_risk_score(self):
        """Button: recompute risk score from the partner form."""
        for partner in self:
            self.env['payment.risk.score'].compute_for_partner(partner.id)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Score Updated'),
                'message': _('Payment risk score has been recalculated.'),
                'sticky': False,
                'type': 'success',
            },
        }

    def action_view_risk_score(self):
        """Open the risk score detail for this partner."""
        self.ensure_one()
        score = self.env['payment.risk.score'].search([
            ('partner_id', '=', self.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if not score:
            score = self.env['payment.risk.score'].compute_for_partner(self.id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Payment Risk Score'),
            'res_model': 'payment.risk.score',
            'res_id': score.id,
            'view_mode': 'form',
            'target': 'current',
        }
