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
from unittest.mock import patch

from odoo.tests import HttpCase, new_test_user, tagged

from .common import POST, mock_response


@tagged('post_install', '-at_install')
class TestGoogleTaskController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data')
        cls.credential.write({'hangout_client': 'client-id',
                              'hangout_client_secret': 'client-secret'})
        cls.manager = new_test_user(
            cls.env, 'gtask_manager',
            groups='base.group_user,project.group_project_manager')
        new_test_user(cls.env, 'gtask_user',
                      groups='base.group_user,project.group_project_user')

    def _state(self, user):
        return self.credential.with_user(user)._get_oauth_state()

    @patch(POST)
    def test_authentication_success(self, mock_post):
        mock_post.return_value = mock_response(json={
            'access_token': 'access', 'refresh_token': 'refresh',
            'expires_in': 3599})
        self.authenticate('gtask_manager', 'gtask_manager')
        response = self.url_open(
            '/google_task_authentication?code=abc&state='
            + self._state(self.manager))
        self.assertIn('Authentication Success', response.text)
        self.assertEqual(self.credential.hangout_company_refresh_token,
                         'refresh')

    @patch(POST)
    def test_authentication_rejects_bad_state(self, mock_post):
        self.authenticate('gtask_manager', 'gtask_manager')
        response = self.url_open(
            '/google_task_authentication?code=abc&state=forged')
        self.assertIn('Invalid authentication request', response.text)
        mock_post.assert_not_called()

    @patch(POST)
    def test_authentication_needs_project_manager(self, mock_post):
        self.authenticate('gtask_user', 'gtask_user')
        response = self.url_open('/google_task_authentication?code=abc')
        self.assertEqual(response.status_code, 404)
        mock_post.assert_not_called()

    @patch(POST)
    def test_authentication_needs_login(self, mock_post):
        response = self.url_open('/google_task_authentication?code=abc')
        self.assertNotIn('Authentication Success', response.text)
        mock_post.assert_not_called()
