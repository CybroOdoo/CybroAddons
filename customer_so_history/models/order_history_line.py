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


class OrderHistoryLine(models.Model):
    """Read-only copy of a past sale order line, shown on the sale order."""

    _name = 'order.history.line'
    _description = 'Order History Line'

    order_id = fields.Many2one(
        'sale.order', string='Sale Order', ondelete='cascade',
        help="Sale order on which this history line is displayed.")
    name = fields.Char(
        string='Order', help="Reference of the past sale order.")
    product_id = fields.Many2one(
        'product.product',
        help="Product included in the past order.")
    product_uom_qty = fields.Float(
        string='Quantity', help="Quantity ordered in the past order.")
    price_unit = fields.Float(
        string='Unit Price', help="Unit price of the ordered product.")
    tax_id = fields.Many2many(
        'account.tax', string='Taxes',
        help="Taxes applied to the past order line.")
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        help="Company related to this record.")
    price_subtotal = fields.Float(
        string='Subtotal', help="Subtotal of the past order line.")

    def action_add(self):
        """Add a new sale order line using the selected history line."""
        self.ensure_one()
        self.env['sale.order.line'].create({
            'order_id': self.order_id.id,
            'product_id': self.product_id.id,
            'product_uom_qty': self.product_uom_qty,
            'price_unit': self.price_unit,
            'tax_ids': [fields.Command.set(self.tax_id.ids)],
        })
