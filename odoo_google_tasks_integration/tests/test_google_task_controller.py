# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.odoo_google_tasks_integration.controllers import odoo_google_tasks_integration as controller_module
from odoo.addons.odoo_google_tasks_integration.controllers.odoo_google_tasks_integration import (
    GoogleTaskAuth,
)


@tagged('post_install', '-at_install')
class TestGoogleTaskController(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = GoogleTaskAuth()
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data'
        )
        cls.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_redirect_uri': 'http://localhost/google_task_authentication',
        })

    @patch('odoo.addons.odoo_google_tasks_integration.controllers.odoo_google_tasks_integration.requests.post')
    @patch.object(controller_module, 'http')
    def test_get_auth_code_success(self, mock_http, mock_post):
        mock_http.request = SimpleNamespace(env=self.env)
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'access-token',
            'expires_in': 3600,
        }
        mock_post.return_value = mock_response

        result = self.controller.get_auth_code(code='auth-code')

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_data(as_text=True), "Authentication Success. You can close this window.")
        self.assertEqual(self.credential.hangout_company_authorization_code, 'auth-code')
        self.assertEqual(self.credential.hangout_company_access_token, 'access-token')
        self.assertEqual(self.credential.hangout_company_refresh_token, 'access-token')

    @patch('odoo.addons.odoo_google_tasks_integration.controllers.odoo_google_tasks_integration._', lambda message: message)
    @patch('odoo.addons.odoo_google_tasks_integration.controllers.odoo_google_tasks_integration.requests.post')
    @patch.object(controller_module, 'http')
    def test_get_auth_code_invalid_token_response(self, mock_http, mock_post):
        mock_http.request = SimpleNamespace(env=self.env)
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.assertRaises(UserError):
            self.controller.get_auth_code(code='bad-code')

    @patch.object(controller_module, 'http')
    def test_get_auth_code_without_code_returns_none(self, mock_http):
        mock_http.request = SimpleNamespace(env=self.env)

        result = self.controller.get_auth_code()

        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.get_data(as_text=True), '')
