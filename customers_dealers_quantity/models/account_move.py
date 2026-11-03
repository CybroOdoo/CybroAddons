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
from odoo import api, fields, models


class AccountMove(models.Model):
    """This class is to set the dealer price"""
    _inherit = "account.move"

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Triggered when the 'partner_id' field is changed.
        Apply or revert dealer pricing only on eligible customer invoice lines
        without recomputing all lines or overwriting manual/sale order prices.
        """
        res = super()._onchange_partner_id()
        if self.move_type != 'out_invoice':
            return res

        company = self.company_id or self.env.company
        company_currency = company.currency_id or self.env.company.currency_id
        invoice_currency = self.currency_id or company_currency
        date = self.invoice_date or self.date or fields.Date.today()

        for line in self.invoice_line_ids:
            if line.sale_line_ids or not line.product_id:
                continue
            product = line.product_id
            if not (product.price > 0.0 or product.minimum_quantity > 0.0):
                continue

            dealer_price = company_currency._convert(
                product.price,
                invoice_currency,
                company,
                date,
            )
            if self.partner_id.dealer:
                if line.quantity >= product.minimum_quantity:
                    line.price_unit = dealer_price
            elif line.price_unit == dealer_price:
                line.price_unit = product._get_tax_included_unit_price(
                    company,
                    invoice_currency,
                    date,
                    'sale',
                    fiscal_position=self.fiscal_position_id,
                    product_uom=line.product_uom_id,
                    document_tax_mode=line.document_tax_mode,
                )
        return res
