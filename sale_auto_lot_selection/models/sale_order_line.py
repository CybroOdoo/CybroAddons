# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arjun S(odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    """
    Inherits the model Sale Order Line to extend and add extra field and method
    for the working of the app.
    """
    _inherit = 'sale.order.line'

    lot_ids = fields.Many2many('stock.lot', string='Lot',
                               domain="[('product_id','=', product_id)]",
                               help='Lot from which the product will be sold')

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Method _action_launch_stock_rule will super the already existing method
        and select the lots automatically when confirming the Sale Order
        """
        res = super(SaleOrderLine, self)._action_launch_stock_rule(
            previous_product_uom_qty)
        for order_line in self:
            move = self.env['stock.move'].search(
                [('sale_line_id', '=', order_line.id)])
            for items in move.move_line_ids:
                items.unlink()
            for lot in order_line.lot_ids:
                move.move_line_ids = [fields.Command.create({
                    'lot_id': lot.id,
                    'qty_done': move.sale_line_id.product_uom_qty,
                    'product_id': move.sale_line_id.product_id.id,
                    'product_uom_id': move.sale_line_id.product_uom.id,
                    'location_id': move.location_id.id,
                    'location_dest_id': move.location_dest_id.id,
                    'reserved_uom_qty': move.sale_line_id.product_uom_qty,
                    'company_id': self.env.company.id,
                    'picking_id': move.picking_id.id,
                })]
        return res
