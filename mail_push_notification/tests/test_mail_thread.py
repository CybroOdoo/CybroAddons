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
from unittest.mock import MagicMock, patch
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailThread(TransactionCase):
    """Test cases for mail.thread model methods in mail_push_notification:
    - _notify_thread
    - _get_receiver_ids
    - _send_push_notification
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'push_notification': True,
            'project_id_firebase': 'test-firebase-proj',
            'private_key_ref': 'key_ref_999',
            'private_key': '-----BEGIN PRIVATE KEY-----\\nFAKE_KEY\\n-----END PRIVATE KEY-----\\n',
            'client_email': 'test@test-firebase-proj.iam.gserviceaccount.com',
            'client_id_firebase': 'client_id_999',
            'client_cert_url': 'https://cert.url',
        })

        # Users and partners for testing
        cls.group_user = cls.env.ref('base.group_user')
        cls.groups_field = 'group_ids' if 'group_ids' in cls.env['res.users']._fields else 'groups_id'

        cls.author_user = cls.env['res.users'].create({
            'name': 'Author User',
            'login': 'test_author_user',
            'email': 'author@example.com',
            cls.groups_field: [(6, 0, [cls.group_user.id])],
        })
        cls.receiver_user = cls.env['res.users'].create({
            'name': 'Receiver User',
            'login': 'test_receiver_user',
            'email': 'receiver@example.com',
            cls.groups_field: [(6, 0, [cls.group_user.id])],
        })
        cls.portal_group = cls.env.ref('base.group_portal', raise_if_not_found=False)
        portal_vals = {
            'name': 'Portal User',
            'login': 'test_portal_sender',
            'email': 'portal_sender@example.com',
        }
        if cls.portal_group:
            portal_vals[cls.groups_field] = [(6, 0, [cls.portal_group.id])]
        cls.portal_user = cls.env['res.users'].create(portal_vals)

        cls.external_partner = cls.env['res.partner'].create({
            'name': 'External Contact Without User',
            'email': 'contact@external.com',
        })

        # Direct chat channel for testing 1-to-1 interactions (author and receiver)
        cls.channel = cls.env['discuss.channel'].with_user(cls.author_user).create({
            'name': 'Test Discuss Chat',
            'channel_type': 'chat',
            'channel_partner_ids': [(4, cls.receiver_user.partner_id.id)],
        })

        # Public channel for testing multiple members and external contacts
        cls.public_channel = cls.env['discuss.channel'].create({
            'name': 'Test Discuss Public Channel',
            'channel_type': 'channel',
            'channel_partner_ids': [
                (4, cls.author_user.partner_id.id),
                (4, cls.receiver_user.partner_id.id),
                (4, cls.external_partner.id),
            ],
        })

        # Test message
        cls.message = cls.env['mail.message'].create({
            'model': 'discuss.channel',
            'res_id': cls.channel.id,
            'body': '<p>Hello Push Notification World!</p>',
            'author_id': cls.author_user.partner_id.id,
            'message_type': 'comment',
        })

    def test__get_receiver_ids(self):
        """Test _get_receiver_ids function on mail.thread (discuss.channel):
        1. When channel_type != 'channel' (chat), author is excluded and only non-author user partners are returned.
        2. When channel_type == 'channel', all member users are returned.
        3. Partners without corresponding res.users records are filtered out.
        """
        msg = self.message.read()

        # 1. Direct chat mode (channel_type != 'channel')
        receivers = self.channel._get_receiver_ids(msg)
        receiver_user_ids = [rec.id for rec in receivers]

        self.assertIn(
            self.receiver_user.id,
            receiver_user_ids,
            "Receiver user should be identified in direct chat."
        )
        self.assertNotIn(
            self.author_user.id,
            receiver_user_ids,
            "Author user must be excluded from receivers in direct chat."
        )

        # 2. Public channel mode (channel_type == 'channel')
        receivers_channel = self.public_channel._get_receiver_ids(msg)
        channel_user_ids = [rec.id for rec in receivers_channel]

        self.assertIn(self.receiver_user.id, channel_user_ids)
        self.assertIn(self.author_user.id, channel_user_ids)

        # 3. External partner with no user should not result in False in receiver_ids
        for rec in receivers_channel:
            self.assertTrue(rec, "Receiver should be a valid user recordset, not False or empty.")

    def test_get_receiver_ids(self):
        """Alias for test__get_receiver_ids."""
        self.test__get_receiver_ids()

    def test__send_push_notification(self):
        """Test _send_push_notification function on mail.thread:
        1. Tokens are retrieved from push.notification for the target domain.
        2. Firebase notification title and body (converted to plaintext) are correctly passed.
        3. MulticastMessage and send_each_for_multicast are invoked.
        4. If _apps is populated, initialize_app is not called again.
        """
        msg = self.message.read()

        # Register push token for receiver
        self.env['push.notification'].search([('user_id', '=', self.receiver_user.id)]).unlink()
        self.env['push.notification'].create({
            'user_id': self.receiver_user.id,
            'register_id': 'firebase_test_token_xyz',
        })

        patch_target_apps = 'odoo.addons.mail_push_notification.models.mail_thread._apps'
        patch_target_cred = 'odoo.addons.mail_push_notification.models.mail_thread.credentials.Certificate'
        patch_target_init = 'odoo.addons.mail_push_notification.models.mail_thread.initialize_app'
        patch_target_msg = 'odoo.addons.mail_push_notification.models.mail_thread.messaging'

        domain = [('user_id', 'in', [self.receiver_user.id])]

        # Subtest 1: Fresh Firebase app initialization
        with patch.dict(patch_target_apps, {}, clear=True), \
             patch(patch_target_cred) as mock_cert, \
             patch(patch_target_init) as mock_init, \
             patch(patch_target_msg) as mock_messaging:

            mock_cert.return_value = MagicMock()
            mock_messaging.Notification = MagicMock()
            mock_messaging.MulticastMessage = MagicMock()

            self.channel._send_push_notification(msg, domain)

            mock_cert.assert_called_once()
            mock_init.assert_called_once_with(mock_cert.return_value)
            mock_messaging.Notification.assert_called_once_with(
                title='Message from ' + self.author_user.partner_id.name,
                body='Hello Push Notification World!'
            )
            mock_messaging.MulticastMessage.assert_called_once()
            call_kwargs = mock_messaging.MulticastMessage.call_args[1]
            self.assertIn('firebase_test_token_xyz', call_kwargs.get('tokens', []))
            mock_messaging.send_each_for_multicast.assert_called_once()

        # Subtest 2: _apps already initialized
        with patch.dict(patch_target_apps, {'[DEFAULT]': MagicMock()}), \
             patch(patch_target_init) as mock_init, \
             patch(patch_target_msg) as mock_messaging:

            self.channel._send_push_notification(msg, domain)
            mock_init.assert_not_called()
            mock_messaging.send_each_for_multicast.assert_called_once()

    def test_send_push_notification(self):
        """Alias for test__send_push_notification."""
        self.test__send_push_notification()

    def test__notify_thread(self):
        """Test _notify_thread function on mail.thread:
        1. When push_notification is disabled on company, _send_push_notification is not called.
        2. When current user is not in group_user, _send_push_notification is not called.
        3. When push_notification is enabled and user is internal, _send_push_notification is called.
        4. When an exception occurs during push, it is captured and logged via _logger.error.
        """
        # 1. Company push_notification disabled
        self.company.push_notification = False
        with patch.object(type(self.channel), '_send_push_notification') as mock_send:
            self.channel._notify_thread(self.message)
            mock_send.assert_not_called()

        # 2. Company push enabled, but sender user is not in group_user (portal user)
        self.company.push_notification = True
        with patch.object(type(self.channel), '_send_push_notification') as mock_send:
            self.channel.with_user(self.portal_user)._notify_thread(self.message)
            mock_send.assert_not_called()

        # 3. Company push enabled and sender is internal user -> calls _send_push_notification
        with patch.object(type(self.channel), '_send_push_notification') as mock_send, \
             patch.object(type(self.channel), '_get_receiver_ids', return_value=[self.receiver_user]):
            self.channel.with_user(self.author_user)._notify_thread(self.message)
            mock_send.assert_called_once()
            called_domain = mock_send.call_args[0][1]
            self.assertEqual(called_domain, [('user_id', 'in', [self.receiver_user.id])])

        # 4. Exception in push notification is safely caught and logged via _logger.error
        with patch.object(type(self.channel), '_send_push_notification', side_effect=RuntimeError("FCM Outage")), \
             patch('odoo.addons.mail_push_notification.models.mail_thread._logger.error') as mock_log_error:
            self.channel.with_user(self.author_user)._notify_thread(self.message)
            mock_log_error.assert_called_once()
            self.assertIn("FCM Outage", str(mock_log_error.call_args))

    def test_notify_thread(self):
        """Alias for test__notify_thread."""
        self.test__notify_thread()

