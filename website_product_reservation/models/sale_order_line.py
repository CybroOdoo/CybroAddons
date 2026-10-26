# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import datetime
from odoo import fields, models


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
        company = self.order_id.company_id or self.env.company
        destination_location_id = company.destination_location_id
        if not destination_location_id:
            destination_location_id = self.env['stock.location'].search(
                [('usage', '=', 'internal'),
                 ('company_id', '=', company.id)], limit=1)
        warehouse_id = self.order_id.warehouse_id
        location_id = warehouse_id.lot_stock_id
        if self.env.context.get('product_id'):
            product_id = self.env.context.get('product_id')
            product_uom = product_id.uom_id
        else:
            product_id = self.product_id
            product_uom = self.product_uom_id or product_id.uom_id
        if self.env.context.get('new_qty'):
            product_uom_qty = self.env.context.get('new_qty')
        else:
            product_uom_qty = self.product_uom_qty
        move_lines = []
        move_vals = {
            'product_id': product_id.id,
            'product_uom_qty': product_uom_qty,
            'quantity': product_uom_qty,
            'uom_id': product_uom.id,
            'location_id': location_id and location_id.id,
            'location_dest_id': destination_location_id and destination_location_id.id,
        }
        if 'name' in self.env['stock.move']._fields:
            move_vals['name'] = product_id.name
        else:
            move_vals['description_picking'] = product_id.name
        move_lines.append((0, 0, move_vals))
        values = {
            'partner_id': self.order_id.partner_id.id,
            'location_id': location_id and location_id.id,
            'location_dest_id': destination_location_id and destination_location_id.id,
            'scheduled_date': datetime.now(),
            'date_done': datetime.now(),
            'origin': self.order_id.name,
            'owner_id': self.order_id.partner_id.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'move_ids': move_lines,
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
        for picking in picking_ids:
            if picking.state in ['draft', 'waiting', 'confirmed', 'assigned'] or picking.products_availability_state == "late":
                picking.action_cancel()
                continue
            if hasattr(picking, '_create_return'):
                new_picking = picking.sudo()._create_return()
                for move in new_picking.move_ids:
                    orig_move = move.move_orig_ids[:1]
                    qty = orig_move.quantity or orig_move.product_uom_qty or 1.0
                    move.product_uom_qty = qty
                    move.quantity = qty
                    move.picked = True
                new_picking.sudo().action_confirm()
                new_picking.sudo().action_assign()
                for move in new_picking.move_ids:
                    if not move.quantity:
                        orig_move = move.move_orig_ids[:1]
                        move.quantity = orig_move.quantity or orig_move.product_uom_qty or 1.0
                    move.picked = True
                new_picking.sudo().button_validate()
            else:
                picking.action_cancel()

    def unlink(self):
        """ Override unlink method to cancel reservation stock when deleting
        product lines in draft reservation orders."""
        for line in self:
            order_id = line.order_id
            if order_id.state == 'draft' and order_id.is_reservation_order:
                if line.picking_id:
                    line.sudo().cancel_reservation_stock(line.picking_id)
        return super().unlink()
