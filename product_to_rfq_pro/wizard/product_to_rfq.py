# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Albin PJ (odoo@cybrosys.com)
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
from datetime import date, timedelta
from odoo import api, fields, models, _


class ProductToRfq(models.TransientModel):
    """This is for wizard view"""
    _name = 'product.to.rfq'
    _description = "Product To RFQ"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string="Product",
                                 readonly=True, help="Product Name")
    qty = fields.Float(string="Quantity", default=1.00, help="Product Quantity")
    order_id = fields.Many2one('purchase.order', string="RFQ No.",
                               readonly=True, help="Purchase Order")
    price_unit = fields.Float(string="Unit Price",
                              help="Price unit of the product")
    recent_products_ids = fields.One2many('recent.products.tree.purchase',
                                          'purchase_id',
                                          string="Recent Products",
                                          help="Recent products purchased")
    recent_date = fields.Datetime(string="Recent Purchase From",
                                  default=date.today() + timedelta(days=30),
                                  help="Recent date")

    @api.onchange('recent_date')
    def _onchange_recent_date(self):
        """We can get the recent products"""
        purchase_order_ids = self.env['purchase.order.line'].search(
            [('product_id', '=', self.product_id.id),
             ('order_id.date_order', '<=', self.recent_date),
             ('state', '=',
              ['purchase']),
             ])
        vals = purchase_order_ids.mapped(lambda record: (0, 0, {
            'order_line_id': record.id,
        }))
        self.recent_products_ids = vals

    def action_add_to_rfq(self):
        """We can add products to RFQ from wizard"""
        quot_id = self.order_id
        product_id = self.product_id
        display_name = product_id.name_get()[0][1]
        if product_id.description_sale:
            display_name += '\n' + product_id.description_sale
        if not quot_id.order_line:
            quot_id.order_line.create({
                'product_id': product_id.id,
                'name': display_name,
                'product_qty': self.qty,
                'price_unit': self.price_unit,
                'date_planned': fields.Datetime.today(),
                'product_uom': product_id.product_tmpl_id.uom_id.id,
            })
        else:
            products = [rec.product_id.id for rec in quot_id.order_line]
            price_unit = [rec.price_unit for rec in quot_id.order_line]
            if product_id.id not in products:
                quot_id.order_line.create({
                    'product_id': product_id.id,
                    'name': display_name,
                    'product_qty': self.qty,
                    'price_unit': self.price_unit,
                    'date_planned': fields.Datetime.today(),
                    'product_uom': product_id.product_tmpl_id.uom_id.id,
                })
            elif product_id.id in products and self.price_unit in price_unit:
                for rec in quot_id.order_line.search(
                        [('product_id', '=', product_id.id),
                         ('price_unit', '=', self.price_unit)]):
                    rec.product_qty += self.qty
            else:
                quot_id.order_line.create({
                    'product_id': product_id.id,
                    'name': display_name,
                    'product_qty': self.qty,
                    'price_unit': self.price_unit,
                    'date_planned': fields.Datetime.today(),
                    'product_uom': product_id.product_tmpl_id.uom_id.id,
                })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _(f'Product Successfully Added to {quot_id.name}'),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
