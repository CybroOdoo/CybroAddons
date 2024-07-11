# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResPartner(models.Model):
    """
        Inherited Model res partner adding the credit details.
    """
    _inherit = "res.partner"

    credit_amount = fields.Float(compute='_compute_credit_amount',
                                 string='Credit Amount',
                                 help='Here the credit amount for the '
                                      'associated customer.')
    allow_credit_amount = fields.Boolean(
        string='Allow credit payment when Order Amount is More Than Credit '
               'Balance',
        help='Field allows the customer to purchase if the credit amount is '
             'insufficient.')
    cust_credit_line_ids = fields.One2many('credit.detail.lines', 'customer_id',
                                           string='Credit Details',
                                           help='Credit details associated '
                                                'with the customer')

    def _compute_credit_amount(self):
        """ Compute function to get the credit amount of the associated
        customer"""
        for record in self:
            credit_count = self.env['credit.details'].search(
                [('customer_id', '=', record.id)])
            record.credit_amount = credit_count.credit_details_amount

    def credit_details(self):
        """ Function to return the credit details associated with the
        customer."""
        return {
            'name': 'Credits',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'credit.details',
            'type': 'ir.actions.act_window',
            'domain': [('customer_id', '=', self.id)]
        }


class CustomerCreditDetails(models.Model):
    """ Model to get the customer credit details """
    _name = 'customer.credit.details'
    _description = "Customer Credit Details"

    customer_credit_id = fields.Many2one('res.partner', string='Customer Id',
                                         help='To attach with the customer '
                                              'model')
    customer_credit_details_id = fields.Many2one('credit.detail.lines',
                                                 string='Customer Credit '
                                                        'Details',
                                                 help='The field to get the '
                                                      'customer credit details')
    date = fields.Date(string='Date',
                       help='The date field for the associated credit detail '
                            'lines.')
    amount = fields.Float(string='Amount',
                          help='To get the credit amount for the partner')
    previous_credit_amount = fields.Float(string='Previous Credit Amount',
                                          help='The previous credit amount '
                                               'associated with the partner.')
    updated_amount = fields.Float('Updated Amount',
                                  help='The Updated amount associated with '
                                       'the partner.')


class AccountPayment(models.Model):
    """ Inherited the Model "account.payment" to add the customer details """
    _inherit = "account.payment"
    _description = "Account Payment"

    customer_credit_payment_id = fields.Many2one('res.partner',
                                                 string='Customer',
                                                 help='The customer details '
                                                      'add to the account '
                                                      'payment.')
