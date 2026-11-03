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
from odoo import models


class PosOrder(models.Model):
    """Inherit pos.order to include multicurrency payment data in receipt."""
    _inherit = 'pos.order'

    def _order_receipt_generate_payment_data(self):
        """Include multi-currency payment data in order receipt payment lines.

        :return: List of payment line dictionaries enriched with payment_currency
                 and currency_amount.
        :rtype: list[dict]
        """
        payments = super()._order_receipt_generate_payment_data()
        for i, line in enumerate(self.payment_ids):
            if i < len(payments):
                payments[i]['payment_currency'] = line.payment_currency or False
                payments[i]['currency_amount'] = (
                    f"{line.currency_amount:.2f}" if line.currency_amount else False
                )
        return payments
