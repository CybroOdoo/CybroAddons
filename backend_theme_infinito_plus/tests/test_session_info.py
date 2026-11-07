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

from ..models.utils import set_param

ROUTE = '/web/session/get_session_info'


@tagged('post_install', '-at_install')
class TestSessionInfo(HttpCase):

    def _session_info(self):
        response = self.url_open(ROUTE, json={
            'jsonrpc': '2.0', 'method': 'call', 'params': {}})
        return response.json()['result']

    def test_internal_user_gets_options(self):
        new_test_user(self.env, login='int_user', groups='base.group_user')
        set_param(self.env, 'backend_theme_infinito_plus.chatterbox_position',
                  'Top Left')
        set_param(self.env, 'backend_theme_infinito_plus.animation_plus',
                  'Scale')
        self.authenticate('int_user', 'int_user')
        info = self._session_info()
        self.assertEqual(info['chatBoxPosition'], 'Top Left')
        self.assertEqual(info['infinitoAnimation'], 'Scale')
        self.assertFalse(info['infinitoRefresh'])
        self.assertIn('currentLang', info)
        self.assertIn('availableLanguages', info)

    def test_refresh_from_user_flag(self):
        user = new_test_user(
            self.env, login='int_user', groups='base.group_user')
        user.is_refresh = True
        self.authenticate('int_user', 'int_user')
        self.assertTrue(self._session_info()['infinitoRefresh'])

    def test_refresh_from_global_param(self):
        new_test_user(self.env, login='int_user', groups='base.group_user')
        set_param(self.env, 'backend_theme_infinito_plus.is_refresh', True)
        self.authenticate('int_user', 'int_user')
        self.assertTrue(self._session_info()['infinitoRefresh'])

    def test_portal_user_gets_no_theme_options(self):
        new_test_user(self.env, login='portal_user', groups='base.group_portal')
        self.authenticate('portal_user', 'portal_user')
        info = self._session_info()
        self.assertNotIn('infinitoRefresh', info)
        self.assertNotIn('chatBoxPosition', info)
        # language info is added for every user
        self.assertIn('currentLang', info)