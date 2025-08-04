# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anzil K A (odoo@cybrosys.com)
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
from odoo import models
from odoo.tools.float_utils import float_compare


class StockMove(models.Model):
    """ Inherits stock_move to manage pickings with respect to the
        delivery address """

    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """ Extending _get_new_picking_values to create values for new
         pickings with different delivery addresses"""
        origins = self.filtered(lambda m: m.origin).mapped('origin')
        origins = list(dict.fromkeys(origins))
        if len(origins) == 0:
            origin = False
        else:
            origin = ','.join(origins[:5])
            if len(origins) > 5:
                origin += "..."
        orders = self.env['sale.order'].search([('name', 'in', origins)])
        for rec in orders:
            address = [rec.partner_id.id]
            for line in rec.order_line:
                if line.delivery_addr_id:
                    if line.delivery_addr_id.id not in address:
                        address.append(line.delivery_addr_id.id)
                elif rec.partner_id.id not in address:
                    address.append(rec.partner_id.id)
            if len(address) <= 1:
                res = super(StockMove, self)._get_new_picking_values()
                return res
        return {
            'origin': origin,
            'company_id': self.mapped('company_id').id,
            'user_id': False,
            'move_type': self.mapped('group_id').move_type or 'direct',
            'partner_id': self.sale_line_id.delivery_addr_id.id or
                          self.sale_line_id.order_id.partner_id.id,
            'picking_type_id': self.mapped('picking_type_id').id,
            'location_id': self.mapped('location_id').id,
            'location_dest_id': self.mapped('location_dest_id').id,
        }

    def _assign_picking(self):
        """Create separate deliveries per address, ensuring all products are included."""
        picking_obj = self.env['stock.picking']
        moves_by_address = {}
        for move in self:
            if not move.sale_line_id:
                continue
            partner_id = move.sale_line_id.delivery_addr_id.id or move.sale_line_id.order_id.partner_id.id

            if partner_id not in moves_by_address:
                moves_by_address[partner_id] = self.env['stock.move']
            moves_by_address[partner_id] += move

        for partner_id, moves in moves_by_address.items():
            moves = moves.filtered(
                lambda m: float_compare(
                    m.product_uom_qty, 0.0,
                    precision_rounding=m.product_uom.rounding) >= 0
            )
            if not moves:
                continue

            picking_vals = moves._get_new_picking_values()
            picking = picking_obj.create(picking_vals)
            moves.write({'picking_id': picking.id})
            moves._assign_picking_post_process(new=True)

        return True