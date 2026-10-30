# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from unittest.mock import Mock, patch

from odoo.exceptions import AccessDenied
from odoo.tests import TransactionCase, new_test_user, tagged

REQUEST_PATH = 'odoo.addons.login_user_detail.models.res_users.request'


@tagged('post_install', '-at_install')
class TestResUsers(TransactionCase):
    """ Test cases for the login logging added to res.users """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login='login_detail_user', password='login_detail_pwd',
            name='Login Detail User')
        cls.user_agent_env = {'interactive': True}

    def _login(self, password='login_detail_pwd'):
        """ Log in through res.users._login, as the web login does """
        return self.env['res.users']._login({
            'type': 'password',
            'login': 'login_detail_user',
            'password': password,
        }, self.user_agent_env)

    def _login_details(self):
        return self.env['login.detail'].search(
            [('user_id', '=', self.user.id)])

    def _mock_request(self, environ):
        mock_request = Mock()
        mock_request.httprequest.environ = environ
        return patch(REQUEST_PATH, mock_request)

    def test_successful_login_creates_login_detail(self):
        """ A valid login stores the user name and the request IP """
        with self._mock_request({'REMOTE_ADDR': '192.168.1.100'}):
            auth_info = self._login()
        self.assertEqual(auth_info['uid'], self.user.id)
        login_record = self._login_details()
        self.assertEqual(len(login_record), 1)
        self.assertEqual(login_record.name, 'Login Detail User')
        self.assertEqual(login_record.ip_address, '192.168.1.100')
        self.assertTrue(login_record.date_time)

    def test_missing_remote_addr_stores_empty_ip(self):
        """ A request without REMOTE_ADDR still logs the login """
        with self._mock_request({}):
            self._login()
        login_record = self._login_details()
        self.assertEqual(len(login_record), 1)
        self.assertFalse(login_record.ip_address)

    def test_login_without_request_is_logged(self):
        """ A login outside an HTTP request is logged without an IP """
        auth_info = self._login()
        self.assertEqual(auth_info['uid'], self.user.id)
        login_record = self._login_details()
        self.assertEqual(len(login_record), 1)
        self.assertFalse(login_record.ip_address)

    def test_each_login_creates_a_record(self):
        """ Every login adds its own record to the history """
        with self._mock_request({'REMOTE_ADDR': '10.0.0.1'}):
            self._login()
        with self._mock_request({'REMOTE_ADDR': '10.0.0.2'}):
            self._login()
        self.assertCountEqual(self._login_details().mapped('ip_address'),
                              ['10.0.0.1', '10.0.0.2'])

    def test_wrong_password_is_not_logged(self):
        """ A failed login raises AccessDenied and creates no record """
        with self._mock_request({'REMOTE_ADDR': '192.168.1.100'}), \
                self.assertRaises(AccessDenied):
            self._login(password='wrong_password')
        self.assertFalse(self._login_details())

    def test_password_confirmation_is_not_logged(self):
        """ Re-confirming the password (identity check) is not a login """
        with self._mock_request({'REMOTE_ADDR': '192.168.1.100'}):
            self.user.with_user(self.user)._check_credentials(
                {'type': 'password', 'password': 'login_detail_pwd'},
                self.user_agent_env)
        self.assertFalse(self._login_details())
