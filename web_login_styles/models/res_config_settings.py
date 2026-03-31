# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gee Paul Joby (<https://www.cybrosys.com>)
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
###############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherits 'res.config.settings' to add fields for customize login page."""
    _inherit = 'res.config.settings'

    orientation = fields.Selection(selection=[('default', 'Default'),
                                              ('left', 'Left'),
                                              ('middle', 'Middle'),
                                              ('right', 'Right')],
                                   string="Orientation",
                                   help="Type of login page visibility",
                                   config_parameter="web_login_styles.orientation")
    background = fields.Selection(selection=[('color', 'Color Picker'),
                                             ('image', 'Image'),
                                             ('url', 'URL')],
                                  string="Background",
                                  help="Background of the login page",
                                  config_parameter="web_login_styles.background")
    image = fields.Binary(string="Image", help="Select background image "
                                               "of login page")
    url = fields.Char(string="URL", help="Select and url of image",
                      config_parameter="web_login_styles.url")
    color = fields.Char(string="Color", help="Set a colour for background "
                                             "of login page",
                        config_parameter="web_login_styles.color")

    @api.model
    def get_values(self):
        """
        Retrieve configuration values for the login page customization.

        This method extends the default `get_values` to fetch the stored
        login background image from system parameters and populate the
        settings form accordingly.

        :return: Dictionary of configuration values
        :rtype: dict
        """
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(image=params.get_param('web_login_styles.image'))
        return res

    def set_values(self):
        """
        Save configuration values for the login page customization.

        This method extends the default `set_values` to persist the selected
        login background image into system parameters.
        """
        super(ResConfigSettings, self).set_values()
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('web_login_styles.image', self.image)

    @api.onchange('orientation')
    def onchange_orientation(self):
        """
        Reset background customization fields when default orientation is selected.

        When the orientation is set to 'default', this method clears all
        background-related fields to hide customization options and ensure
        the standard login page layout is used.
        """
        if self.orientation == 'default':
            self.background = False
            self.color = False
            self.image = False
            self.url = False
