# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Shijin V (<https://www.cybrosys.com>)
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
###################################################################################


from odoo import models, fields, api, _


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self):
        new_picking, pick_type_id = super(StockReturnPicking, self)._create_returns()
        picking = self.env['stock.picking'].browse(new_picking)
        if self.picking_id.return_order:
            picking.write({'return_order_picking': False,
                           'return_order': False,
                           'return_order_pick': self.picking_id.return_order.id})
            self.picking_id.return_order.write({'state': 'confirm'})
        return new_picking, pick_type_id


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    return_order = fields.Many2one('sale.return', string='Return order',
                                   help="Shows the return order of current transfer")
    return_order_pick = fields.Many2one('sale.return', string='Return order Pick',
                                        help="Shows the return order picking  of current return order")
    return_order_picking = fields.Boolean(string='Return order picking',
                                          help="Helps to identify delivery and return picking, if true the transfer is return picking else delivery")

    def button_validate(self):
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if rec.return_order_pick:
                if any(line.state != 'done' for line in rec.return_order_pick.stock_picking):
                    return res
                else:
                    rec.return_order_pick.write({'state': 'done'})
        return res
