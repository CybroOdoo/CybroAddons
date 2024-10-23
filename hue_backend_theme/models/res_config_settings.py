# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
    """
    Inherit settings model.
    """
    _inherit = 'res.config.settings'

    theme_background = fields.Binary(string="App menu Background",
                                     related='company_id.background_image',
                                     readonly=False)
    app_bar_color = fields.Char(string='Appbar color',
                                config_parameter='hue_backend_theme.'
                                'appbar_color',
                                default='#000000')
    primary_accent = fields.Char(string="Navbar color",
                                 config_parameter='hue_backend_theme.'
                                 'primary_accent_color',
                                 default='#A53860')
    kanban_bg_color = fields.Char(string="Kanban Bg Color",
                                  config_parameter='hue_backend_theme.'
                                  'kanban_bg_color',
                                  default='#F7F7F7')
    primary_hover = fields.Char(string="Hover Primary Color",
                                config_parameter='hue_backend_theme.'
                                'primary_hover',
                                default='#953256')
    light_hover = fields.Char(string="Light Hover",
                              config_parameter='hue_backend_theme.light_hover',
                              default='#d5d5d5')
    appbar_text = fields.Char(string="Home Menu Text Color",
                              config_parameter='hue_backend_theme.appbar_text',
                              default='#F7F8F7')
    appbar_hover = fields.Char(string="AppBar Hover",
                               config_parameter='hue_backend_theme.'
                               'appbar_hover',
                               default='#953256')

    def config_color_settings(self):
        """
        To return dict of colors.
        """
        colors = {
            'full_bg_img': self.env.user.company_id.background_image,
            'appbar_color': self.env['ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.appbar_color'),
            'primary_accent': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.primary_accent_color'),
            'secondary_color': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.secondary_color'),
            'kanban_bg_color': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.kanban_bg_color'),
            'primary_hover': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.primary_hover'),
            'light_hover': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.light_hover'),
            'appbar_text': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.appbar_text'),
            'appbar_hover': self.env[
                'ir.config_parameter'].sudo().get_param(
                'hue_backend_theme.appbar_hover')
        }
        return colors
