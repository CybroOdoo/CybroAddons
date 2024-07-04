# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class StockMove(models.Model):
    """to identify the click and collect transfer"""
    _inherit = 'stock.picking'

    is_click_and_collect_order = fields.Boolean(default=False,
                                                string="is click and collect"
                                                       " order",
                                                help="enable to change the"
                                                     " order as click and "
                                                     "collect order")

    @api.model
    def action_confirmation_click(self, order_id):
        """validate click and collect from pos config"""
        order_id = int(order_id)
        stock = self.search([])
        for rec in stock:
            for lines in rec.move_ids_without_package:
                if lines.sale_line_id.id == order_id:
                    rec.action_set_quantities_to_reservation()
                    rec._action_done()
        return True

    @api.model
    def action_stock_picking(self, order_lines):
        """display the sale order lines in pos session"""
        record = []
        stock = self.search([('state', '!=', 'done')])
        for rec in stock:
            for lines in rec.move_ids_without_package:
                if lines.sale_line_id.id in order_lines:
                    data = {
                        'id': lines.sale_line_id.id,
                        'order_id': rec.origin,
                        'partner_id': rec.partner_id.name,
                        'product_id': rec.product_id.name,
                        'product_uom_quantity': lines.product_uom_qty,
                    }
                    record.append(data)
        return record
