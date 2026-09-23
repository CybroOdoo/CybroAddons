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


class PosSession(models.Model):
    """inherit pos.session to add fields and modules in session."""
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config):
        """Extend the list of models to be loaded in the POS session."""
        models = super()._load_pos_data_models(config)
        return models + ['stock.quant', 'stock.move.line', 'ir.config_parameter']


