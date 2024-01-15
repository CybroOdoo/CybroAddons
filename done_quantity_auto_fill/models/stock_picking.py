# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class StockPicking(models.Model):
    """inheriting the stock_move for updating the done quantity"""
    _inherit = 'stock.picking'

    select_all_toggle = fields.Boolean(string="All", default=False,
                                       help="Can select all the lines",
                                       copy=False)

    def action_select_all(self):
        """select the product from order line"""
        self.select_all_toggle = True
        for rec in self.move_ids_without_package:
            rec.product_select = True

    def action_unselect_all(self):
        """select the product from order line"""
        self.select_all_toggle = False
        for rec in self.move_ids_without_package:
            rec.product_select = False

    def action_fill_done_qty(self):
        """search for the corresponding sale order
            write the product quantity in to the done quantity"""
        for pick in self.move_ids_without_package:
            if pick.product_select and pick.forecast_availability > 0:
                pick.write({'quantity': pick.product_uom_qty})

    def action_unfill_done_qty(self):
        """search for the corresponding sale order
        un fill the product quantity in to the done quantity"""
        self.move_ids_without_package.filtered(
            lambda pick: pick.product_select).sudo().write(
            {'quantity': '0'})
