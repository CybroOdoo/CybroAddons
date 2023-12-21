# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited res.config.settings and added required fields"""
    _inherit = 'res.config.settings'

    margin_left_color = fields.Char(string="Margin Left Color",
                                    help='Margin-left color of mandatory field',
                                    config_parameter="mandatory_field_highlight"
                                                     ".margin_left_color")
    margin_right_color = fields.Char(string="Margin Right Color",
                                     help='Margin-right color of mandatory '
                                          'field',
                                     config_parameter=
                                     "mandatory_field_highlight"
                                     ".margin_right_color")
    margin_top_color = fields.Char(string="Margin Top Color",
                                   help='Margin-top color of mandatory field',
                                   config_parameter="mandatory_field_highlight"
                                                    ".margin_top_color")
    margin_bottom_color = fields.Char(string="Margin Bottom Color",
                                      help='Margin-bottom color of mandatory '
                                           'field',
                                      config_parameter=
                                      "mandatory_field_highlight"
                                      ".margin_bottom_color")
    field_background_color = fields.Char(string="Field Background Color",
                                         help='Background color of mandatory '
                                              'field',
                                         config_parameter=
                                         "mandatory_field_highlight."
                                         "field_background_color")

    def set_values(self):
        """inorder to set values in the settings"""
        res = super().set_values()
        self.env['ir.config_parameter'].set_param(
            'mandatory_field_highlight.margin_left_color',
            self.margin_left_color)
        self.env['ir.config_parameter'].set_param(
            'mandatory_field_highlight.margin_right_color',
            self.margin_right_color)
        self.env['ir.config_parameter'].set_param(
            'mandatory_field_highlight.margin_top_color',
            self.margin_top_color)
        self.env['ir.config_parameter'].set_param(
            'mandatory_field_highlight.margin_bottom_color',
            self.margin_bottom_color)
        self.env['ir.config_parameter'].set_param(
            'mandatory_field_highlight.field_background_color',
            self.field_background_color)
        return res

    @api.model
    def get_values(self):
        """inorder to get values from the settings"""
        res = super().get_values()
        margin_left_color = self.env['ir.config_parameter'].sudo().get_param(
            'mandatory_field_highlight.margin_left_color')
        margin_right_color = self.env['ir.config_parameter'].sudo().get_param(
            'mandatory_field_highlight.margin_right_color')
        margin_top_color = self.env['ir.config_parameter'].sudo().get_param(
            'mandatory_field_highlight.margin_top_color')
        margin_bottom_color = self.env['ir.config_parameter'].sudo().get_param(
            'mandatory_field_highlight.margin_bottom_color')
        field_background_color = self.env['ir.config_parameter'].sudo().get_param(
            'mandatory_field_highlight.field_background_color')
        res.update(
            margin_left_color=margin_left_color,
            margin_right_color=margin_right_color,
            margin_top_color=margin_top_color,
            margin_bottom_color=margin_bottom_color,
            field_background_color=field_background_color)
        return res
