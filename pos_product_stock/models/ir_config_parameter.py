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
from odoo import  api, models


class IrConfigParameter(models.Model):
    """Inherits model "stock.quant to load pos data"""
    _name = 'ir.config_parameter'
    _inherit = ['ir.config_parameter', 'pos.load.mixin']

    @api.model
    def _load_pos_data_fields(self, config):
        """Returns the list of fields to be loaded for POS data."""
        return ['key', 'value']

