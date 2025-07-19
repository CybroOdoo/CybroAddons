# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
"""This module enables users to place online orders and
pick up their purchases from nearby stores. """
from odoo import api, fields, models


class StockPicking(models.Model):
    """to identify the click and collect transfer"""
    _inherit = 'stock.picking'

    is_click_and_collect_order = fields.Boolean(
        default=False, help='Whether click and collect order or not')

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Loading pos data fields"""
        return []

    @api.model
    def _load_pos_data_domain(self, data):
        """Loading pos data domains"""
        return []

    def _load_pos_data(self, data):
        """Loading pos data"""
        domain = self._load_pos_data_domain(data)
        fields = self._load_pos_data_fields(data['pos.config']['data'][0]['id'])
        return {
            'data': self.search_read(domain, fields,
                                     load=False) if domain is not False else [],
            'fields': fields,
        }

    @api.model
    def action_confirmation_click(self, order_id):
        """validate click and collect from pos config"""
        order_id = int(order_id)
        stock = self.search([])
        for rec in stock:
            for lines in rec.move_ids_without_package:
                if lines.sale_line_id.id == order_id:
                    rec.button_validate()
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
