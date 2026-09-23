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


class StockQuant(models.Model):
    """Inherits model stock.quant to load pos data"""
    _inherit = ['stock.quant', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the list of fields to be loaded for POS data."""
        return ['product_id', 'available_quantity', 'quantity', 'location_id']

    @api.model
    def _load_pos_data_domain(self, data):
        """Constructs the domain for loading POS data based on the POS configuration."""
        config_id = data.get('pos.config')
        if config_id and hasattr(config_id, 'location_from'):
            if config_id.location_from == 'current_warehouse' and config_id.pos_stock_location_id:
                return [('location_id', 'child_of', config_id.pos_stock_location_id.id)]
        return [('location_id.usage', '=', 'internal')]
