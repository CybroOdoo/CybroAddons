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
from datetime import datetime
from odoo import fields, models


class CreditDetails(models.Model):
    """
        Model for managing credit details associated with customers.
    """
    _name = "credit.details"
    _description = "Credit Details"
    _rec_name = 'customer_id'

    credit_id = fields.Many2one(
        'credit.amount',
        help='Reference to the associated credit amount record.')
    customer_id = fields.Many2one(
        'res.partner', string='Customer',
        help='Reference to the associated customer/partner.')
    credit_amount = fields.Float(
        "Credit", compute='_compute_credit_amount',
        help='Representing the total credit amount associated with this '
             'record.')
    debit_amount = fields.Float(
        "Debit", compute='_compute_debit_amount',
        help='Representing the total debit amount associated with this record.')
    credit_details_amount = fields.Float(
        "Credit Details", compute='_compute_credit_details_amount',
        help='Representing the total credit details amount associated with '
             'this record.')
    updated_amount = fields.Float(
        "Update", help='Field used for updating the credit amount.')
    credit_details_ids = fields.One2many(
        'credit.detail.lines', 'credit_id',
        help='Credit detail lines associated with this record.')
    debit_details_ids = fields.One2many(
        'debit.detail.lines', 'debit_id',
        help='Debit detail lines associated with this record.')
    _is_amount_updated = fields.Boolean(
        string='to check whether the credit is updated with accounts')

    def _compute_credit_amount(self):
        """ Function to compute the credit amount """
        for rec in self:
            rec.credit_amount = 0.0
            if rec.credit_details_ids:
                rec.credit_amount = sum(
                    rec.credit_details_ids.mapped('amount'))

    def _compute_debit_amount(self):
        """"" Function to compute the debit amount """
        for rec in self:
            rec.debit_amount = 0.0
            if rec.debit_details_ids:
                rec.debit_amount = sum(
                    rec.debit_details_ids.mapped('debit_amount'))

    def _compute_credit_details_amount(self):
        """ Function to compute the credit details amount """
        for rec in self:
            rec.credit_details_amount = 0.0
            rec.credit_details_amount = rec.credit_amount + rec.debit_amount

    def _compute_amount_updated(self):
        for rec in self:
            if rec.credit_details_ids.mapped(
                    'previous_credit_amount').pop() < rec.credit_details_amount:
                rec._is_amount_updated = True

    def action_update_account(self):
        """ Function to update the amount in the account payment"""
        self._is_amount_updated = True
        return {
            'name': 'Credit Payment',
            'view_mode': 'form',
            'res_model': 'credit.payment',
            'type': 'ir.actions.act_window',
            'context': {'default_partner_id': self.customer_id.id,
                        'default_credit_amount': self.credit_details_ids.mapped(
                            'amount').pop(),
                        'default_payment_journal': self.env[
                            'account.journal'].search([('type', '=', 'bank')],
                                                      limit=1).id,
                        'default_credit_detail_id': self.id,
                        },
            'target': 'new'
        }


class CreditDetailsLines(models.Model):
    """ Model for managing credit detail lines associated with credit details"""
    _name = "credit.detail.lines"
    _description = "Credit Detail Lines"

    credit_id = fields.Many2one('credit.details', string=" Credit Id",
                                help="Credit detail associate with this "
                                     "record.")
    customer_id = fields.Many2one('res.partner', string="Customer details",
                                  help="Customer details")
    amount = fields.Float(string='Amount',
                          help="Total credit amount associated with the "
                               "partner.")
    previous_credit_amount = fields.Float(string='Previous Credit Amount',
                                          help='The previous credit amount')
    approve_date = fields.Datetime(string='Approve Date',
                                   default=datetime.today(),
                                   help='Approved date of the credit amount')
    updated_amount = fields.Float(string='Updated Amount',
                                  help='Updated amount')


class DebitDetailsLines(models.Model):
    """ Model for managing debit detail lines associated with credit details """
    _name = "debit.detail.lines"
    _description = "Debit Detail lines"

    debit_id = fields.Many2one('credit.details', string=" Credit Id",
                               help="Credit detail associate with this record.")
    customer_id = fields.Many2one('res.partner', string="Customer details",
                                  help="Customer details")
    debit_amount = fields.Float(string='Amount',
                                help="Total credit amount associated with the "
                                     "partner.")
    previous_debit_amount = fields.Float(string='Previous Debit Amount',
                                         help='The previous credit amount')
    approve_date = fields.Datetime('Approve Date', default=datetime.today(),
                                   help='Approved date of the credit amount')
    updated_amount = fields.Float(string='Updated Amount',
                                  help='Updated amount')
