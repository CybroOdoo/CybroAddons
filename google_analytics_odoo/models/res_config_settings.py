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
    """Inherits 'res.config.settings' to add Google Analytics configuration fields."""
    _inherit = 'res.config.settings'

    measurement_id_analytics = fields.Char(
        config_parameter='google_analytics_odoo.measurement_id_analytics',
        string='Measurement ID',
        help='Measurement ID of Google Analytics')
    api_secret = fields.Char(
        config_parameter='google_analytics_odoo.api_secret',
        string='API Secret',
        help='API secret of Google Analytics')
    enable_analytics = fields.Boolean(
        config_parameter='google_analytics_odoo.enable_analytics',
        help='Enable to send events to Google Analytics')
