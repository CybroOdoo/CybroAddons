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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adding a new field to res_config_settings model for apply limit"""
    _inherit = "res.config.settings"

    purchase_limit = fields.Float(string="Purchase Limit",
                                  help='Set a minimum purchase limit for website orders',
                                  config_parameter='website_purchase_limit.purchase_limit')
    enabled_limit = fields.Boolean(string='Enable Purchase Limit',
                                   help='Enable or disable the purchase limit on the website',
                                   config_parameter='website_purchase_limit.enabled_limit')
