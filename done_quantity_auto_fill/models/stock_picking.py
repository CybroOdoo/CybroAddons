# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saneen K (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class StockPicking(models.Model):
    """Inherits the stock. picking for updating the done quantity"""
    _inherit = 'stock.picking'

    select_all_toggle = fields.Boolean(string="All", default=False,
                                       help="Select all the lines")

    @api.onchange('select_all_toggle')
    def _onchange_select_all_toggle(self):
        """Select the product from order line while clicking on the
         toggle button"""
        for rec in self.move_ids_without_package:
            rec.is_product_select = self.select_all_toggle

    def action_fill_done_qty(self):
        """Search for the corresponding sale order
            write the product quantity in to the done quantity"""
        for pick in self.move_ids_without_package:
            if pick.is_product_select and pick.forecast_availability > 0:
                pick.write({'quantity_done': pick.product_uom_qty})

    def action_unfill_done_qty(self):
        """Search for the corresponding sale order
            unfill the product quantity in to the done quantity"""
        self.move_ids_without_package.filtered(
            lambda pick: pick.is_product_select).sudo().write(
            {'quantity_done': '0'})
