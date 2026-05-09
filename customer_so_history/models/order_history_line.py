# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class OrderHistoryLine(models.Model):
    _name = 'order.history.line'
    _description = 'Order History Line'

    order_id = fields.Many2one('sale.order', string='Sale Order',
                               help="Sale order linked to this record.")
    name = fields.Char(string='Order', help="Order line reference.")
    product_id = fields.Many2one('product.product', string='Product',
                                 help="Product included in the order.")
    product_uom_qty = fields.Float(string='Quantity',
                                     help="Ordered product quantity.")
    price_unit = fields.Float(string='Unit price',
                                help="Product Unit Price Ordered")
    tax_id = fields.Many2many('account.tax',
                              help="Taxes applied to this order line.", string='Taxes',)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 help="Company related to this record.")
    price_subtotal = fields.Float(string='Subtotal',
                                    help="Subtotal of the Placed Order")

    def action_add(self):
        """Add a new sale order line using the selected product details."""
        existing_line = self.env['sale.order.line'].search([
            ('order_id', '=', self.order_id.id),
            ('product_id', '=', self.product_id.id)
        ], limit=1)
        
        if existing_line:
            existing_line.product_uom_qty += self.product_uom_qty
        else:
            vals = {
                'order_id': self.order_id.id,
                'product_id': self.product_id.id,
                'product_uom_qty': self.product_uom_qty,
                'price_unit': self.price_unit,
                'tax_id': self.tax_id.ids,
                'price_subtotal': self.price_subtotal,
                'company_id': self.company_id.id,
            }
            self.env['sale.order.line'].sudo().create(vals)
