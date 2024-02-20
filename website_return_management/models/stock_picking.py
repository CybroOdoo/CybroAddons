# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sabeel B (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class StockPicking(models.Model):
    """Inheriting stock_picking to add new fields regarding return orders"""
    _inherit = 'stock.picking'

    return_order_id = fields.Many2one('sale.return',
                                      string='Return Order',
                                      help="Shows the return order of current"
                                           "transfer")
    return_order_pick_id = fields.Many2one('sale.return',
                                           string='Return Order Pick',
                                           help="Shows the return order picking"
                                                "of current return order")
    return_order_picking = fields.Boolean(string='Return Order Picking',
                                          help="Helps to identify delivery"
                                               " and return picking, if true"
                                               "the transfer is return picking"
                                               "else delivery")

    def button_validate(self):
        """Supering Validate Button function"""
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if rec.return_order_pick_id:
                if any(line.state != 'done' for line in
                       rec.return_order_pick_id.stock_picking_ids):
                    return res
                else:
                    for line in (rec.return_order_pick_id.sale_order_id.
                            order_line.filtered(
                            lambda ids: ids.product_id.id == rec.
                                    return_order_pick_id.product_id.id)):
                        return_order = self.env[
                            'sale.return'].sudo().search(
                            [('sale_order_id', '=',
                              rec.return_order_pick_id.sale_order_id.id),
                             ('product_id', '=',
                              rec.return_order_pick_id.product_id.id),
                             ('state', '=', 'done')])
                        if (return_order and (
                                sum(return_order.mapped('quantity')) +
                                rec.return_order_pick_id.quantity) ==
                                line.qty_delivered):
                            line.return_qty = True
                        elif (rec.return_order_pick_id.quantity ==
                              line.qty_delivered):
                            line.return_qty = True
                    rec.return_order_pick_id.state = 'done'
        return res
