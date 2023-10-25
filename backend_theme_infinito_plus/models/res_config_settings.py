# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    """Inhering res.config.settings class for adding new fields."""
    _inherit = 'res.config.settings'

    is_refresh = fields.Boolean(string='Tree,Kanban Refresh mode Enabled',
                                help='To check refresh button enabled or not',
                                default=False)
    chatbox_position = fields.Char(string='Chat box position',
                                   help='To set chat box position')
    animation_plus = fields.Char(string='Animation',
                                 help='To set animation position')
    google_font = fields.Integer(string='Google font',
                                 help='To set google font')

    @api.model
    def get_values(self):
        """Get the current values for the configuration settings"""
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['is_refresh'] = get_param('backend_theme_infinito_plus.is_refresh',
                                      default=False)
        res['chatbox_position'] = get_param(
            'backend_theme_infinito_plus.chatbox_position')
        res['animation_plus'] = get_param(
            'backend_theme_infinito_plus.animation_plus')
        res['google_font'] = get_param(
            'backend_theme_infinito_plus.google_font')
        return res

    @api.model
    def set_values(self):
        """Update the values of the configuration settings"""
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('backend_theme_infinito_plus.is_refresh', self.is_refresh)
        set_param('backend_theme_infinito_plus.chatbox_position',
                  self.chatbox_position)
        set_param('backend_theme_infinito_plus.animation_plus',
                  self.animation_plus)
        set_param('backend_theme_infinito_plus.google_font',
                  self.google_font)
        super(ResConfigSettings, self).set_values()
