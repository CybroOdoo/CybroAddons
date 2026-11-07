# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import HttpCase, new_test_user, tagged

from ..models.utils import get_param, set_param

ROUTE_SAVE = '/theme_studio/set_advanced_data_plus'
ROUTE_RESET = '/theme_studio_plus/reset_to_default_style'
ROUTE_LANG = '/theme_studio_plus/set_user_lang'
ROUTE_CSS = '/backend_theme_infinito_plus/dynamic_styles.css'

VALS = {
    'infinitoRefresh': True,
    'chatBoxPosition': 'Bottom Left',
    'infinitoAnimation': 'Scale',
    'infinitoGoogleFont': 0,
}


@tagged('post_install', '-at_install')
class TestThemeStudioPlus(HttpCase):

    def _rpc(self, route, params=None):
        response = self.url_open(route, json={
            'jsonrpc': '2.0', 'method': 'call', 'params': params or {}})
        self.assertEqual(response.status_code, 200)
        return response.json()

    def _param(self, name):
        return get_param(self.env, 'backend_theme_infinito_plus.' + name)

    # ---- admin: global options ----

    def test_admin_saves_global_options(self):
        self.authenticate('admin', 'admin')
        result = self._rpc(ROUTE_SAVE, {'args': [{'vals': VALS}]})
        self.assertEqual(result.get('result'), 'global')
        self.assertEqual(self._param('chatterbox_position'), 'Bottom Left')
        self.assertEqual(self._param('animation_plus'), 'Scale')
        self.assertTrue(self._param('is_refresh'))

    def test_invalid_values_are_ignored(self):
        self.authenticate('admin', 'admin')
        vals = dict(VALS, chatBoxPosition='Middle', infinitoAnimation='Spin',
                    infinitoGoogleFont='abc')
        self._rpc(ROUTE_SAVE, {'args': [{'vals': vals}]})
        self.assertFalse(self._param('chatterbox_position'))
        self.assertFalse(self._param('animation_plus'))
        self.assertFalse(self._param('font'))

    def test_unknown_font_id_is_ignored(self):
        self.authenticate('admin', 'admin')
        vals = dict(VALS, infinitoGoogleFont=999999)
        self._rpc(ROUTE_SAVE, {'args': [{'vals': vals}]})
        self.assertFalse(self._param('font'))

    def test_existing_font_is_saved(self):
        font = self.env['infinito.google.font'].create(
            {'name': 'Roboto', 'font': ''})
        self.authenticate('admin', 'admin')
        vals = dict(VALS, infinitoGoogleFont=font.id)
        self._rpc(ROUTE_SAVE, {'args': [{'vals': vals}]})
        self.assertEqual(self._param('font'), str(font.id))

    def test_malformed_payload(self):
        self.authenticate('admin', 'admin')
        for args in ([], [{}], [{'other': 1}]):
            result = self._rpc(ROUTE_SAVE, {'args': args})
            self.assertFalse(result.get('result'))
            self.assertNotIn('error', result)

    # ---- normal user: own refresh option only ----

    def test_user_cannot_save_when_user_edit_is_off(self):
        new_test_user(self.env, login='plain_user', groups='base.group_user')
        set_param(self.env, 'backend_theme_infinito.is_user_edit', False)
        self.authenticate('plain_user', 'plain_user')
        result = self._rpc(ROUTE_SAVE, {'args': [{'vals': VALS}]})
        self.assertIn('error', result)
        self.assertFalse(self._param('chatterbox_position'))

    def test_user_saves_only_own_refresh_when_user_edit_is_on(self):
        user = new_test_user(
            self.env, login='plain_user', groups='base.group_user')
        set_param(self.env, 'backend_theme_infinito.is_user_edit', True)
        self.authenticate('plain_user', 'plain_user')
        result = self._rpc(ROUTE_SAVE, {'args': [{'vals': VALS}]})
        self.assertEqual(result.get('result'), 'user')
        user.invalidate_recordset()
        self.assertTrue(user.is_refresh)
        # global options stay untouched
        self.assertFalse(self._param('chatterbox_position'))
        self.assertFalse(self._param('animation_plus'))

    # ---- reset ----

    def test_admin_reset(self):
        set_param(self.env, 'backend_theme_infinito_plus.chatterbox_position',
                  'Top Left')
        set_param(self.env, 'backend_theme_infinito_plus.animation_plus',
                  'Scale')
        self.authenticate('admin', 'admin')
        result = self._rpc(ROUTE_RESET)
        self.assertTrue(result.get('result'))
        self.assertFalse(self._param('chatterbox_position'))
        self.assertFalse(self._param('animation_plus'))
        self.assertFalse(self._param('font'))

    def test_user_cannot_reset(self):
        new_test_user(self.env, login='plain_user', groups='base.group_user')
        set_param(self.env, 'backend_theme_infinito_plus.animation_plus',
                  'Scale')
        self.authenticate('plain_user', 'plain_user')
        result = self._rpc(ROUTE_RESET)
        self.assertIn('error', result)
        self.assertEqual(self._param('animation_plus'), 'Scale')

    # ---- language ----

    def test_set_user_lang(self):
        user = new_test_user(
            self.env, login='lang_user', groups='base.group_user')
        self.authenticate('lang_user', 'lang_user')
        result = self._rpc(ROUTE_LANG, {'lang': 'en_US'})
        self.assertTrue(result.get('result'))
        user.invalidate_recordset()
        self.assertEqual(user.lang, 'en_US')

    def test_set_user_lang_not_installed(self):
        new_test_user(self.env, login='lang_user', groups='base.group_user')
        self.authenticate('lang_user', 'lang_user')
        result = self._rpc(ROUTE_LANG, {'lang': 'xx_XX'})
        self.assertIn('error', result)

    # ---- dynamic CSS ----

    def test_dynamic_css_with_chatbox_position(self):
        set_param(self.env, 'backend_theme_infinito_plus.chatterbox_position',
                  'Bottom Right')
        response = self.url_open(ROUTE_CSS)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/css', response.headers['Content-Type'])
        self.assertIn('no-store', response.headers['Cache-Control'])
        self.assertIn('.o-mail-ChatWindow{', response.text)
        self.assertIn('bottom:10px!important', response.text)
        self.assertIn('right:10px!important', response.text)

    def test_dynamic_css_empty_by_default(self):
        for key in ('font', 'chatterbox_position'):
            set_param(self.env, 'backend_theme_infinito_plus.' + key, False)
        response = self.url_open(ROUTE_CSS)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text.strip(), '')

    def test_dynamic_css_includes_active_font(self):
        font = self.env['infinito.google.font'].create(
            {'name': 'Roboto', 'font': '@font-face{font-family:Roboto;}'})
        set_param(self.env, 'backend_theme_infinito_plus.font', font.id)
        response = self.url_open(ROUTE_CSS)
        self.assertIn("font-family: 'Roboto', sans-serif", response.text)