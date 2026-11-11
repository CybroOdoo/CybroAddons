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
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Model for adding pixel id in settings SEO section. """
    _inherit = 'res.config.settings'

    meta_tracking = fields.Boolean(
        string="Meta Tracking",
        config_parameter='meta_pixel_tracking.meta_tracking',
        default=False,
        help="Enable Meta tracking on your website.")
    pixel_id = fields.Char(
        string="Pixel ID",
        config_parameter='meta_pixel_tracking.pixel_id',
        help="Enter your Meta Pixel ID here.")

    @api.onchange('meta_tracking')
    def _onchange_meta_tracking(self):
        """Function to clear the pixel_id if not enabled meta_tracking"""
        if not self.meta_tracking:
            self.pixel_id = False
