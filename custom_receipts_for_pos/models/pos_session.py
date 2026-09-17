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
from odoo import models


class PosSession(models.Model):
    """
       This is an Odoo model for Point of Sale (POS) sessions.
       It inherits from the 'pos.session' model and extends its functionality.
    """
    _inherit = 'pos.session'

    def _load_pos_data_models(self, config):
        """Add pos.receipt to the POS UI data load."""
        models = super()._load_pos_data_models(config)
        models.append('pos.receipt')
        return models
