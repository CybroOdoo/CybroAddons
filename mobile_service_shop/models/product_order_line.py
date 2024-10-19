# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Jumana Jabin MP (odoo@cybrosys.com)
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
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _


class ProductOrderLine(models.Model):
    """Model for managing product order lines in mobile service operations."""
    _name = 'product.order.line'
    _description = 'Product Order Line'

    product_order_id = fields.Many2one('mobile.service',
                                       help="Reference to the related mobile "
                                            "service order to which this product"
                                            " order line belongs.")
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('is_a_parts','=', True)]",
                                 help="Product ID of the product.",
                                 required=True)
    product_uom_qty = fields.Float(string='Used Quantity', default=1.0,
                                   help="Choose a quantity to use.",
                                   required=True)
    price_unit = fields.Float(string='Unit Price', default=0.0, required=True,
                              help="Price of the product.")
    qty_invoiced = fields.Float(string='Invoiced Qty', readonly=True,
                                help="Number of invoice created.")
    qty_stock_move = fields.Float(string='Stock Move Posted Qty', readonly=True,
                                  help="Count of stock move.")
    part_price = fields.Char(compute='_compute_part_price', string='Price',
                             readonly=True, store=True, help="Price for the "
                                                             "part.")
    product_uom = fields.Char(string='Unit of Measure', required=True,
                              help="Unit of measure of the product.")
    stock_number = fields.Char(string="Picking", help="Stock move picking name",
                               readonly=True)

    @api.onchange('product_id')
    def change_prod(self):
        """It will return the product price and the unit of measurement"""
        self.ensure_one()
        if self.product_id:
            product_template_obj = self.product_id.product_tmpl_id
            self.price_unit = product_template_obj.list_price
            self.product_uom = product_template_obj.uom_id.name

    @api.depends('product_uom_qty', 'product_id')
    def _compute_part_price(self):
        """Compute the amount of part price"""
        for line in self:
            price = line.price_unit * line.product_uom_qty
            line.update({'part_price': price})
