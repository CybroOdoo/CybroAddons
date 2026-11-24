# -*- coding: utf-8 -*-
#############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
# You can modify it under the terms of the GNU LESSER
# GENERAL PUBLIC LICENSE (LGPL v3) , Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import json

from odoo.addons.backend_theme_infinito_plus.models.ir_http import (
    get_current_lang)
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install')
class TestCurrentLang(TransactionCase):

    def test_get_current_lang(self):
        langs = [['en_US', 'English (US)'], ['fr_FR', 'French']]
        self.assertEqual(get_current_lang(langs, 'fr_FR'), ['fr_FR', 'French'])
        self.assertEqual(get_current_lang(langs, False), ['en_US', 'English (US)'])
        self.assertEqual(get_current_lang([], 'en_US'), ['', ''])


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):

    def test_user_can_write_own_refresh_option(self):
        user = new_test_user(
            self.env, login='refresh_self_user', groups='base.group_user')
        self.assertIn('is_refresh', user.SELF_WRITEABLE_FIELDS)
        user.with_user(user).write({'is_refresh': True})
        self.assertTrue(user.is_refresh)


@tagged('post_install', '-at_install')
class TestPlusSessionInfo(HttpCase):

    def _session_info(self, login='admin'):
        self.authenticate(login, login)
        response = self.url_open(
            '/web/session/get_session_info',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': {}}),
            headers={'Content-Type': 'application/json'})
        return response.json()['result']

    def _set_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(
            'backend_theme_infinito_plus.%s' % key, value)

    def test_font_false_values_are_normalised(self):
        for value in ('False', 'false', '0', ''):
            self._set_param('font', value)
            res = self._session_info()
            self.assertFalse(res['infinitoGoogleFont'], value)

    def test_font_id_is_returned(self):
        self._set_param('font', '7')
        res = self._session_info()
        self.assertEqual(res['infinitoGoogleFont'], '7')

    def test_session_info_plus_values(self):
        self._set_param('animation_plus', 'Scale')
        self._set_param('chatterbox_position', 'Top Left')
        self._set_param('is_refresh', 'True')
        res = self._session_info()
        self.assertEqual(res['infinitoAnimation'], 'Scale')
        self.assertEqual(res['chatBoxPosition'], 'Top Left')
        self.assertIn('currentLang', res)
        self.assertTrue(res['availableLanguages'])
        self.assertIn('infinitoRefresh', res)

    def test_refresh_follows_the_global_setting(self):
        self._set_param('is_refresh', 'True')
        self.assertTrue(self._session_info()['infinitoRefresh'])
        self._set_param('is_refresh', 'False')
        self.assertFalse(self._session_info()['infinitoRefresh'])

    def test_user_refresh_follows_own_setting(self):
        user = new_test_user(
            self.env, login='refresh_user', groups='base.group_user')
        self.env['ir.config_parameter'].sudo().set_param(
            'backend_theme_infinito.is_user_edit', True)
        self._set_param('is_refresh', 'True')
        user.write({'is_refresh': False})
        self.assertFalse(self._session_info('refresh_user')['infinitoRefresh'])
        user.write({'is_refresh': True})
        self.assertTrue(self._session_info('refresh_user')['infinitoRefresh'])