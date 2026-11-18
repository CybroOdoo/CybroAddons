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
from odoo import models, fields, api


class PosPayment(models.Model):
    _inherit = 'pos.payment'

    amount_currency = fields.Float(
        string='Amount in Currency',
        digits='Account',
        default=0.0,
        help='Amount paid in the foreign currency.'
    )
    foreign_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        help='The currency in which the customer paid.'
    )
    currency_symbol = fields.Char(
        string='Currency Symbol',
        help='Symbol of the currency used for payment.'
    )

    def _export_for_ui(self, payment):
        """Export payment data for the POS UI, including foreign currency details.

        Args:
            payment: The payment record whose data is being exported.

        Returns:
            dict: The payment data prepared for the POS UI, including the
                foreign currency amount, currency details, and symbols.
        """
        result = super()._export_for_ui(payment)
        result['amount_currency'] = payment.amount_currency
        result['foreign_currency_id'] = payment.foreign_currency_id.id if payment.foreign_currency_id else False
        result['foreign_currency_name'] = payment.foreign_currency_id.name if payment.foreign_currency_id else ''
        result['foreign_currency_symbol'] = payment.foreign_currency_id.symbol if payment.foreign_currency_id else ''
        result['currency_symbol'] = payment.currency_symbol or ''
        return result
