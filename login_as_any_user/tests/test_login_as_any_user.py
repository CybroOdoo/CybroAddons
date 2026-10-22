# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.exceptions import AccessError
from odoo.tests import HttpCase, JsonRpcException, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestLoginAsAnyUser(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = new_test_user(
            cls.env,
            login='test_switch_admin',
            groups='base.group_system',
            password='test_switch_admin',
        )
        cls.internal_user = new_test_user(
            cls.env,
            login='test_switch_internal',
            groups='base.group_user',
            password='test_switch_internal',
        )

    def _get_session_uid(self):
        """Return the uid of the current HTTP session."""
        return self.make_jsonrpc_request(
            '/web/session/get_session_info')['uid']

    def _switch_to(self, user):
        """Create the wizard and switch to the given user through RPC."""
        wizard_id = self.make_jsonrpc_request('/web/dataset/call_kw', {
            'model': 'user.selection',
            'method': 'create',
            'args': [{'user_id': user.id}],
            'kwargs': {},
        })
        return self.make_jsonrpc_request('/web/dataset/call_button', {
            'model': 'user.selection',
            'method': 'action_switch',
            'args': [wizard_id],
            'kwargs': {},
        })

    def test_admin_can_switch_and_switch_back(self):
        """An administrator can log in as another user and switch back."""
        self.authenticate(self.admin_user.login, self.admin_user.login)
        self.assertIs(self.make_jsonrpc_request('/switch/user'), True)

        self._switch_to(self.internal_user)
        self.assertEqual(self._get_session_uid(), self.internal_user.id)
        self.assertIs(self.make_jsonrpc_request('/switch/user'), False)

        self.make_jsonrpc_request('/switch/admin')
        self.assertEqual(self._get_session_uid(), self.admin_user.id)

    def test_non_admin_cannot_switch_through_rpc(self):
        """A non-admin user cannot use the wizard through RPC."""
        self.authenticate(self.internal_user.login, self.internal_user.login)
        self.assertIs(self.make_jsonrpc_request('/switch/user'), False)
        with self.assertRaises(JsonRpcException):
            self._switch_to(self.admin_user)
        self.assertEqual(self._get_session_uid(), self.internal_user.id)

    def test_action_switch_requires_admin(self):
        """action_switch itself refuses non-admin users."""
        wizard = self.env['user.selection'].create({
            'user_id': self.admin_user.id,
        })
        with self.assertRaises(AccessError):
            wizard.with_user(self.internal_user).action_switch()

    def test_switch_admin_without_previous_user(self):
        """Switching back without a previous admin keeps the session."""
        self.authenticate(self.internal_user.login, self.internal_user.login)
        self.make_jsonrpc_request('/switch/admin')
        self.assertEqual(self._get_session_uid(), self.internal_user.id)
