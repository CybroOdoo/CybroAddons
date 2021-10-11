# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Milind Mohan @ Cybrosys, (odoo@cybrosys.com)
#            Mohammed Shahil M P @ Cybrosys, (odoo@cybrosys.com)
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields, api, _


class ProductOrderLine(models.Model):

    _name = 'product.order.line'

    product_order_id = fields.Many2one('mobile.service')

    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('is_a_parts','=', True)]", required=True)
    product_uom_qty = fields.Float(string='Used Quantity', default=1.0, required=True)
    price_unit = fields.Float(string='Unit Price', default=0.0, required=True)
    qty_invoiced = fields.Float(string='Invoiced qty', readonly=True)
    qty_stock_move = fields.Float(string='Stock Move Posted Qty', readonly=True)
    part_price = fields.Char(compute='_compute_amount', string='Price', readonly=True, store=True)
    product_uom = fields.Char(string='Unit of Measure', required=True)

    @api.onchange('product_id')
    def change_prod(self):
        self.ensure_one()
        if self.product_id:
            product_template_obj = self.product_id.product_tmpl_id
            self.price_unit = product_template_obj.list_price
            self.product_uom = product_template_obj.uom_id.name

    @api.depends('product_uom_qty', 'product_id')
    def _compute_amount(self):
        """
        Compute the amount
        """
        for line in self:
            price = line.price_unit * line.product_uom_qty

            line.update({
                'part_price': price,
            })

    def _create_stock_moves_transfer(self, picking):
        moves = self.env['stock.move']
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
                    (6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
            }
            qty = self.product_uom_qty - self.qty_stock_move
            print(qty)
            diff_quantity = qty
            tmp = template.copy()
            tmp.update({
                'product_uom_qty': diff_quantity,
            })
            template['product_uom_qty'] = diff_quantity
            done += moves.create(template)
            self.qty_stock_move = self.qty_stock_move + qty
        return done