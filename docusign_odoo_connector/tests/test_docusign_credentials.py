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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestDocuSignCredentials(TransactionCase):
    """Unit tests for docusign.credentials model in models/docusign_credentials.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.att_1 = cls.env['ir.attachment'].create({
            'name': 'key1.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nMOCK1\n-----END RSA PRIVATE KEY-----",
        })
        cls.att_2 = cls.env['ir.attachment'].create({
            'name': 'key2.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nMOCK2\n-----END RSA PRIVATE KEY-----",
        })
        cls.credentials = cls.env['docusign.credentials'].create({
            'name': 'Test Credentials',
            'integrator_key': 'test-int-key-123',
            'account_id_data': 'test-account-id-456',
            'user_id_data': 'test-user-id-789',
            'private_key_ids': [Command.link(cls.att_1.id)],
            'company_id': cls.env.company.id,
        })

    def test_01_create_credentials_valid(self):
        """Test creating docusign.credentials record with valid single attachment."""
        self.assertEqual(self.credentials.name, 'Test Credentials')
        self.assertEqual(self.credentials.integrator_key, 'test-int-key-123')
        self.assertEqual(self.credentials.account_id_data, 'test-account-id-456')
        self.assertEqual(self.credentials.user_id_data, 'test-user-id-789')
        self.assertEqual(len(self.credentials.private_key_ids), 1)

    def test_02_multiple_private_key_ids_constraint(self):
        """Test constraint preventing multiple RSA key attachments."""
        with self.assertRaises(ValidationError):
            self.env['docusign.credentials'].create({
                'name': 'Invalid Multi Key',
                'integrator_key': 'int-key',
                'account_id_data': 'acc-id',
                'user_id_data': 'user-id',
                'private_key_ids': [Command.link(self.att_1.id), Command.link(self.att_2.id)],
            })

    def test_03_write_multiple_private_keys_constraint(self):
        """Test constraint when updating an existing record with a second key."""
        with self.assertRaises(ValidationError):
            self.credentials.write({
                'private_key_ids': [Command.link(self.att_2.id)],
            })

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign', return_value=200)
    def test_04_action_test_credentials_success(self, mock_action_login):
        """Test action_test_credentials when connection is successful (HTTP 200)."""
        action = self.credentials.action_test_credentials()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action.get('params', {}).get('type'), 'success')
        self.assertIn('Successful', action.get('params', {}).get('message', ''))
        mock_action_login.assert_called_once_with(
            self.credentials.user_id_data,
            self.credentials.account_id_data,
            self.credentials.integrator_key,
            self.credentials.private_key_ids,
            environment=self.credentials.environment,
        )

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign', return_value=401)
    def test_05_action_test_credentials_failure(self, mock_action_login):
        """Test action_test_credentials raises UserError when login fails."""
        with self.assertRaises(UserError):
            self.credentials.action_test_credentials()

    def test_06_check_private_key_ids_constraint(self):
        """Test _check_private_key_ids raises ValidationError when > 1 attachment is linked."""
        att_1 = self.env['ir.attachment'].create({'name': 'key1.pem', 'raw': b'key1'})
        att_2 = self.env['ir.attachment'].create({'name': 'key2.pem', 'raw': b'key2'})
        with self.assertRaises(ValidationError):
            self.credentials.write({
                'private_key_ids': [Command.set([att_1.id, att_2.id])]
            })

    def test_07_environment_selection_and_webhook_secret(self):
        """Test default environment is 'demo' and can be set to 'production' with webhook_secret."""
        self.assertEqual(self.credentials.environment, 'demo')
        self.credentials.write({
            'environment': 'production',
            'webhook_secret': 'test-secret-key-xyz',
        })
        self.assertEqual(self.credentials.environment, 'production')
        self.assertEqual(self.credentials.webhook_secret, 'test-secret-key-xyz')
