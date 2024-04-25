# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, fields, models


class PantryOrderLine(models.Model):
    """A class that represents a new model pantry order line"""
    _name = 'pantry.order.line'
    _description = 'Pantry Order Line'

    pantry_order_id = fields.Many2one('pantry.order', string='Pantry Order',
                                      required=True,
                                      help='The corresponding pantry order')
    product_id = fields.Many2one('product.product', string='Product',
                                 required=True,
                                 domain=[('pantry_product', '=', True)],
                                 help='The product to order')
    quantity = fields.Float(string='Quantity',
                            help='The quantity of the product')
    unit_price = fields.Float(string='Unit Price',
                              help='The unit price of the product')
    subtotal = fields.Float(string='Subtotal', compute='_compute_subtotal',
                            help='The subtotal of the order line')

    @api.depends('quantity')
    def _compute_subtotal(self):
        """Calculates the subtotal"""
        for rec in self:
            rec.subtotal = rec.quantity * rec.unit_price
