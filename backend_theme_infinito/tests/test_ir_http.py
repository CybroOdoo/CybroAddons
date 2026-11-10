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
import json

from odoo.tests import HttpCase, TransactionCase, tagged

from odoo.addons.backend_theme_infinito.models.ir_http import (
    float_to_time, to_bool)


@tagged('post_install', '-at_install')
class TestIrHttpHelpers(TransactionCase):

    def test_to_bool(self):
        self.assertTrue(to_bool(True))
        self.assertFalse(to_bool(False))
        self.assertFalse(to_bool(None))
        for value in ('1', 'true', 'True', ' yes ', 'on', 't', 'y'):
            self.assertTrue(to_bool(value), value)
        for value in ('0', 'false', 'no', '', 'off'):
            self.assertFalse(to_bool(value), value)

    def test_float_to_time(self):
        self.assertEqual(float_to_time(19.5), '19:30')
        self.assertEqual(float_to_time(5.0), '05:00')
        self.assertEqual(float_to_time('6.25'), '06:15')


@tagged('post_install', '-at_install')
class TestSessionInfo(HttpCase):

    def _session_info(self):
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/web/session/get_session_info',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': {}}),
            headers={'Content-Type': 'application/json'})
        return response.json()['result']

    def _set_params(self, values):
        params = self.env['ir.config_parameter'].sudo()
        for key, value in values.items():
            params.set_param('backend_theme_infinito.%s' % key, value)

    def test_session_info_uses_global_settings(self):
        # userEdit is also written by backend_theme_infinito_plus,
        # so it is not asserted here.
        self._set_params({
            'is_user_edit': 'False',
            'is_sidebar_enabled': 'True',
            'is_sidebar_icon': 'False',
            'is_recent_apps': 'True',
            'is_rtl': 'True',
            'dark_mode': 'schedule',
            'dark_start': '20.5',
            'dark_end': '6.0',
            'loader_class': 'spinner',
        })
        res = self._session_info()
        self.assertTrue(res['sidebar'])
        self.assertFalse(res['sidebarIcon'])
        self.assertTrue(res['recentApps'])
        self.assertTrue(res['infinitoRtl'])
        self.assertEqual(res['infinitoDarkMode'], 'schedule')
        self.assertEqual(res['infinitoDarkStart'], '20:30')
        self.assertEqual(res['infinitoDarkEnd'], '06:00')
        self.assertEqual(res['loaderClass'], 'spinner')

    def test_session_info_uses_user_settings(self):
        # Global value is False, user value is True: if the result is True
        # the per-user branch was used.
        self._set_params({'is_user_edit': 'True',
                          'is_sidebar_enabled': 'False'})
        user = self.env.ref('base.user_admin')
        user.write({'is_sidebar_enabled': True})
        res = self._session_info()
        self.assertTrue(res['sidebar'])
        self.assertEqual(res['sidebarIcon'], user.is_sidebar_icon)
        self.assertEqual(res['infinitoDarkMode'], user.dark_mode)
        self.assertEqual(res['infinitoDarkStart'],
                         float_to_time(user.dark_start))
        self.assertEqual(res['infinitoDarkEnd'],
                         float_to_time(user.dark_end))
        self.assertEqual(res['loaderClass'], user.loader_class)

    def test_session_info_bookmarks(self):
        user = self.env.ref('base.user_admin')
        Bookmark = self.env['infinito.menu.bookmark']
        Bookmark.create({'name': 'Inventory', 'user_id': user.id})
        Bookmark.create({'name': False, 'user_id': user.id})
        res = self._session_info()
        short_names = {b['short_name'] for b in res['infinitoMenuBookmarks']}
        self.assertEqual(short_names, {'IN', 'BO'})
        self.assertIn('infinitoBookmarks', res)