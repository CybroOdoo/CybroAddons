# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sigha CK (odoo@cybrosys.com)
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
    """Class for adding new fields in configuration settings"""
    _inherit = 'res.config.settings'

    is_refresh = fields.Boolean(string='Refresh', help='Tree,Kanban Refresh '
                                                       'mode Enabled',
                                default=False)
    chatbox_position = fields.Char(string="ChatBox position",
                                   help="different layouts for chatBox")
    animation_plus = fields.Char(stirng="Animation",
                                 help="Different Animations")

    @api.model
    def get_values(self):
        """Get the current values for the configuration settings"""
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['is_refresh'] = get_param('backend_theme_infinito_plus.is_refresh',
                                      default=False)
        res['chatbox_position'] = get_param('backend_theme_infinito_plus'
                                            '.chatbox_position')
        res['animation_plus'] = get_param('backend_theme_infinito_plus'
                                          '.animation_plus')
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
        super(ResConfigSettings, self).set_values()
