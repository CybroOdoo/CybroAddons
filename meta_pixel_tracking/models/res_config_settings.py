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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """ Model for adding pixel id in settings SEO section. """
    _inherit = 'res.config.settings'

    meta_tracking = fields.Boolean(
        config_parameter='meta_pixel_tracking.meta_tracking', default=False,
        help='For enabling meta tracking in your website.',
        string="Meta tracking.")
    pixel_id = fields.Char(
        string='Pixel ID:', help='Enter your pixel ID here.',
        config_parameter='meta_pixel_tracking.pixel_id')

    @api.onchange('meta_tracking')
    def _onchange_meta_tracking(self):
        """Function to clear the pixel_id if not enabled meta_tracking"""
        if not self.meta_tracking:
            self.pixel_id = ""
