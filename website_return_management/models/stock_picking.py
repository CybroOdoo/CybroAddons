# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Abbas P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class StockPicking(models.Model):
    """Class for inherit stock picking to add fields"""
    _inherit = 'stock.picking'

    return_order_id = fields.Many2one(
        'sale.return',
        help="Shows the return order of current transfer")
    return_order_pick_id = fields.Many2one(
        'sale.return',
        help="Shows the return order this return picking was created from")
    return_order_picking = fields.Boolean(
        help="Helps to identify delivery and return picking, if true the "
             "transfer is return picking else delivery")

    def button_validate(self):
        """Function for validate stock picking"""
        res = super().button_validate()
        for rec in self:
            if rec.return_order_pick_id and all(
                    picking.state == 'done'
                    for picking in rec.return_order_pick_id.return_picking_ids):
                rec.return_order_pick_id.write({'state': 'done'})
        return res
