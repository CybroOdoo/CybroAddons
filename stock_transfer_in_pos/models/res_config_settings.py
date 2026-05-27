# -*- coding: utf-8 -*-
"""Res Config Settings Model"""
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies(odoo@cybrosys.com)
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

###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting model for adding a field to settings that allow to
            transfer stock from pos session """
    _inherit = 'res.config.settings'

    is_stock_transfer = fields.Boolean(related="pos_config_id.stock_transfer",
                                       string="Enable Stock Transfer",
                                       help="Enable if you want to transfer "
                                       "stock from PoS session", readonly=False)
