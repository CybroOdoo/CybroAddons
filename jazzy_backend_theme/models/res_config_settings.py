# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import models, fields


class ResCompany(models.Model):
    """Inherits the Res Company Model"""
    _inherit = 'res.company'

    background_image = fields.Binary(string="Background Image", attachment=True)


class ResConfigSettings(models.TransientModel):
    """Inherits the Configuration settings Model"""
    _inherit = 'res.config.settings'

    theme_background = fields.Binary(string="App menu Background",
                                     related='company_id.background_image',
                                     readonly=False)

    app_bar_color = fields.Char(string='Appbar color',
                                config_parameter='jazzy_backend_theme.appbar_color',
                                default='#000000')
    primary_accent = fields.Char(string="Navbar color",
                                 config_parameter='jazzy_backend_theme.primary_accent_color',
                                 default='#004589')
    secondary_accent = fields.Char(string="Navbar color",
                                   config_parameter='jazzy_backend_theme.secondary_color',
                                   default='#0C4D9D')

    kanban_bg_color = fields.Char(string="Kanban Bg Color",
                                  config_parameter='jazzy_backend_theme.kanban_bg_color',
                                  default='#F7F7F7')

    primary_hover = fields.Char(string="Hover Primary Color",
                                config_parameter='jazzy_backend_theme.primary_hover',
                                default='#00376E')
    light_hover = fields.Char(string="Light Hover",
                              config_parameter='jazzy_backend_theme.light_hover',
                              default='#ffffff')
    appbar_text = fields.Char(string="Home Menu Text Color",
                              config_parameter='jazzy_backend_theme.appbar_text',
                              default='#ffffff')
    secoundary_hover = fields.Char(string="AppBar Hover",
                                   config_parameter='jazzy_backend_theme.secoundary_hover',
                                   default='#F2F2F3')

    def config_color_settings(self):
        """Define the configuration color settings"""
        colors = {}
        colors['full_bg_img'] = self.env.user.company_id.background_image
        colors['appbar_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.appbar_color')
        colors['primary_accent'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.primary_accent_color')
        colors['secondary_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.secondary_color')
        colors['kanban_bg_color'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.kanban_bg_color')
        colors['primary_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.primary_hover')
        colors['light_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.light_hover')
        colors['appbar_text'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.appbar_text')
        colors['secoundary_hover'] = self.env[
            'ir.config_parameter'].sudo().get_param(
            'jazzy_backend_theme.secoundary_hover')

        return colors
