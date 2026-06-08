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

import datetime
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProjectCredential(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credential = cls.env['project.credential'].create({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_redirect_uri': 'http://localhost/google_task_authentication',
            'hangout_company_refresh_token': 'refresh-token',
        })

    def test_get_access_token_uses_existing_token(self):
        self.credential.write({
            'hangout_company_access_token': 'existing-token',
            'hangout_company_access_token_expiry': fields.Datetime.now() + datetime.timedelta(hours=1),
        })

        token = self.credential._get_access_token()

        self.assertEqual(token, 'existing-token')

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_credential.ProjectCredential.action_google_task_company_refresh_token')
    def test_get_access_token_refreshes_expired_token(self, mock_refresh):
        self.credential.write({
            'hangout_company_access_token': False,
            'hangout_company_access_token_expiry': fields.Datetime.now() - datetime.timedelta(hours=1),
        })

        def _refresh():
            self.credential.hangout_company_access_token = 'refreshed-token'

        mock_refresh.side_effect = _refresh

        token = self.credential._get_access_token()

        self.assertEqual(token, 'refreshed-token')
        self.assertTrue(mock_refresh.called)

    def test_action_google_task_company_authenticate_requires_client(self):
        self.credential.hangout_client = False

        with self.assertRaises(ValidationError):
            self.credential.action_google_task_company_authenticate()

    def test_action_google_task_company_authenticate_requires_redirect_uri(self):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_redirect_uri': False,
        })

        with self.assertRaises(ValidationError):
            self.credential.action_google_task_company_authenticate()

    def test_action_google_task_company_authenticate_returns_url_action(self):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_redirect_uri': 'http://localhost/google_task_authentication',
        })

        action = self.credential.action_google_task_company_authenticate()

        self.assertEqual(action['type'], 'ir.actions.act_url')
        self.assertEqual(action['target'], 'new')
        self.assertIn('client_id=client-id', action['url'])
        self.assertIn('https://www.googleapis.com/auth/tasks', action['url'])

    def test_refresh_token_requires_client(self):
        self.credential.write({
            'hangout_client': False,
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': 'refresh-token',
        })

        with self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()

    def test_refresh_token_requires_client_secret(self):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': False,
            'hangout_company_refresh_token': 'refresh-token',
        })

        with self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()

    def test_refresh_token_requires_refresh_token(self):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': False,
        })

        with self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_credential.requests.post')
    def test_refresh_token_success(self, mock_post):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': 'refresh-token',
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'access_token': 'new-access-token',
            'expires_in': 1800,
        }
        mock_post.return_value = mock_response

        action = self.credential.action_google_task_company_refresh_token()

        self.assertEqual(self.credential.hangout_company_access_token, 'new-access-token')
        self.assertEqual(action['tag'], 'display_notification')
        self.assertEqual(action['params']['type'], 'success')

    @patch('odoo.addons.odoo_google_tasks_integration.models.project_credential.requests.post')
    def test_refresh_token_failure(self, mock_post):
        self.credential.write({
            'hangout_client': 'client-id',
            'hangout_client_secret': 'client-secret',
            'hangout_company_refresh_token': 'refresh-token',
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_post.return_value = mock_response

        with self.assertRaises(UserError):
            self.credential.action_google_task_company_refresh_token()
