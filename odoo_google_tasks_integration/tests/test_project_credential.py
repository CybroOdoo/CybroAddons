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
#############################################################################from unittest.mock import MagicMock, patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class ProjectCredentialTestCase(TransactionCase):

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
class TestProjectCredential(ProjectCredentialTestCase):

    def test_action_google_task_company_authenticate_requires_client(self):
        self.credential.hangout_client = False

        with self.assertRaises(ValidationError):
            self.credential.action_google_task_company_authenticate()

    def test_action_google_task_company_authenticate_returns_google_url(self):
        action = self.credential.action_google_task_company_authenticate()

        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['target'], 'new')
        self.assertIn('https://accounts.google.com/o/oauth2/v2/auth', action['url'])
        self.assertIn('client_id=client-id', action['url'])
        self.assertIn('redirect_uri=http://localhost:8069/google_task_authentication', action['url'])
        self.assertIn('https://www.googleapis.com/auth/tasks', action['url'])

    def test_action_google_task_company_refresh_token_requires_values(self):
        self.credential.hangout_company_refresh_token = False

        with self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()

    def test_action_google_task_company_refresh_token_updates_access_token(self):
        response = self._make_response(payload={'access_token': 'new-access-token'})

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_credential.requests.post',
            return_value=response,
        ) as post:
            self.credential.action_google_task_company_refresh_token()

        self.assertEqual(
            self.credential.hangout_company_access_token,
            'new-access-token',
        )
        post.assert_called_once()
        self.assertEqual(post.call_args.kwargs['timeout'], 20)
        self.assertEqual(post.call_args.kwargs['data']['grant_type'], 'refresh_token')

    def test_action_google_task_company_refresh_token_raises_on_error_payload(self):
        response = self._make_response(payload={'error': 'invalid_grant'})

        with patch(
            'odoo.addons.odoo_google_tasks_integration.models.project_credential.requests.post',
            return_value=response,
        ), self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()
