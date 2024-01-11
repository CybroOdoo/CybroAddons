# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP S (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models, _


class ProductOrderLine(models.Model):
    _name = 'product.order.line'
    _description = 'Product Order Line'

    product_order_id = fields.Many2one('mobile.service')
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

    def _create_stock_moves_transfer(self, picking):
        """It will return the stock moves"""
        done = self.env['stock.move'].browse()
        if self.product_id.product_tmpl_id.type != 'service':
            price_unit = self.price_unit
            template = {
                'name': self.product_id.product_tmpl_id.name or '',
                'product_id': self.product_id.id,
                'product_uom': self.product_id.product_tmpl_id.uom_id.id,
                'location_id': picking.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.product_order_id.person_name.property_stock_customer.id,
                'picking_id': picking.id,
                'move_dest_ids': False,
                'state': 'draft',
                'company_id': self.product_order_id.company_id.id,
                'price_unit': price_unit,
                'picking_type_id': picking.picking_type_id.id,
                'route_ids': 1 and [
                    (6, 0, [x.id for x in self.env['stock.route'].search(
                        [('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id}
            diff_quantity = self.product_uom_qty - self.qty_stock_move
            tmp = template.copy()
            tmp.update({'product_uom_qty': diff_quantity})
            template['product_uom_qty'] = diff_quantity
            done += self.env['stock.move'].create(template)
            self.qty_stock_move = self.qty_stock_move + diff_quantity
        return done
