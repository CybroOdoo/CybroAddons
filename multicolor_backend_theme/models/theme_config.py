# -*- coding: utf-8 -*-
##############################################################################
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
##############################################################################
from odoo import api, fields, models


class ThemeConfig(models.Model):
    """Model for storing configuration settings related to the theme"""
    _name = 'theme.config'
    _description = "Model for storing configuration settings related to the " \
                   "theme"

    name = fields.Char(string="Name")
    theme_main_color = fields.Char(
        string="Theme main color", help="main theme color")
    view_font_color = fields.Char(
        string="View font color", help="backend font color")
    theme_font_color = fields.Char(
        string="Font color", help="backend view font color")
    theme_active = fields.Boolean(string="Active")

    def write(self, vals_data):
        """only one theme can be active at a time"""
        if ('theme_active' in vals_data.keys() and
                vals_data['theme_active']):
            for theme_rec in self.search([]):
                theme_rec.theme_active = False
        res = super(ThemeConfig, self).write(vals_data)
        return res

    @api.model
    def create_new_theme(self):
        """create a new theme"""
        theme_data = self.theme_defaults()
        theme_obj = self.create(theme_data)
        theme_data = self.search_read([])
        return [theme_obj.id, theme_data]

    @api.model
    def update_color(self, vals):
        """update the color"""
        vals_data = {
            vals['key']: '#' + vals['value']
        }
        self.browse(int(vals['theme_id'])).write(vals_data)
        return

    @api.model
    def find_active(self):
        """find the active theme"""
        active_theme = self.search_read([('theme_active', '=', True)])
        return active_theme[0] if active_theme else False

    @api.model
    def update_active_theme(self, theme_id):
        """update active theme """
        for theme_obj in self.search([]):
            if theme_obj.theme_active and theme_obj.id != int(theme_id):
                theme_obj.theme_active = False
            elif not theme_obj.theme_active and theme_obj.id == int(theme_id):
                theme_obj.theme_active = True
        return

    @api.model
    def check_for_removal(self, theme_id):
        """removal of a theme"""
        theme_rec = self.browse(int(theme_id))
        if not theme_rec:
            return False
        if not theme_rec.theme_active:
            theme_rec.unlink()
        theme_data = self.search_read([])
        return theme_data

    def theme_defaults(self):
        """set default theme"""
        cr = self._cr
        cr.execute("select count(*) from theme_config")
        max_id = cr.fetchone()
        return {
            'name': 'Theme ' + str(max_id[0] + 1 if max_id else 1),
            'theme_main_color': '#6fb702',
            'view_font_color': '#333',
            'theme_font_color': '#fff',
            'theme_active': False,
        }
