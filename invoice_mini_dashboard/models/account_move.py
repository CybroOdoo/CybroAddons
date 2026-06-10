# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Arshad Ali Pottengal(<https://www.cybrosys.com>)
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
    def retrieve_out_invoice_dashboard(self, domain=None):
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
        # Determine move_types from domain or context
        move_types = set()
        if domain:
            for leaf in domain:
                if isinstance(leaf, (list, tuple)) and len(leaf) == 3 and leaf[0] == 'move_type' and leaf[1] == '=':
                    if leaf[2] in ('out_invoice', 'out_refund'):
                        move_types.add(leaf[2])
        # If domain didn't specify, check context (optional fallback, but domain is preferred)
        if not move_types:
            default_move_type = self._context.get('default_move_type')
            if default_move_type in ('out_invoice', 'out_refund'):
                move_types.add(default_move_type)
        # If still empty (no domain filter, no context default), or if BOTH were found in domain (e.g. OR), use both
        if not move_types or len(move_types) > 1:
            query_move_types = ['out_invoice', 'out_refund']
        else:
            query_move_types = list(move_types)
        sum_amount = 0
        sum_invoices = account_move.search([('payment_state', 'in', ('paid', 'in_payment')),
                                            ('state', '=', 'posted'),
                                            ('move_type', 'in', query_move_types)])
        for line in sum_invoices:
            sum_amount += line.amount_total_signed
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', 'in', ('not_paid', 'partial')),
             ('state', '=', 'posted'),
             ('move_type', 'in', query_move_types)])
        for line in amount_invoices:
            amount += line.amount_residual_signed
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'),
             ('move_type', 'in', query_move_types)])
        for line in lost_invoices:
            lost += line.amount_total_signed
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', 'in', query_move_types)])
        for line in expected_invoices:
            expected += line.amount_residual_signed
        result['paid_amount'] = sum_amount
        result['lost_amount'] = lost
        result['not_paid_amount'] = amount
        result['expected_amount'] = expected
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', 'in', query_move_types)])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', 'in', query_move_types)])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', 'in', query_move_types)])
        result['paid'] = account_move.search_count(
            [('payment_state', 'in', ('paid', 'in_payment')), ('state', '=', 'posted'), ('move_type', 'in', query_move_types)])
        result['not_paid'] = account_move.search_count(
            [('payment_state', 'in', ('not_paid', 'partial')), ('state', '=', 'posted'),
             ('move_type', 'in', query_move_types)])
        return result

    @api.model
    def retrieve_in_invoice_dashboard(self, domain=None):
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
        # Determine move_types from domain or context
        move_types = set()
        if domain:
            for leaf in domain:
                if isinstance(leaf, (list, tuple)) and len(leaf) == 3 and leaf[0] == 'move_type' and leaf[1] == '=':
                    if leaf[2] in ('in_invoice', 'in_refund'):
                        move_types.add(leaf[2])
        # If domain didn't specify, check context
        if not move_types:
            default_move_type = self._context.get('default_move_type')
            if default_move_type in ('in_invoice', 'in_refund'):
                move_types.add(default_move_type)
        # If still empty or both, use both
        if not move_types or len(move_types) > 1:
            query_move_types = ['in_invoice', 'in_refund']
        else:
            query_move_types = list(move_types)
        sum_amount = 0
        sum_invoices = account_move.search(
            [('payment_state', 'in', ('paid', 'in_payment')), ('state', '=', 'posted'), ('move_type', 'in', query_move_types)])
        for line in sum_invoices:
            sum_amount -= line.amount_total_signed
        amount = 0
        amount_invoices = account_move.search(
            [('payment_state', 'in', ('not_paid', 'partial')),
             ('state', '=', 'posted'),
             ('move_type', 'in', query_move_types)])
        for line in amount_invoices:
            amount -= line.amount_residual_signed
        lost = 0
        lost_invoices = account_move.search(
            [('state', '=', 'cancel'), ('move_type', 'in', query_move_types)])
        for line in lost_invoices:
            lost -= line.amount_total_signed
        expected = 0
        expected_invoices = account_move.search(
            [('state', '=', 'posted'), ('payment_state', 'in', ('not_paid', 'partial')),
             ('move_type', 'in', query_move_types)])
        for line in expected_invoices:
            expected -= line.amount_residual_signed
        result['paid_amount'] = sum_amount
        result['lost_amount'] = lost
        result['not_paid_amount'] = amount
        result['expected_amount'] = expected
        result['draft'] = account_move.search_count(
            [('state', '=', 'draft'), ('move_type', 'in', query_move_types)])
        result['posted'] = account_move.search_count(
            [('state', '=', 'posted'), ('move_type', 'in', query_move_types)])
        result['cancelled'] = account_move.search_count(
            [('state', '=', 'cancel'), ('move_type', 'in', query_move_types)])
        result['paid'] = account_move.search_count(
            [('payment_state', 'in', ('paid', 'in_payment')), ('state', '=', 'posted'), ('move_type', 'in', query_move_types)])
        result['not_paid'] = account_move.search_count(
            [('payment_state', 'in', ('not_paid', 'partial')), ('state', '=', 'posted'),
             ('move_type', 'in', query_move_types)])
        return result
