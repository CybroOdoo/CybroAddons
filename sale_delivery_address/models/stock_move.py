# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo.tools.misc import groupby


class StockMove(models.Model):
    """ Inherits stock_move to manage pickings with respect to the
    delivery address. """
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """ Extending _get_new_picking_values to create values for new
        pickings with different delivery addresses. """
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
            # if no delivery address is selected for order lines,
            # only one transfer will be created
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
        """ Extending _assign_picking function to create new pickings for
        order lines having different delivery addresses. """
        picking_obj = self.env['stock.picking']
        grouped_moves = groupby(self, key=lambda m: m._key_assign_picking())
        for group, moves in grouped_moves:
            moves = self.env['stock.move'].concat(*moves)
            picking = moves[0]._search_picking_for_assignation()
            if picking:
                vals = {}
                if any(picking.partner_id.id != move.partner_id.id for move in moves):
                    vals['partner_id'] = False
                if any(picking.origin != move.origin for move in moves):
                    vals['origin'] = False
                if vals:
                    picking.write(vals)
            else:
                moves = moves.filtered(
                    lambda m: float_compare(
                        m.product_uom_qty, 0.0,
                        precision_rounding=m.product_uom.rounding) >= 0)
                if not moves:
                    continue
                new_picking = True
                origins = moves[0].origin
                orders = self.env['sale.order'].search(
                    [('name', '=', origins)])
                for rec in orders:
                    addr = [rec.partner_id.id]
                    for line in rec.order_line:
                        if line.delivery_addr_id and line.delivery_addr_id.id \
                                not in addr:
                            addr.append(line.delivery_addr_id.id)
                        elif line.delivery_addr_id and rec.partner_id.id not \
                                in addr:
                            addr.append(rec.partner_id.id)
                    if len(addr) <= 1:
                        return super(StockMove, self)._assign_picking()
                    else:
                        for mov in moves:
                            mov.write({
                                'partner_id':
                                    mov.sale_line_id.delivery_addr_id.id
                                    or mov.sale_line_id.order_id.partner_id.id
                            })
                        move_ids = []
                        for index, value in enumerate(addr):
                            for mov in moves:
                                if mov.partner_id.id == value:
                                    move_ids.append(mov.id)
                            mvs = self.env['stock.move'].search(
                                [('id', 'in', move_ids)])
                            move_ids = []
                            if mvs:
                                picking = picking_obj.create(
                                    mvs._get_new_picking_values())
                                mvs.write({'picking_id': picking.id})
                            mvs._assign_picking_post_process(new=new_picking)
        return True
