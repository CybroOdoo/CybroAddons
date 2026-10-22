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

class StockLocation(models.Model):
    """Inheriting stock location to load internal locations into POS"""
    _name = 'stock.location'
    _inherit = ['stock.location', 'pos.load.mixin']

    @api.model
    def _load_pos_data_domain(self, data):
        return [('usage', '=', 'internal')]

    @api.model
    def _load_pos_data_fields(self, config):
        return ['id', 'name']

