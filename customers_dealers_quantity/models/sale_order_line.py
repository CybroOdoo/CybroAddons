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
from odoo import fields, models


class SaleOrderLine(models.Model):
    """This class is to set the dealer price"""
    _inherit = "sale.order.line"

    def _get_display_price(self):
        self.ensure_one()
        if self.order_id.partner_id.dealer and self.product_id:
            if self.product_id.price > 0.0 or self.product_id.minimum_quantity > 0.0:
                if self.product_uom_qty >= self.product_id.minimum_quantity:
                    company_currency = self.company_id.currency_id or self.env.company.currency_id
                    order_currency = self.currency_id or self.order_id.currency_id
                    date = self.order_id.date_order or fields.Date.today()
                    return company_currency._convert(
                        self.product_id.price,
                        order_currency,
                        self.company_id or self.env.company,
                        date
                    )
        return super()._get_display_price()
