# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import  api, models


class StockQuant(models.Model):
    """Inherits model "stock.quant to load pos data"""
    _name = 'stock.quant'
    _inherit = ['stock.quant','pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Returns the list of fields to be loaded for POS data."""
        return [
            'product_id', 'available_quantity', 'quantity', 'location_id'
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        """Constructs the domain for loading POS data based on the POS configuration."""
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        if config_id.location_from == 'all_warehouse':
            location_ids = self.env['stock.location'].search([])
            domain = [('location_id', 'in', location_ids.ids)]
        else:
            location_id = config_id.pos_stock_location_id
            domain = ['|', ('location_id', '=', location_id.id), ('location_id', 'in', location_id.child_ids.ids)]
        return domain
