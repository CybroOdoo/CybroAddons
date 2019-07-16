# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2009-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Sreejith P(<http://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class ProductForm(models.Model):
    _inherit = 'product.product'

    internal_location = fields.One2many('stock.quantity', 'product_id', compute='get_product_qty')

    def get_product_qty(self):
        location_list = []
        product_list = []
        obj_location = self.env['stock.location'].search([('usage', '=', 'internal')])
        for i in obj_location:
            location_list.append(i.id)
        obj_quant = self.env['stock.quant'].search([('product_id', '=', self.id),
                                                    ('location_id', 'in', location_list)])
        for obj in obj_quant:
            move_line = {'product_id': obj.product_id.id,
                         'stock_location': obj.location_id.id,
                         'qty_on_hand': obj.qty,
                         }
            product_list.append(move_line)
        for i in product_list:
            if i['qty_on_hand'] > 0:
                self.internal_location |= self.env['stock.quantity'].create(i)


class TemplateForm(models.Model):
    _inherit = 'product.template'

    internal_location = fields.One2many('stock.quantity', 'product_id', compute='get_product_qty')

    def get_product_qty(self):
        location_list = []
        product_list = []
        obj_location = self.env['stock.location'].search([('usage', '=', 'internal')])
        for i in obj_location:
            location_list.append(i.id)
        obj_product = self.env['product.product'].search([('product_tmpl_id', '=', self.id)])
        for i in obj_product:
            obj_quant = self.env['stock.quant'].search([('product_id', '=', i.id),
                                                        ('location_id', 'in', location_list)])
            for obj in obj_quant:
                move_line = {'product_id': obj.product_id.id,
                             'stock_location': obj.location_id.id,
                             'qty_on_hand': obj.qty,
                             }
                product_list.append(move_line)
        for i in product_list:
            if i['qty_on_hand'] > 0:
                self.internal_location |= self.env['stock.quantity'].create(i)


class InternalLocation(models.Model):
    _name = 'stock.quantity'

    stock_location = fields.Many2one('stock.location', string='Location Name')
    qty_on_hand = fields.Float('On Hand')
    forecast = fields.Float('Forecast')
    incoming_qty = fields.Float('Incoming Quantity')
    outgoing_qty = fields.Float('Outgoing Quantity')
    product_id = fields.Many2one('product.product', string='Product')
