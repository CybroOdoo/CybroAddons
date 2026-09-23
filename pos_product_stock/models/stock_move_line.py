# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, models


class StockMoveLine(models.Model):
    """Inherits model "stock.move.line to load pos data fields"""
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the list of fields to be loaded for POS data."""
        result = super()._load_pos_data_fields(config)
        result.extend(['product_id', 'location_dest_id', 'quantity', 'location_id'])
        return result

    @api.model
    def _load_pos_data_domain(self, data):
        """Constructs the domain for loading POS move line data."""
        config_id = data.get('pos.config')
        if not config_id:
            return []
        if config_id.location_from == 'all_warehouse':
            return []
        else:
            location_id = config_id.pos_stock_location_id
            if not location_id:
                return []
            return ['|', ('location_id', 'child_of', location_id.id), ('location_dest_id', 'child_of', location_id.id)]

