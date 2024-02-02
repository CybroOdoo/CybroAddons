# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Yadhukrishnan K (odoo@cybrosys.com)
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
################################################################################
from odoo import fields, models


class StockPicking(models.Model):
    """inheriting the stock picking and add fields"""
    _inherit = 'stock.picking'

    return_order_id = fields.Many2one('sale.return',
                                      string='Return order',
                                      help="Shows the return order of current"
                                           "transfer")
    return_order_pick_id = fields.Many2one('sale.return',
                                           string='Return order Pick',
                                           help="Shows the return order picking"
                                                "of current return order")
    return_order_picking = fields.Boolean(string='Return order picking',
                                          help="Helps to identify delivery and "
                                               "return picking, if true the tra"
                                               "nsfer is return picking else de"
                                               "livery")

    def button_validate(self):
        """Supering the function changing the configuration"""
        res = super(StockPicking, self).button_validate()
        for rec in self:
            if rec.return_order_pick_id:
                if any(line.state != 'done' for line in
                       rec.return_order_pick.stock_picking_ids):
                    return res
                else:
                    rec.return_order_pick_id.write({'state': 'done'})
        return res
