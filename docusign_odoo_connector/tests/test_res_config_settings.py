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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettingsDocuSign(TransactionCase):
    """Unit tests for res.config.settings DocuSign configuration in models/res_config_settings.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_att = cls.env['ir.attachment'].create({
            'name': 'config_key.pem',
            'type': 'binary',
            'raw': b"-----BEGIN RSA PRIVATE KEY-----\nCONFIG\n-----END RSA PRIVATE KEY-----",
        })

    def test_01_set_and_get_values(self):
        """Test setting DocuSign configuration values creates/updates docusign.credentials."""
        settings = self.env['res.config.settings'].create({
            'docusign_integrator_key': 'cfg-int-key',
            'docusign_account_id_data': 'cfg-acc-id',
            'docusign_user_id_data': 'cfg-user-id',
            'docusign_private_key_ids': [Command.link(self.test_att.id)],
            'docusign_reminder_days': 5,
        })
        with patch.object(type(self.env['ir.ui.view']), '_check_xml'):
            settings.set_values()

        # Check that docusign.credentials was updated/created
        credential = self.env['docusign.credentials'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        self.assertTrue(credential)
        self.assertEqual(credential.integrator_key, 'cfg-int-key')
        self.assertEqual(credential.account_id_data, 'cfg-acc-id')
        self.assertEqual(credential.user_id_data, 'cfg-user-id')
        self.assertIn(self.test_att, credential.private_key_ids)

        # Check get_values loads them back
        new_settings = self.env['res.config.settings'].new({})
        values = new_settings.get_values()
        self.assertEqual(values.get('docusign_integrator_key'), 'cfg-int-key')
        self.assertEqual(values.get('docusign_account_id_data'), 'cfg-acc-id')
        self.assertEqual(values.get('docusign_user_id_data'), 'cfg-user-id')

    def test_02_action_test_credentials_missing_info(self):
        """Test action_test_credentials raises UserError when credentials are missing."""
        # Unlink any existing credentials for clean test
        self.env['docusign.credentials'].search([]).unlink()

        settings = self.env['res.config.settings'].create({
            'docusign_integrator_key': 'int-key',
            # missing user_id, account_id, private_key
        })
        with self.assertRaises(UserError):
            settings.action_test_credentials()

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign', return_value=200)
    def test_03_action_test_credentials_success(self, mock_action_login):
        """Test action_test_credentials returns success when fields are directly provided on settings."""
        settings = self.env['res.config.settings'].create({
            'docusign_environment': 'demo',
            'docusign_integrator_key': 'direct-int-key',
            'docusign_account_id_data': 'direct-acc-id',
            'docusign_user_id_data': 'direct-user-id',
            'docusign_private_key_ids': [Command.link(self.test_att.id)],
        })
        action = settings.action_test_credentials()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action.get('params', {}).get('type'), 'success')
        mock_action_login.assert_called_once_with(
            'direct-user-id',
            'direct-acc-id',
            'direct-int-key',
            settings.docusign_private_key_ids,
            environment='demo'
        )

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign', return_value=401)
    def test_04_action_test_credentials_failure(self, mock_action_login):
        """Test action_test_credentials raises UserError when login fails."""
        settings = self.env['res.config.settings'].create({
            'docusign_integrator_key': 'bad-int-key',
            'docusign_account_id_data': 'bad-acc-id',
            'docusign_user_id_data': 'bad-user-id',
            'docusign_private_key_ids': [Command.link(self.test_att.id)],
        })
        with self.assertRaises(UserError):
            settings.action_test_credentials()

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign', return_value=200)
    def test_05_action_test_credentials_fallback_to_existing_record(self, mock_action_login):
        """Test action_test_credentials falls back to saved docusign.credentials when fields in transient settings are blank."""
        cred = self.env['docusign.credentials'].create({
            'name': 'Saved Cred',
            'integrator_key': 'saved-int-key',
            'account_id_data': 'saved-acc-id',
            'user_id_data': 'saved-user-id',
            'private_key_ids': [Command.link(self.test_att.id)],
            'company_id': self.env.company.id,
        })
        blank_settings = self.env['res.config.settings'].create({})
        action = blank_settings.action_test_credentials()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'display_notification')
        self.assertEqual(action.get('params', {}).get('type'), 'success')

    def test_06_config_settings_environment_and_webhook_secret(self):
        """Test configuring environment and webhook_secret in settings syncs with credentials."""
        settings = self.env['res.config.settings'].create({
            'docusign_environment': 'production',
            'docusign_webhook_secret': 'super-secret-hmac-key',
            'docusign_integrator_key': 'prod-int-key',
            'docusign_account_id_data': 'prod-acc-id',
            'docusign_user_id_data': 'prod-user-id',
            'docusign_private_key_ids': [Command.link(self.test_att.id)],
        })
        with patch.object(type(self.env['ir.ui.view']), '_check_xml'):
            settings.set_values()

        cred = self.env['docusign.credentials'].search([
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        self.assertEqual(cred.environment, 'production')
        self.assertEqual(cred.webhook_secret, 'super-secret-hmac-key')

        new_settings = self.env['res.config.settings'].new({})
        vals = new_settings.get_values()
        self.assertEqual(vals.get('docusign_environment'), 'production')
        self.assertEqual(vals.get('docusign_webhook_secret'), 'super-secret-hmac-key')
