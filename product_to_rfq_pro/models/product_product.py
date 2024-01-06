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
from odoo import fields, models, _


class Product(models.Model):
    """We can add products directly to RFQ"""
    _inherit = 'product.product'

    def action_add_to_rfq_direct(self):
        """We can add products directly to RFQ using this button click"""
        quot_id = (self.env['purchase.order'].
                   browse(self._context.get('active_id')))
        name = self.product_tmpl_id.name_get()[0][1]
        if self.product_tmpl_id.description_sale:
            name += '\n' + self.product_tmpl_id.description_sale
        if not quot_id.order_line:
            quot_id.order_line.create({
                'product_id': self.id,
                'name': name,
                'product_qty': 1.00,
                'date_planned': fields.Datetime.today(),
                'price_unit': self.product_tmpl_id.standard_price,
                'product_uom': self.product_tmpl_id.uom_id.id,
                'order_id': quot_id.id
            })
        else:
            products = [rec.product_id.id for rec in quot_id.order_line]
            if self.id not in products:
                quot_id.order_line.create({
                    'product_id': self.id,
                    'name': name,
                    'product_qty': 1.00,
                    'date_planned': fields.Datetime.today(),
                    'price_unit': self.product_tmpl_id.standard_price,
                    'product_uom': self.product_tmpl_id.uom_id.id,
                    'order_id': quot_id.id
                })
            else:
                for rec in quot_id.order_line.search(
                        [('product_id', '=', self.id),
                         ('price_unit', '=', self.standard_price)]):
                    rec.product_qty += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _(f'Product Successfully Added to {quot_id.name}'),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_get_purchase_wizard(self):
        """We can get the wizard view"""
        res = {
            'name': _('Product Details'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.to.rfq',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {
                'default_order_id': self.env['purchase.order'].
                browse(self._context.get('active_id')).id,
                'default_product_id': self.id,
                'default_price_unit': self.product_tmpl_id.standard_price
            }
        }
        return res
