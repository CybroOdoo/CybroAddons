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

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user

PARAM = 'backend_theme_infinito_plus.%s'
STYLES_URL = '/backend_theme_infinito_plus/dynamic_styles.css'


@tagged('post_install', '-at_install')
class TestPlusControllers(HttpCase):

    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()

    def _rpc(self, route, params=None):
        response = self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': params or {}}),
            headers={'Content-Type': 'application/json'})
        return response.json()

    def _vals(self, **kwargs):
        vals = {'infinitoRefresh': True, 'infinitoGoogleFont': 0,
                'chatBoxPosition': 'Bottom Left',
                'infinitoAnimation': 'Scale'}
        vals.update(kwargs)
        return {'args': [{'vals': vals}]}

    # ---- dynamic stylesheet (fonts and chatbox position) ----

    def test_stylesheet_has_chatbox_position(self):
        self.params.set_param(PARAM % 'chatterbox_position', 'Bottom Left')
        response = self.url_open(STYLES_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/css', response.headers['Content-Type'])
        self.assertIn('.o-mail-ChatWindow{left:10px!important;',
                      response.text)

    def test_stylesheet_has_selected_font(self):
        font = self.env['infinito.google.font'].create({
            'name': 'Lato', 'font': "@font-face { font-family: 'Lato'; }"})
        self.params.set_param(PARAM % 'font', str(font.id))
        response = self.url_open(STYLES_URL)
        self.assertIn("font-family: 'Lato', sans-serif !important",
                      response.text)

    def test_stylesheet_is_empty_without_settings(self):
        for key in ('chatterbox_position', 'animation_plus', 'font'):
            self.params.set_param(PARAM % key, False)
        response = self.url_open(STYLES_URL)
        self.assertEqual(response.text.strip(), '')

    # ---- saving the options (refresh, font, chatbox, animation) ----

    def test_admin_saves_global_settings(self):
        font = self.env['infinito.google.font'].create({'name': 'Lato'})
        self.authenticate('admin', 'admin')
        result = self._rpc('/theme_studio/set_advanced_data_plus',
                           self._vals(infinitoGoogleFont=font.id))
        self.assertEqual(result['result'], 'global')
        self.assertEqual(self.params.get_param(PARAM % 'font'), str(font.id))
        self.assertEqual(self.params.get_param(PARAM % 'chatterbox_position'),
                         'Bottom Left')
        self.assertEqual(self.params.get_param(PARAM % 'animation_plus'),
                         'Scale')
        self.assertEqual(self.params.get_param(PARAM % 'is_refresh'), 'True')

    def test_invalid_values_are_ignored(self):
        self.authenticate('admin', 'admin')
        self._rpc('/theme_studio/set_advanced_data_plus', self._vals(
            infinitoGoogleFont=999999, chatBoxPosition='Nowhere'))
        self.assertFalse(self.params.get_param(PARAM % 'font'))
        self.assertFalse(self.params.get_param(PARAM % 'chatterbox_position'))

    def test_save_without_values_does_nothing(self):
        self.authenticate('admin', 'admin')
        result = self._rpc('/theme_studio/set_advanced_data_plus',
                           {'args': [{}]})
        self.assertFalse(result['result'])

    def test_user_needs_user_edit_enabled(self):
        user = new_test_user(
            self.env, login='theme_plain_user', groups='base.group_user')
        self.authenticate('theme_plain_user', 'theme_plain_user')
        payload = self._vals()
        self.assertIn('error', self._rpc(
            '/theme_studio/set_advanced_data_plus', payload))
        self.params.set_param('backend_theme_infinito.is_user_edit', True)
        result = self._rpc('/theme_studio/set_advanced_data_plus', payload)
        self.assertEqual(result['result'], 'user')
        user.invalidate_recordset()
        self.assertTrue(user.is_refresh)
        self.assertFalse(self.params.get_param(PARAM % 'chatterbox_position'))

    # ---- language switch ----

    def test_set_user_lang(self):
        self.authenticate('admin', 'admin')
        result = self._rpc('/theme_studio_plus/set_user_lang',
                           {'lang': 'en_US'})
        self.assertTrue(result['result'])
        self.assertIn('error', self._rpc('/theme_studio_plus/set_user_lang',
                                         {'lang': 'zz_ZZ'}))

    # ---- reset ----

    def test_reset_requires_admin_and_clears(self):
        self.params.set_param(PARAM % 'chatterbox_position', 'Top Left')
        new_test_user(
            self.env, login='theme_reset_user', groups='base.group_user')
        self.authenticate('theme_reset_user', 'theme_reset_user')
        self.assertIn('error', self._rpc(
            '/theme_studio_plus/reset_to_default_style'))
        self.assertTrue(self.params.get_param(PARAM % 'chatterbox_position'))
        self.authenticate('admin', 'admin')
        self.assertTrue(self._rpc(
            '/theme_studio_plus/reset_to_default_style')['result'])
        self.assertFalse(self.params.get_param(PARAM % 'chatterbox_position'))

    def test_invalid_animation_is_ignored(self):
        self.authenticate('admin', 'admin')
        self._rpc('/theme_studio/set_advanced_data_plus',
                  self._vals(infinitoAnimation='Spin'))
        self.assertFalse(self.params.get_param(PARAM % 'animation_plus'))

    def test_non_numeric_font_id(self):
        self.authenticate('admin', 'admin')
        response = self.url_open(
            '/theme_studio/set_advanced_data_plus',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {
                'args': [{'vals': {'infinitoGoogleFont': 'abc'}}]}}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.json()['result'], 'global')
        self.assertFalse(self.env['ir.config_parameter'].sudo().get_param(
            'backend_theme_infinito_plus.font'))