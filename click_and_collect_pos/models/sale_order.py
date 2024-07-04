# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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


class SaleOrder(models.Model):
    """to show the click and collect delivery order in smart button"""
    _inherit = 'sale.order'

    collect_count = fields.Integer(string='Click And Collect',
                                   compute='_compute_collect_count',
                                   help='collect count')

    @api.depends('collect_count')
    def _compute_collect_count(self):
        """to see the click and collect orders count"""
        count = self.env['stock.picking'].search_count(
            [('is_click_and_collect_order', '=', True),
             ('origin', '=', self.name)])
        self.collect_count = count

    def _action_confirm(self):
        """this action is used for confirm delivery orders"""
        self.action_split_delivery_order()
        return super(SaleOrder, self)._action_confirm()

    def action_split_delivery_order(self):
        """to split delivery order and click and collect order separately"""
        click_and_collect_list = []
        for line in self.order_line.filtered(lambda l: l.is_click_and_collect):
            click_and_collect_list.append(line)
        for res in click_and_collect_list:
            delivery_order = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'location_id':
                    self.env.ref('stock.stock_location_customers').id,
                'location_dest_id':
                    self.env.ref('stock.stock_location_customers').id,
                'picking_type_id': self.env.ref('stock.picking_type_out').id,
                'sale_id': self.id,
                'origin': self.name,
                'is_click_and_collect_order': True
            })
            move = self.env['stock.move'].create({
                'name': res.name,
                'product_id': res.product_id.id,
                'product_uom_qty': res.product_uom_qty,
                'product_uom': res.product_uom.id,
                'picking_id': delivery_order.id,
                'location_id': delivery_order.location_id.id,
                'location_dest_id': delivery_order.location_dest_id.id,
                'sale_line_id': res.id,
            })
            move._action_confirm()
        return True

    def action_view_click_and_collect(self):
        """smart button for click and collect"""
        self.ensure_one()
        return {
            'name': 'Click And Collect',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'domain': [('origin', '=', self.name),
                       ('is_click_and_collect_order', '=', True)],
            'context': "{'create':False}"
        }
