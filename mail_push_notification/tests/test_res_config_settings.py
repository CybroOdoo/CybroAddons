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
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test cases for res.config.settings in mail_push_notification."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.valid_firebase_config = {
            'push_notification': True,
            'project_id_firebase': 'demo-firebase-project',
            'private_key_ref': 'private-key-ref-12345',
            'private_key': '-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7...\\n-----END PRIVATE KEY-----\\n',
            'client_email': 'firebase-adminsdk-test@demo-firebase-project.iam.gserviceaccount.com',
            'client_id_firebase': '109876543210987654321',
            'client_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-test',
        }

    def test_test_connection(self):
        """Test test_connection function on res.config.settings under all scenarios:
        1. When push_notification is disabled.
        2. When push_notification is enabled and credentials are valid.
        3. When push_notification is enabled but initialization raises an exception.
        4. When _apps is already initialized.
        """
        # Case 1: push_notification is disabled -> should return False
        self.company.write({'push_notification': False})
        settings = self.env['res.config.settings'].create({})
        res_disabled = settings.test_connection()
        self.assertFalse(
            res_disabled,
            "test_connection() should return False when push_notification is disabled."
        )

        # Case 2: push_notification is enabled and Firebase initialization succeeds
        self.company.write(self.valid_firebase_config)
        settings = self.env['res.config.settings'].create({})

        patch_target_apps = 'odoo.addons.mail_push_notification.models.res_config_settings._apps'
        patch_target_cred = 'odoo.addons.mail_push_notification.models.res_config_settings.credentials.Certificate'
        patch_target_init = 'odoo.addons.mail_push_notification.models.res_config_settings.initialize_app'

        with patch.dict(patch_target_apps, {}, clear=True), \
             patch(patch_target_cred) as mock_cert, \
             patch(patch_target_init) as mock_init:
            mock_cert.return_value = MagicMock()
            res_success = settings.test_connection()

            mock_cert.assert_called_once()
            mock_init.assert_called_once_with(mock_cert.return_value)
            self.assertEqual(res_success.get('type'), 'ir.actions.client')
            self.assertEqual(res_success.get('tag'), 'display_notification')
            self.assertEqual(res_success.get('params', {}).get('type'), 'success')

        # Case 3: push_notification is enabled but Firebase initialization raises an exception
        with patch.dict(patch_target_apps, {}, clear=True), \
             patch(patch_target_cred, side_effect=Exception("Invalid private key format")):
            res_error = settings.test_connection()

            self.assertEqual(res_error.get('type'), 'ir.actions.client')
            self.assertEqual(res_error.get('tag'), 'display_notification')
            self.assertEqual(res_error.get('params', {}).get('type'), 'danger')
            self.assertIn("Failed to connect with firebase", res_error.get('params', {}).get('message', ''))
            self.assertIn("Invalid private key format", res_error.get('params', {}).get('message', ''))

        # Case 4: _apps is already initialized -> initialize_app should not be called again
        with patch.dict(patch_target_apps, {'[DEFAULT]': MagicMock()}):
            with patch(patch_target_init) as mock_init:
                res_already_init = settings.test_connection()
                mock_init.assert_not_called()
                self.assertEqual(res_already_init.get('params', {}).get('type'), 'success')

