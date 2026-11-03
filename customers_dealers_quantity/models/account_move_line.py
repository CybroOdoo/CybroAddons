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


class AccountMoveLine(models.Model):
    """This class is to set the dealer price"""
    _inherit = "account.move.line"

    @api.depends('product_id', 'product_uom_id')
    def _compute_price_unit(self):
        """Override to apply dealer pricing with currency conversion."""
        res = super()._compute_price_unit()
        for line in self:
            if (
                line.move_id.move_type == 'out_invoice'
                and line.move_id.partner_id.dealer
                and not line.sale_line_ids
                and line.product_id
                and (line.product_id.price > 0.0 or line.product_id.minimum_quantity > 0.0)
                and line.quantity >= line.product_id.minimum_quantity
            ):
                company_currency = line.company_id.currency_id or line.env.company.currency_id
                invoice_currency = line.move_id.currency_id or company_currency
                date = line.move_id.invoice_date or line.move_id.date or fields.Date.today()
                dealer_price = company_currency._convert(
                    line.product_id.price,
                    invoice_currency,
                    line.company_id or line.env.company,
                    date,
                )
                line.price_unit = dealer_price
        return res

    @api.onchange('quantity')
    def _onchange_quantity_dealer_price(self):
        """Apply dealer pricing when quantity is changed in the UI only for dealer out-invoices."""
        for line in self:
            if (
                line.move_id.move_type == 'out_invoice'
                and line.move_id.partner_id.dealer
                and not line.sale_line_ids
                and line.product_id
                and (line.product_id.price > 0.0 or line.product_id.minimum_quantity > 0.0)
            ):
                company_currency = line.company_id.currency_id or line.env.company.currency_id
                invoice_currency = line.move_id.currency_id or company_currency
                date = line.move_id.invoice_date or line.move_id.date or fields.Date.today()
                dealer_price = company_currency._convert(
                    line.product_id.price,
                    invoice_currency,
                    line.company_id or line.env.company,
                    date,
                )
                if line.quantity >= line.product_id.minimum_quantity:
                    line.price_unit = dealer_price
                elif line.price_unit == dealer_price:
                    line.price_unit = line.product_id._get_tax_included_unit_price(
                        line.company_id or line.env.company,
                        invoice_currency,
                        date,
                        'sale',
                        fiscal_position=line.move_id.fiscal_position_id,
                        product_uom=line.product_uom_id,
                        document_tax_mode=line.document_tax_mode,
                    )
