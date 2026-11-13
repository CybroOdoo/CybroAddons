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
    """
    Configuration settings extension to add parameters for low stock alert.
    """
    _inherit = 'res.config.settings'

    is_low_stock_alert = fields.Boolean(
        string="Low Stock Alert",
        help='This field determines whether the low stock alert is enabled. '
             'When the product quantity falls below this value, the background '
             'color for the product will be changed based on the alert state.',
        config_parameter='low_stocks_product_alert.is_low_stock_alert')
    min_low_stock_alert = fields.Integer(
        string='Alert Quantity', default=0,
        help='Change the background color for the product based '
             'on the Alert Quantity.',
        config_parameter='low_stocks_product_alert.min_low_stock_alert')
