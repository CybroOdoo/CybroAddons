# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json
from unittest.mock import patch

from odoo.tests import TransactionCase, HttpCase


class TestPushNotification(TransactionCase):
    """Test cases for the mail_push_notification model and integration logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a test company with mock Firebase configurations
        cls.test_company = cls.env['res.company'].create({
            'name': 'Test Push Notification Company',
            'push_notification': True,
            'api_key': 'test_api_key_123',
            'auth_domain': 'test_auth_domain',
            'project_id_firebase': 'test_project_id',
            'private_key_ref': 'test_private_key_ref',
            'private_key': 'test_private_key_value',
            'client_email': 'test_client_email@example.com',
            'client_id_firebase': 'test_client_id',
            'client_cert_url': 'test_cert_url',
            'vapid': 'test_vapid_key',
            'storage_bucket': 'test_storage_bucket',
            'messaging_sender_id_firebase': 'test_sender_id',
            'app_id_firebase': 'test_app_id',
            'measurement_id_firebase': 'test_measurement_id',
        })

        # Create a test user with base.group_user (Internal User)
        cls.user_internal = cls.env['res.users'].create({
            'name': 'Internal User',
            'login': 'internal_user_push',
            'email': 'internal_user@example.com',
            'company_id': cls.test_company.id,
            'company_ids': [(4, cls.test_company.id)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

        # Create a portal user
        cls.user_portal = cls.env['res.users'].create({
            'name': 'Portal User',
            'login': 'portal_user_push',
            'email': 'portal@example.com',
            'company_id': cls.test_company.id,
            'company_ids': [(4, cls.test_company.id)],
            'groups_id': [(6, 0, [cls.env.ref('base.group_portal').id])],
        })

    def test_01_user_push_notification_permission(self):
        """Test the has_push_notification_permission() method on users."""
        self.assertTrue(self.user_internal.has_push_notification_permission())
        self.assertFalse(self.user_portal.has_push_notification_permission())

    def test_02_config_settings_test_connection_disabled(self):
        """Test test_connection when push notification is disabled."""
        self.env.company.push_notification = False
        config = self.env['res.config.settings'].create({
            'company_id': self.env.company.id,
        })
        # If disabled, test_connection should return False
        self.assertFalse(config.test_connection())

    @patch('odoo.addons.mail_push_notification.models.res_config_settings.credentials.Certificate')
    @patch('odoo.addons.mail_push_notification.models.res_config_settings.initialize_app')
    def test_03_config_settings_test_connection_success(self, mock_init, mock_cert):
        """Test test_connection when push notification is enabled and initialization succeeds."""
        self.test_company.push_notification = True
        config = self.env['res.config.settings'].create({
            'company_id': self.test_company.id,
            'project_id_firebase': 'test_proj',
            'private_key_ref': 'test_ref',
            'private_key': 'test_key',
            'client_email': 'test_email',
            'client_id_firebase': 'test_client_id',
            'client_cert_url': 'test_cert_url',
        })

        with patch('odoo.addons.mail_push_notification.models.res_config_settings._apps', []):
            res = config.test_connection()

            mock_cert.assert_called_once()
            args, kwargs = mock_cert.call_args
            self.assertEqual(args[0]['project_id'], 'test_proj')
            self.assertEqual(args[0]['private_key_id'], 'test_ref')

            mock_init.assert_called_once()

            self.assertEqual(res.get('type'), 'ir.actions.client')
            self.assertEqual(res.get('tag'), 'display_notification')
            self.assertEqual(res.get('params').get('type'), 'success')
            self.assertIn("Connection successfully established", res.get('params').get('message'))

    @patch('odoo.addons.mail_push_notification.models.res_config_settings.credentials.Certificate')
    @patch('odoo.addons.mail_push_notification.models.res_config_settings.initialize_app')
    def test_04_config_settings_test_connection_failure(self, mock_init, mock_cert):
        """Test test_connection when an exception occurs during initialization."""
        self.test_company.push_notification = True
        config = self.env['res.config.settings'].create({
            'company_id': self.test_company.id,
            'project_id_firebase': 'test_proj',
            'private_key_ref': 'test_ref',
            'private_key': 'test_key',
            'client_email': 'test_email',
            'client_id_firebase': 'test_client_id',
            'client_cert_url': 'test_cert_url',
        })

        mock_init.side_effect = Exception("Firebase Config Error")

        with patch('odoo.addons.mail_push_notification.models.res_config_settings._apps', []):
            res = config.test_connection()

            self.assertEqual(res.get('type'), 'ir.actions.client')
            self.assertEqual(res.get('tag'), 'display_notification')
            self.assertEqual(res.get('params').get('type'), 'danger')
            self.assertIn("Failed to connect with firebase", res.get('params').get('message'))

    def test_05_mail_thread_get_receiver_ids_chat(self):
        """Test _get_receiver_ids for a direct chat channel."""
        partner_2 = self.env['res.partner'].create({'name': 'Partner 2'})

        user_2 = self.env['res.users'].create({
            'name': 'User 2',
            'login': 'user2_push',
            'email': 'user2@example.com',
            'partner_id': partner_2.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        # Chat channels in Odoo must have exactly two partners (usually the creator and the target user)
        channel = self.env['discuss.channel'].create({
            'name': 'Chat Channel',
            'channel_type': 'chat',
            'channel_partner_ids': [(4, self.env.user.partner_id.id), (4, partner_2.id)],
        })

        msg = [{'author_id': (self.env.user.partner_id.id, self.env.user.name)}]

        receivers = channel._get_receiver_ids(msg)
        self.assertIn(user_2, receivers)

    def test_06_mail_thread_get_receiver_ids_channel(self):
        """Test _get_receiver_ids for a group channel."""
        partner_1 = self.env['res.partner'].create({'name': 'Partner 1'})
        partner_2 = self.env['res.partner'].create({'name': 'Partner 2'})

        user_2 = self.env['res.users'].create({
            'name': 'User 2',
            'login': 'user2_push_channel',
            'email': 'user2_chan@example.com',
            'partner_id': partner_2.id,
            'groups_id': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        channel = self.env['discuss.channel'].create({
            'name': 'Public Channel',
            'channel_type': 'channel',
            'channel_partner_ids': [(4, partner_1.id), (4, partner_2.id)],
        })

        msg = [{'author_id': (partner_1.id, 'Partner 1')}]

        receivers = channel._get_receiver_ids(msg)
        self.assertIn(user_2, receivers)

    @patch('odoo.addons.mail_push_notification.models.mail_thread.credentials.Certificate')
    @patch('odoo.addons.mail_push_notification.models.mail_thread.messaging.send_each_for_multicast')
    @patch('odoo.addons.mail_push_notification.models.mail_thread.messaging.MulticastMessage')
    @patch('odoo.addons.mail_push_notification.models.mail_thread.messaging.Notification')
    @patch('odoo.addons.mail_push_notification.models.mail_thread.initialize_app')
    def test_07_mail_thread_send_push_notification(self, mock_init, mock_notif, mock_multi, mock_send, mock_cert):
        """Test _send_push_notification functionality."""
        self.env.user.company_id = self.test_company

        self.env['push.notification'].create({
            'user_id': self.user_internal.id,
            'register_id': 'token_internal_1'
        })
        self.env['push.notification'].create({
            'user_id': self.user_portal.id,
            'register_id': 'token_portal_2'
        })

        msg = [{
            'author_id': (self.env.user.partner_id.id, self.env.user.name),
            'body': '<p>Hello world push notification test</p>'
        }]

        domain = [('user_id', 'in', [self.user_internal.id, self.user_portal.id])]

        with patch('odoo.addons.mail_push_notification.models.mail_thread._apps', []):
            self.env['mail.thread']._send_push_notification(msg, domain)

            mock_init.assert_called_once()
            mock_notif.assert_called_once_with(
                title='Message from ' + self.env.user.name,
                body='Hello world push notification test'
            )
            mock_multi.assert_called_once()
            args, kwargs = mock_multi.call_args
            self.assertIn('token_internal_1', kwargs.get('tokens'))
            self.assertIn('token_portal_2', kwargs.get('tokens'))
            mock_send.assert_called_once()

    @patch('odoo.addons.mail_push_notification.models.mail_thread.MailThread._send_push_notification')
    def test_08_mail_thread_notify_thread(self, mock_send_push):
        """Test that _notify_thread triggers push notification flow."""
        self.env.user.company_id = self.test_company
        self.test_company.push_notification = True

        partner_1 = self.env['res.partner'].create({'name': 'Partner 1'})
        channel = self.env['discuss.channel'].create({
            'name': 'Test Channel',
            'channel_type': 'chat',
            'channel_partner_ids': [(4, self.env.user.partner_id.id), (4, partner_1.id)],
        })

        with patch('odoo.addons.mail_push_notification.models.mail_thread.MailThread._get_receiver_ids', return_value=[self.user_internal]):
            message = channel.message_post(body="Test message body", message_type="comment")

            mock_send_push.assert_called_once()
            args, kwargs = mock_send_push.call_args

            msg_arg = args[0]
            self.assertEqual(msg_arg[0]['id'], message.id)
            self.assertEqual(args[1], [('user_id', 'in', [self.user_internal.id])])

    @patch('odoo.addons.mail_push_notification.models.mail_thread.MailThread._send_push_notification')
    def test_09_mail_thread_notify_thread_exception(self, mock_send_push):
        """Test that exception during _notify_thread is gracefully caught and logged in ir.logging."""
        self.env.user.company_id = self.test_company
        self.test_company.push_notification = True

        mock_send_push.side_effect = Exception("Firebase Multicast Error")

        log_count_before = self.env['ir.logging'].sudo().search_count([
            ('name', '=', 'Push Notification Error'),
            ('message', '=', 'Firebase Multicast Error')
        ])

        channel = self.env['discuss.channel'].create({
            'name': 'Test Channel Exception',
            'channel_type': 'chat',
            'channel_partner_ids': [(4, self.env.user.partner_id.id)],
        })

        with patch('odoo.addons.mail_push_notification.models.mail_thread.MailThread._get_receiver_ids', return_value=[self.user_internal]):
            channel.message_post(body="Test exception body", message_type="comment")

            log_count_after = self.env['ir.logging'].sudo().search_count([
                ('name', '=', 'Push Notification Error'),
                ('message', '=', 'Firebase Multicast Error')
            ])
            self.assertEqual(log_count_after, log_count_before + 1)


class TestPushNotificationController(HttpCase):
    """Functional tests for the push notification routes."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.company.write({
            'push_notification': True,
            'api_key': 'ctrl_api_key',
            'auth_domain': 'ctrl_auth_domain',
            'project_id_firebase': 'ctrl_project_id',
            'storage_bucket': 'ctrl_storage_bucket',
            'messaging_sender_id_firebase': 'ctrl_sender_id',
            'app_id_firebase': 'ctrl_app_id',
            'measurement_id_firebase': 'ctrl_measurement_id',
            'vapid': 'ctrl_vapid',
        })

        # Set admin password to 'admin' to ensure authenticate works
        admin_user = self.env.ref('base.user_admin')
        admin_user.sudo().write({'password': 'admin'})
        self.admin_login = admin_user.login

    def test_10_sw_js_route(self):
        """Test GET /firebase-messaging-sw.js endpoint."""
        # Test when push notification is enabled
        self.company.push_notification = True
        response = self.url_open('/firebase-messaging-sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/javascript', response.headers.get('Content-Type', ''))
        content = response.text
        self.assertIn("ctrl_api_key", content)
        self.assertIn("ctrl_auth_domain", content)
        self.assertIn("ctrl_project_id", content)

        # Test when push notification is disabled
        self.company.push_notification = False
        response = self.url_open('/firebase-messaging-sw.js')
        self.assertEqual(response.status_code, 200)
        content = response.text
        self.assertNotIn("ctrl_api_key", content)
        self.assertIn("caches.match(e.request)", content)

    def test_11_push_notification_route(self):
        """Test JSON /push_notification route."""
        # Clear any existing tokens matching the test token
        self.env['push.notification'].sudo().search([('register_id', '=', 'test_token_ctrl')]).unlink()

        self.authenticate(self.admin_login, 'admin')
        admin_user = self.env.ref('base.user_admin')

        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {
                'name': 'test_token_ctrl',
            },
            'id': 1,
        }
        response = self.url_open(
            '/push_notification',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertNotIn('error', res_data)
        self.assertTrue(res_data.get('result'))

        # Check token registration in DB
        token_record = self.env['push.notification'].sudo().search([('register_id', '=', 'test_token_ctrl')])
        self.assertTrue(token_record)
        self.assertEqual(token_record.user_id.id, admin_user.id)

        # Re-send the same token to test uniqueness/idempotence check
        response = self.url_open(
            '/push_notification',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertNotIn('error', res_data)

        token_records = self.env['push.notification'].sudo().search([('register_id', '=', 'test_token_ctrl')])
        self.assertEqual(len(token_records), 1)

    def test_12_firebase_config_details_route(self):
        """Test JSON /firebase_config_details route."""
        self.company.push_notification = True
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {},
            'id': 1,
        }
        response = self.url_open(
            '/firebase_config_details',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertNotIn('error', res_data)

        # Parse stringified json result returned by route
        result_dict = json.loads(res_data.get('result'))
        self.assertEqual(result_dict.get('vapid'), 'ctrl_vapid')
        self.assertEqual(result_dict.get('config').get('apiKey'), 'ctrl_api_key')
        self.assertEqual(result_dict.get('config').get('projectId'), 'ctrl_project_id')

    def test_13_firebase_credentials_route(self):
        """Test JSON /firebase_credentials route."""
        self.company.push_notification = True
        payload = {
            'jsonrpc': '2.0',
            'method': 'call',
            'params': {},
            'id': 1,
        }
        response = self.url_open(
            '/firebase_credentials',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(response.status_code, 200)
        res_data = response.json()
        self.assertNotIn('error', res_data)

        result = res_data.get('result')
        self.assertEqual(result.get('id'), self.company.id)
        self.assertTrue(result.get('push_notification'))
