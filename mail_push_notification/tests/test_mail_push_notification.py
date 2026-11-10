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
#############################################################################
import json
from unittest.mock import MagicMock, patch
from odoo.http import Response
from odoo.tests.common import HttpCase, tagged
from odoo.addons.mail_push_notification.controllers.mail_push_notification import MailPushNotification


@tagged('post_install', '-at_install')
class TestMailPushNotification(HttpCase):
    """Test suite for MailPushNotification controller in mail_push_notification:
    - _get_active_company
    - firebase_http
    - get_registration_tokens
    - send_datas
    - firebase_credentials
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = MailPushNotification()
        cls.company = cls.env.company
        cls.company.write({
            'push_notification': True,
            'api_key': 'test_api_key_123',
            'auth_domain': 'test.firebaseapp.com',
            'project_id_firebase': 'test-project-123',
            'storage_bucket': 'test.appspot.com',
            'messaging_sender_id_firebase': '1234567890',
            'app_id_firebase': '1:1234567890:web:abcdef',
            'measurement_id_firebase': 'G-ABC123XYZ',
            'vapid': 'test_vapid_key_456',
        })

        groups_field = 'group_ids' if 'group_ids' in cls.env['res.users']._fields else 'groups_id'
        cls.user_test = cls.env['res.users'].create({
            'name': 'Test Push User',
            'login': 'test_push_user',
            'email': 'push_user@example.com',
            groups_field: [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test__get_active_company(self):
        """Test _get_active_company:
        1. When request.env.company has push_notification enabled, returns request.env.company.
        2. When request.env.company is disabled, searches for another company with push enabled.
        3. When no company has push enabled, returns empty recordset.
        """
        # Case 1: Active company has push_notification = True
        self.company.push_notification = True
        mock_request = MagicMock()
        mock_request.env.company = self.company
        mock_request.env.__getitem__.return_value = self.env['res.company']

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            active_comp = self.controller._get_active_company()
            self.assertEqual(active_comp, self.company)

        # Case 2: Active company disabled, secondary company enabled
        company_secondary = self.env['res.company'].create({
            'name': 'Secondary Company',
            'push_notification': True,
        })
        self.company.push_notification = False
        mock_request.env.company = self.company
        mock_request.env.__getitem__.return_value = self.env['res.company']

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            active_comp = self.controller._get_active_company()
            self.assertTrue(active_comp.push_notification)

        # Case 3: All companies disabled
        company_secondary.push_notification = False
        self.company.push_notification = False
        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            active_comp = self.controller._get_active_company()
            self.assertFalse(active_comp)

        # Restore
        self.company.push_notification = True

    def test_get_active_company(self):
        """Alias for test__get_active_company."""
        self.test__get_active_company()

    def test_firebase_http(self):
        """Test firebase_http route (/firebase-messaging-sw.js):
        1. When push_notification is enabled, returns JS containing firebaseConfig.
        2. When push_notification is disabled, returns fallback service worker script.
        """
        self.company.write({'push_notification': True})
        mock_request = MagicMock()
        mock_request.env.company = self.company
        mock_request.env.__getitem__.return_value = self.env['res.company']
        mock_request.make_response = lambda text, headers=None: Response(text, headers=headers)

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            # 1. Enabled scenario
            res_enabled = self.controller.firebase_http()
            self.assertEqual(res_enabled.status_code, 200)
            res_text = res_enabled.get_data(as_text=True) if hasattr(res_enabled, 'get_data') else str(res_enabled)
            self.assertIn('firebase.initializeApp(firebaseConfig)', res_text)
            self.assertIn('test_api_key_123', res_text)
            self.assertIn('test-project-123', res_text)

            # 2. Disabled scenario
            self.company.write({'push_notification': False})
            res_disabled = self.controller.firebase_http()
            self.assertEqual(res_disabled.status_code, 200)
            res_disabled_text = res_disabled.get_data(as_text=True) if hasattr(res_disabled, 'get_data') else str(res_disabled)
            self.assertNotIn('firebase.initializeApp', res_disabled_text)
            self.assertIn('caches.match', res_disabled_text)

        self.company.write({'push_notification': True})

    def test_get_registration_tokens(self):
        """Test get_registration_tokens route (/push_notification):
        1. When a new token is provided, creates a push.notification record for current user.
        2. When an existing token belongs to another user, does not touch other user's record and registers for current user.
        3. When token is already registered to the current user, keeps record unchanged.
        4. When name is None/empty, does nothing and returns None.
        """
        token_a = 'fcm_test_token_alpha'
        token_b = 'fcm_test_token_beta'

        # Clean existing test tokens
        self.env['push.notification'].search([('register_id', 'in', [token_a, token_b])]).unlink()

        # 1. Register new token
        mock_request = MagicMock()
        mock_request.env = self.env(user=self.user_test)

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            result = self.controller.get_registration_tokens(name=token_a)
            self.assertTrue(result)
            rec = self.env['push.notification'].search([
                ('user_id', '=', self.user_test.id),
                ('register_id', '=', token_a),
            ])
            self.assertEqual(len(rec), 1)
            self.assertEqual(rec.user_id.id, self.user_test.id)

            # 2. Same token sent again by current user
            result_again = self.controller.get_registration_tokens(name=token_a)
            self.assertTrue(result_again)
            self.assertEqual(len(self.env['push.notification'].search([
                ('user_id', '=', self.user_test.id),
                ('register_id', '=', token_a),
            ])), 1)

            # 3. Same token sent by another user -> creates own record, does not reassign other user's record
            other_user = self.env.ref('base.user_admin')
            mock_request.env = self.env(user=other_user)
            result_other = self.controller.get_registration_tokens(name=token_a)
            self.assertTrue(result_other)
            # Original user's record is intact and NOT reassigned
            original_rec = self.env['push.notification'].search([
                ('user_id', '=', self.user_test.id),
                ('register_id', '=', token_a),
            ])
            self.assertEqual(len(original_rec), 1)
            self.assertEqual(original_rec.user_id.id, self.user_test.id)
            # Other user has their own record
            other_rec = self.env['push.notification'].search([
                ('user_id', '=', other_user.id),
                ('register_id', '=', token_a),
            ])
            self.assertEqual(len(other_rec), 1)
            self.assertEqual(other_rec.user_id.id, other_user.id)

            # 4. Empty/None token
            result_empty = self.controller.get_registration_tokens(name=None)
            self.assertIsNone(result_empty)

    def test_send_datas(self):
        """Test send_datas route (/firebase_config_details):
        1. When push_notification is enabled, returns JSON string with vapid and config.
        2. When push_notification is disabled, returns None.
        """
        self.company.write({'push_notification': True})
        mock_request = MagicMock()
        mock_request.env.company = self.company
        mock_request.env.__getitem__.return_value = self.env['res.company']

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            # 1. Enabled
            res = self.controller.send_datas()
            self.assertTrue(res)
            data = json.loads(res)
            self.assertEqual(data.get('vapid'), 'test_vapid_key_456')
            config = data.get('config', {})
            self.assertEqual(config.get('apiKey'), 'test_api_key_123')
            self.assertEqual(config.get('projectId'), 'test-project-123')
            self.assertEqual(config.get('messagingSenderId'), '1234567890')

            # 2. Disabled
            self.company.write({'push_notification': False})
            res_disabled = self.controller.send_datas()
            self.assertIsNone(res_disabled)

        self.company.write({'push_notification': True})

    def test_firebase_credentials(self):
        """Test firebase_credentials route (/firebase_credentials):
        1. When push_notification is enabled, returns dict with push_notification: True and company id.
        2. When push_notification is disabled, returns dict with push_notification: False.
        """
        self.company.write({'push_notification': True})
        mock_request = MagicMock()
        mock_request.env.company = self.company
        mock_request.env.__getitem__.return_value = self.env['res.company']

        with patch('odoo.http.request', mock_request), \
             patch('odoo.addons.mail_push_notification.controllers.mail_push_notification.request', mock_request):
            # 1. Enabled
            creds = self.controller.firebase_credentials()
            self.assertEqual(creds.get('id'), self.company.id)
            self.assertTrue(creds.get('push_notification'))

            # 2. Disabled
            self.company.write({'push_notification': False})
            creds_disabled = self.controller.firebase_credentials()
            self.assertFalse(creds_disabled.get('push_notification'))

        self.company.write({'push_notification': True})

