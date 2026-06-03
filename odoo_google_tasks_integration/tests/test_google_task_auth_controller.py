# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<http://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.odoo_google_tasks_integration.controllers.odoo_google_tasks_integration import (
    GoogleTaskAuth,
)


class GoogleTaskAuthControllerTestCase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env.ref(
            'odoo_google_tasks_integration.project_google_credential_data'
        )
        cls.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_redirect_uri': 'http://localhost:8069/google_task_authentication',
            'hangout_company_access_token': 'access-token',
            'hangout_company_refresh_token': 'refresh-token',
        })

    def _make_response(self, status_code=200, payload=None, text=''):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = payload or {}
        response.text = text
        return response


@tagged('-at_install', 'post_install')
class TestGoogleTaskAuthController(GoogleTaskAuthControllerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = GoogleTaskAuth()

    def _make_request(self):
        return SimpleNamespace(env=self.env)

    def _response_text(self, response):
        if hasattr(response, 'get_data'):
            return response.get_data(as_text=True)
        return response

    def test_get_auth_code_exchanges_code_and_stores_tokens(self):
        response = self._make_response(
            payload={
                'access_token': 'controller-access-token',
                'expires_in': 3600,
            },
        )

        with patch(
            'odoo.addons.odoo_google_tasks_integration.controllers'
            '.odoo_google_tasks_integration.http.request',
            self._make_request(),
        ), patch(
            'odoo.addons.odoo_google_tasks_integration.controllers'
            '.odoo_google_tasks_integration.requests.post',
            return_value=response,
        ) as post:
            result = self.controller.get_auth_code(code='auth-code')

        self.assertEqual(
            self._response_text(result),
            'Authentication Success. You can close this window.',
        )
        self.assertEqual(
            self.credential.hangout_company_authorization_code,
            'auth-code',
        )
        self.assertEqual(
            self.credential.hangout_company_access_token,
            'controller-access-token',
        )
        self.assertEqual(
            self.credential.hangout_company_refresh_token,
            'controller-access-token',
        )
        self.assertEqual(post.call_args.kwargs['data']['code'], 'auth-code')
        self.assertEqual(post.call_args.kwargs['timeout'], 20)

    def test_get_auth_code_raises_when_google_returns_no_access_token(self):
        response = self._make_response(payload={'error': 'invalid_grant'})

        with patch(
            'odoo.addons.odoo_google_tasks_integration.controllers'
            '.odoo_google_tasks_integration.http.request',
            self._make_request(),
        ), patch(
            'odoo.addons.odoo_google_tasks_integration.controllers'
            '.odoo_google_tasks_integration.requests.post',
            return_value=response,
        ), self.assertRaises(UserError):
            self.controller.get_auth_code(code='bad-code')
