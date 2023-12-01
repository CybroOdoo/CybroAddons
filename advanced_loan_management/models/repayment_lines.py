# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class RepaymentLine(models.Model):
    """Loan repayments """
    _name = "repayment.line"
    _description = "Repayment Line"

    name = fields.Char(string="Loan ", default="/", readonly=True,
                       help="Repayment no: of loan")
    partner_id = fields.Many2one('res.partner', string="Partner",
                                 required=True,
                                 help="Partner")
    company_id = fields.Many2one('res.company', string='Company',
                                 readonly=True,
                                 help="Company",
                                 default=lambda self: self.env.company)
    date = fields.Date(string="Payment Date", required=True,
                       default=fields.Date.today(),
                       readonly=True,
                       help="Date of the payment")
    amount = fields.Float(string="Amount", required=True, help="Amount",
                          digits=(16, 2))
    interest_amount = fields.Float(string="Interest_Amount", required=True,
                                   help="Interest Amount", digits=(16, 2))
    total_amount = fields.Float(string="Total_Amount", required=True,
                                help="Total Amount", digits=(16, 2))
    loan_id = fields.Many2one('loan.request', string="Loan Ref.",
                              help="Loan",
                              readonly=True)
    state = fields.Selection(string="State",
                             selection=[('unpaid', 'Unpaid'),
                                        ('invoiced', 'Invoiced'),
                                        ('paid', 'Paid')],
                             required=True, readonly=True, copy=False,
                             tracking=True, default='unpaid',
                             help="Includes paid and unpaid states for each "
                                  "repayments", )
    journal_loan_id = fields.Many2one('account.journal',
                                      string="Journal",
                                      store=True, default=lambda self: self.
                                      env['account.journal'].
                                      search([('code', 'like', 'CSH1')]),
                                      help="Journal Record")
    interest_account_id = fields.Many2one('account.account',
                                          string="Interest",
                                          store=True,
                                          help="Account For Interest")
    repayment_account_id = fields.Many2one('account.account',
                                           string="Repayment",
                                           store=True,
                                           help="Account For Repayment")
    invoice = fields.Boolean(string="invoice", default=False,
                             help="For monitoring the record")

    def action_pay_emi(self):
        """Creates invoice for each EMI"""
        time_now = self.date
        interest_product_id = self.env['ir.config_parameter'].sudo().get_param(
            'advanced_loan_management.interest_product_id')
        repayment_product_id = self.env['ir.config_parameter'].sudo().get_param(
            'advanced_loan_management.repayment_product_id')

        for rec in self:
            loan_lines_ids = self.env['repayment.line'].search(
                [('loan_id', '=', rec.loan_id.id)], order='date asc')
            for line in loan_lines_ids:
                if line.date < rec.date and line.state in \
                        ('unpaid', 'invoiced'):
                    message_id = self.env['message.popup'].create(
                        {'message': (
                            "You have pending amounts")})
                    return {
                        'name': 'Repayment',
                        'type': 'ir.actions.act_window',
                        'view_mode': 'form',
                        'res_model': 'message.popup',
                        'res_id': message_id.id,
                        'target': 'new'
                    }

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'invoice_date': time_now,
            'partner_id': self.partner_id.id,
            'currency_id': self.company_id.currency_id.id,
            'payment_reference': self.name,
            'invoice_line_ids': [
                (0, 0, {
                    'price_unit': self.amount,
                    'product_id': repayment_product_id,
                    'name': 'Repayment',
                    'account_id': self.repayment_account_id.id,
                    'quantity': 1,
                }),
                (0, 0, {
                    'price_unit': self.interest_amount,
                    'product_id': interest_product_id,
                    'name': 'Interest amount',
                    'account_id': self.interest_account_id.id,
                    'quantity': 1,
                }),
            ],
        })
        if invoice:
            self.invoice = True
            self.write({'state': 'invoiced'})

        return {
            'name': 'Invoice',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
        }
