# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
    _inherit = 'res.config.settings'

    is_user_edit = fields.Boolean('User edit', default=False)
    is_sidebar_enabled = fields.Boolean('Sidebar Enabled', default=False)
    is_fullscreen_enabled = fields.Boolean('Full screen Enabled', default=False)
    is_sidebar_icon = fields.Boolean('Sidebar icon Enabled', default=True)
    is_sidebar_name = fields.Boolean('Sidebar name Enabled', default=True)
    is_sidebar_company = fields.Boolean('Sidebar Company Enabled', default=False)
    is_sidebar_user = fields.Boolean('Sidebar User Enabled', default=False)
    is_recent_apps = fields.Boolean('Recent Apps Enabled', default=False)
    is_fullscreen_app = fields.Boolean('Full screen Apps Enabled', default=False)
    is_rtl = fields.Boolean('Rtl Enabled', default=False)
    is_dark = fields.Boolean('Dark mode Enabled', default=False)
    is_menu_bookmark = fields.Boolean('Menu Bookmark mode Enabled', default=False)
    is_chameleon = fields.Boolean('Chameleon mode Enabled', default=False)
    dark_mode = fields.Selection([
        ('all', 'All'),
        ('schedule', 'Schedule'),
        ('auto', 'Automatic'),
    ], default='all')
    dark_start = fields.Float('Dark Start', default=19.0)
    dark_end = fields.Float('Dark End', default=5.0)
    loader_class = fields.Char('Loader', default='default')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        get_param = self.env['ir.config_parameter'].sudo().get_param
        res['is_user_edit'] = get_param('backend_theme_infinito.is_user_edit', default=False)
        res['is_sidebar_enabled'] = get_param('backend_theme_infinito.is_sidebar_enabled', default=False)
        res['is_fullscreen_enabled'] = get_param('backend_theme_infinito.is_fullscreen_enabled', default=False)
        res['is_sidebar_icon'] = get_param('backend_theme_infinito.is_sidebar_icon', default=False)
        res['is_sidebar_name'] = get_param('backend_theme_infinito.is_sidebar_name', default=False)
        res['is_sidebar_company'] = get_param('backend_theme_infinito.is_sidebar_company', default=False)
        res['is_sidebar_user'] = get_param('backend_theme_infinito.is_sidebar_user', default=False)
        res['is_recent_apps'] = get_param('backend_theme_infinito.is_recent_apps', default=False)
        res['is_rtl'] = get_param('backend_theme_infinito.is_rtl', default=False)
        res['is_dark'] = get_param('backend_theme_infinito.is_dark', default=False)
        res['is_menu_bookmark'] = get_param('backend_theme_infinito.is_menu_bookmark', default=False)
        res['dark_mode'] = get_param('backend_theme_infinito.dark_mode', default='all')
        res['dark_start'] = get_param('backend_theme_infinito.dark_start', default=19.0)
        res['dark_end'] = get_param('backend_theme_infinito.dark_end', default=5.0)
        res['loader_class'] = get_param('backend_theme_infinito.loader_class', default=5.0)
        res['is_chameleon'] = get_param('backend_theme_infinito.is_chameleon', default=False)

        return res

    @api.model
    def set_values(self):
        set_param = self.env['ir.config_parameter'].sudo().set_param
        set_param('backend_theme_infinito.is_user_edit',
                  self.is_user_edit)
        set_param('backend_theme_infinito.is_sidebar_enabled',
                  self.is_sidebar_enabled)
        set_param('backend_theme_infinito.is_fullscreen_enabled',
                  self.is_fullscreen_enabled)
        set_param('backend_theme_infinito.is_sidebar_icon',
                  self.is_sidebar_icon)
        set_param('backend_theme_infinito.is_sidebar_name',
                  self.is_sidebar_name)
        set_param('backend_theme_infinito.is_sidebar_company',
                  self.is_sidebar_company)
        set_param('backend_theme_infinito.is_sidebar_user',
                  self.is_sidebar_user)
        set_param('backend_theme_infinito.is_recent_apps',
                  self.is_recent_apps)
        set_param('backend_theme_infinito.is_rtl',
                  self.is_rtl)
        set_param('backend_theme_infinito.is_dark',
                  self.is_dark)
        set_param('backend_theme_infinito.dark_mode',
                  self.dark_mode)
        set_param('backend_theme_infinito.dark_start',
                  self.dark_start)
        set_param('backend_theme_infinito.dark_end',
                  self.dark_end)
        set_param('backend_theme_infinito.is_menu_bookmark',
                  self.is_menu_bookmark)
        set_param('backend_theme_infinito.loader_class',
                  self.loader_class)
        set_param('backend_theme_infinito.is_chameleon',
                  self.is_chameleon)

        super(ResConfigSettings, self).set_values()
