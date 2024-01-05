# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(<https://www.cybrosys.com>)
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
###########################################################################
from odoo import api, models


class AccountMove(models.Model):
    """
    Class for defining function to fetch data
    """
    _inherit = 'account.move'

    @api.model
    def retrieve_out_invoice_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the invoice order views.
        """
        result = {
            'draft': 0,
            'posted': 0,
            'cancelled': 0,
            'paid': 0,
            'not_paid_amount': 0,
            'paid_amount': 0,
            'lost_amount': 0,
            'expected_amount': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }
        account_move = self.env['account.move']
        sum_amount = 0
        sum_invoices = account_move.search([('payment_state', '=', 'paid'),
                                            ('move_type', '=', 'out_invoice')])
        for line in sum_invoices:
            sum_amount = sum_amount + line.amount_total
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', '=', 'not_paid'),
             ('move_type', '=', 'out_invoice')])
        for line in amount_invoices:
            amount = amount + line.amount_total
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'),
             ('move_type', '=', 'out_invoice')])
        for line in lost_invoices:
            lost = lost + line.amount_total
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', '=', 'not_paid'),
             ('move_type', '=', 'out_invoice')])
        for line in expected_invoices:
            expected = expected + line.amount_total
        result['paid_amount'] = sum_amount
        result['lost_amount'] = lost
        result['not_paid_amount'] = amount
        result['expected_amount'] = expected
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', '=', 'out_invoice')])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', '=', 'out_invoice')])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', '=', 'out_invoice')])
        result['paid'] = account_move.search_count(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'out_invoice')])
        result['not_paid'] = account_move.search_count(
            [('payment_state', '=', 'not_paid'), ('state', '!=', 'draft'),
             ('move_type', '=', 'out_invoice')])
        return result

    @api.model
    def retrieve_in_invoice_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the invoice order views.
        """
        result = {
            'draft': 0,
            'posted': 0,
            'cancelled': 0,
            'paid': 0,
            'not_paid_amount': 0,
            'paid_amount': 0,
            'lost_amount': 0,
            'expected_amount': 0,
            'company_currency_symbol': self.env.company.currency_id.symbol
        }
        account_move = self.env['account.move']
        sum_amount = 0
        sum_invoices = account_move.search(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'in_invoice')])
        for line in sum_invoices:
            sum_amount = sum_amount + line.amount_total
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', '=', 'not_paid'),
             ('move_type', '=', 'in_invoice')])
        for line in amount_invoices:
            amount = amount + line.amount_total
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'), ('move_type', '=', 'in_invoice')])
        for line in lost_invoices:
            lost = lost + line.amount_total
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', '=', 'not_paid'),
             ('move_type', '=', 'in_invoice')])
        for line in expected_invoices:
            expected = expected + line.amount_total
        result['paid_amount'] = sum_amount
        result['lost_amount'] = lost
        result['not_paid_amount'] = amount
        result['expected_amount'] = expected
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', '=', 'in_invoice')])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', '=', 'in_invoice')])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', '=', 'in_invoice')])
        result['paid'] = account_move.search_count(
            [('payment_state', '=', 'paid'), ('move_type', '=', 'in_invoice')])
        result['not_paid'] = account_move.search_count(
            [('payment_state', '=', 'not_paid'), ('state', '!=', 'draft'),
             ('move_type', '=', 'in_invoice')])
        return result
