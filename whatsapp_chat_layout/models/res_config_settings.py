# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra MP (odoo@cybrosys.com)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit the model res_config_settings to add fields"""
    _inherit = 'res.config.settings'

    background_color = fields.Char(string='Background Color',
                                   config_parameter='base_setup.background_color',
                                   default='#FFFFFF',
                                   help='Select discuss background color')
    layout_color = fields.Char(string='Layout Color',
                               config_parameter='base_setup.layout_color',
                               default='#3a8180',
                               help='select discuss layout color')
    chat_background = fields.Binary(string="Background Image",
                                    related='company_id.background_image',
                                    readonly=False,
                                    help='Add background image for discuss')

    def get_color(self):
        """Function to return values into js"""
        colors = {'background_color': self.env[
            'ir.config_parameter'].sudo().get_param(
            'base_setup.background_color'), 'layout_color': self.env[
            'ir.config_parameter'].sudo().get_param(
            'base_setup.layout_color'),
            'background_image': self.env.user.company_id.background_image}
        return colors
