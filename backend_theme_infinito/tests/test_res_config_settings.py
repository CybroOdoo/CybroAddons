# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3)   , Version 3.
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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):

    def _param(self, key):
        return self.env['ir.config_parameter'].sudo().get_param(
            'backend_theme_infinito.%s' % key)

    def test_set_values_saves_parameters(self):
        settings = self.env['res.config.settings'].create({
            'is_user_edit': True,
            'is_sidebar_enabled': True,
            'is_fullscreen_enabled': True,
            'is_sidebar_icon': False,
            'is_recent_apps': True,
            'is_rtl': True,
            'is_dark': True,
            'is_menu_bookmark': True,
            'is_chameleon': True,
            'dark_mode': 'schedule',
            'dark_start': 20.0,
            'dark_end': 6.0,
            'loader_class': 'spinner',
        })
        settings.set_values()
        self.assertEqual(self._param('is_user_edit'), 'True')
        self.assertEqual(self._param('is_sidebar_enabled'), 'True')
        self.assertEqual(self._param('dark_mode'), 'schedule')
        self.assertEqual(self._param('dark_start'), '20.0')
        self.assertEqual(self._param('dark_end'), '6.0')
        self.assertEqual(self._param('loader_class'), 'spinner')
        self.assertEqual(self._param('is_chameleon'), 'True')

    def test_get_values_reads_parameters(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('backend_theme_infinito.is_user_edit', 'True')
        params.set_param('backend_theme_infinito.dark_mode', 'auto')
        params.set_param('backend_theme_infinito.loader_class', 'spinner')
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['is_user_edit'], 'True')
        self.assertEqual(values['dark_mode'], 'auto')
        self.assertEqual(values['loader_class'], 'spinner')

    def test_get_values_defaults(self):
        values = self.env['res.config.settings'].get_values()
        self.assertEqual(values['dark_mode'], 'all')
        self.assertIn('is_sidebar_icon', values)
        self.assertIn('is_chameleon', values)