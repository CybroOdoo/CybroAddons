# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
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
from datetime import datetime
from odoo import fields, models
from odoo.tools import float_round


class SaleOrderLine(models.Model):
    """ This class extends the 'sale.order.line' model in Odoo.
    It adds functionality related to reservation stock for sale order lines."""
    _inherit = 'sale.order.line'

    picking_id = fields.Many2one('stock.picking', string='Picking',
                                 help='The associated picking for the order '
                                      'line')

    def create_reservation_stock(self):
        """ Create reservation stock for the product line."""
        picking_obj = self.env['stock.picking']
        destination_location_id = self.env.user.company_id.destination_location_id
        if not destination_location_id:
            destination_location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'),
                 ('company_id', '=', self.env.user.company_id.id)], limit=1)
        warehouse_id = self.order_id.warehouse_id
        location_id = warehouse_id.lot_stock_id
        if self._context.get('product_id'):
            product_id = self._context.get('product_id')
            product_uom = product_id.uom_id
        else:
            product_id = self.product_id
            product_uom = self.product_uom
        if self._context.get('new_qty'):
            product_uom_qty = self._context.get('new_qty')
        else:
            product_uom_qty = self.product_uom_qty
        move_lines = []
        move_lines.append((0, 0, {
            'name': product_id.name,
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'quantity': product_uom_qty,
            'product_uom': product_uom.id,
            'location_id': location_id and location_id.id,
            'location_dest_id': destination_location_id and destination_location_id.id,
        }))
        values = {
            'partner_id': self.order_id.partner_id.id,
            'location_id': location_id and location_id.id,
            'location_dest_id': destination_location_id and destination_location_id.id,
            'scheduled_date': datetime.now(),
            'date_done': datetime.now(),
            'origin': self.order_id.name,
            'owner_id': self.order_id.partner_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_ids_without_package': move_lines,
        }
        picking = picking_obj.sudo().create(values)
        picking.sudo().action_confirm()
        picking.sudo().action_assign()
        picking.sudo().button_validate()
        sms = self.env['confirm.stock.sms'].sudo().search([])
        for rec in sms:
            for pick in rec.pick_ids:
                if pick.id == picking.id:
                    rec.send_sms()
                    picking.sudo().button_validate()

        self.write({
            'picking_id': picking.id
        })

    def cancel_reservation_stock(self, picking_ids):
        """ Cancel reservation stock for the given picking IDs."""
        product_return_moves = []
        for picking in picking_ids:
            if picking.products_availability_state == "late":
                return picking.action_cancel()
            else:
                for move in picking.move_ids:
                    if move.move_dest_ids:
                        quantity = move.product_qty - sum(
                            move.sudo().filtered(
                                lambda m: m.state in [
                                    'partially_available', 'assigned',
                                    'done']).mapped('move_line_ids').mapped(
                                'qty_done'))
                    else:
                        quantity = move.product_qty
                    quantity = float_round(quantity,
                                           precision_rounding=move.product_uom.rounding)
                    product_return_moves.append((0, 0, {
                        'product_id': move.product_id.id,
                        'quantity': quantity,
                        'move_id': move.id,
                        'uom_id': move.product_id.uom_id.id,
                        'to_refund': True,
                    }))
                location_id = picking.location_id.id
                if picking.picking_type_id.return_picking_type_id\
                        .default_location_dest_id.return_location:
                    location_id = picking.picking_type_id\
                        .return_picking_type_id.default_location_dest_id.id
                stock_return = self.env['stock.return.picking'].sudo().create({
                    'product_return_moves': product_return_moves,
                    'picking_id': picking.id,
                    'original_location_id': picking.location_id.id,
                    'parent_location_id': picking.picking_type_id.warehouse_id and picking.picking_type_id.warehouse_id.view_location_id.id or picking.location_id.location_id.id,
                    'location_id': location_id
                })
                if stock_return:
                    new_picking_id, pick_type_id = stock_return.sudo()._create_returns()
                    new_picking = self.env['stock.picking'].sudo().browse(
                        new_picking_id)
                    if new_picking.mapped('move_line_ids').filtered(
                            lambda move: move.state in ['confirmed',
                                                        'waiting']):
                        new_picking.sudo().action_confirm()
                        new_picking.sudo().action_assign()
                        # new_picking.sudo().action_set_quantities_to_reservation()
                        new_picking.sudo().button_validate()
                    else:
                        new_picking.sudo().action_confirm()
                        new_picking.sudo().action_assign()
                        # new_picking.sudo().action_set_quantities_to_reservation()
                        new_picking.sudo().button_validate()

    def unlink(self):
        """ Override unlink method to cancel reservation stock when deleting
        product lines in draft reservation orders."""
        for line in self:
            order_id = line.order_id
            if order_id.state == 'draft' and order_id.type_name == 'Reservation':
                if line.picking_id:
                    line.sudo().cancel_reservation_stock(line.picking_id)
        return super(SaleOrderLine, self).unlink()
