# -*- coding: utf-8 -*-
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
#############################################################################
from odoo import api, models


class AccountMove(models.Model):
    """Extends account.move with the data used by the mini dashboard."""
    _inherit = 'account.move'

    @api.model
    def _get_mini_dashboard_data(self, move_type):
        """Return the dashboard figures for one move type.

        Only records of the current company are used, so the amounts are
        always expressed in the company currency shown on the dashboard.

        :param str move_type: 'out_invoice' or 'in_invoice'
        :return: counts and amounts for the dashboard
        :rtype: dict
        """
        company = self.env.company
        result = {
            'draft': 0,
            'posted': 0,
            'cancelled': 0,
            'paid': 0,
            'not_paid': 0,
            'paid_amount': 0.0,
            'not_paid_amount': 0.0,
            'lost_amount': 0.0,
            'expected_amount': 0.0,
            'company_currency_symbol': company.currency_id.symbol,
        }
        groups = self._read_group(
            [('move_type', '=', move_type), ('company_id', '=', company.id)],
            groupby=['state', 'payment_state'],
            aggregates=['__count', 'amount_total_signed:sum',
                        'amount_residual_signed:sum'],
        )
        for state, payment_state, count, total, residual in groups:
            # The signed amounts are in company currency; the sign depends
            # on the move type, so only the absolute value is displayed.
            total, residual = abs(total), abs(residual)
            if state == 'draft':
                result['draft'] += count
            elif state == 'cancel':
                result['cancelled'] += count
                result['lost_amount'] += total
            elif state == 'posted':
                result['posted'] += count
                if payment_state == 'paid':
                    result['paid'] += count
                    result['paid_amount'] += total
                elif payment_state == 'not_paid':
                    result['not_paid'] += count
                    result['not_paid_amount'] += total
                if payment_state in ('not_paid', 'partial'):
                    result['expected_amount'] += residual
        for key in ('paid_amount', 'not_paid_amount', 'lost_amount',
                    'expected_amount'):
            result[key] = company.currency_id.round(result[key])
        return result

    @api.model
    def retrieve_out_invoice_dashboard(self):
        """Return the values for the customer invoice dashboard."""
        return self._get_mini_dashboard_data('out_invoice')

    @api.model
    def retrieve_in_invoice_dashboard(self):
        """Return the values for the vendor bill dashboard."""
        return self._get_mini_dashboard_data('in_invoice')
