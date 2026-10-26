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
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestResUsersReadMessages(TransactionCase):
    """Test suite for Odoo Read Messages feature on res.users"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.user_a = cls.env['res.users'].create({
            'name': 'User A',
            'login': 'user_a_read_msgs',
            'email': 'user_a@example.com',
        })
        cls.user_b = cls.env['res.users'].create({
            'name': 'User B',
            'login': 'user_b_read_msgs',
            'email': 'user_b@example.com',
        })
        cls.external_partner = cls.env['res.partner'].create({
            'name': 'External Contact',
            'email': 'external@example.com',
        })

    def test_01_read_notifications_isolation(self):
        """Test marking notifications as read only affects the target user as recipient."""
        message = self.env['mail.message'].create({
            'subject': 'Message from User A',
            'body': '<p>Hello from A</p>',
            'author_id': self.user_a.partner_id.id,
            'message_type': 'notification',
        })

        notif_a = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.user_a.partner_id.id,
            'author_id': self.user_a.partner_id.id,
            'notification_type': 'inbox',
            'is_read': False,
        })
        notif_b = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.user_b.partner_id.id,
            'author_id': self.user_a.partner_id.id,
            'notification_type': 'inbox',
            'is_read': False,
        })

        self.assertFalse(notif_a.is_read)
        self.assertFalse(notif_b.is_read)

        # User A executes action_read_messages
        action = self.user_a.with_user(self.user_a).action_read_messages()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'reload')

        # User A's notification should be read
        self.assertTrue(notif_a.is_read)
        # User B's notification should NOT be marked as read, even though User A is the author
        self.assertFalse(notif_b.is_read)

    def test_02_cancel_failed_notifications_by_author(self):
        """Test cancelling bounce/exception notifications correctly clears failures belonging to author."""
        # Message 1 authored by User A to an external partner (User A's delivery failure)
        msg_a = self.env['mail.message'].create({
            'subject': 'Failure Message from User A',
            'body': '<p>User A email bounced</p>',
            'author_id': self.user_a.partner_id.id,
            'message_type': 'email',
        })
        notif_a = self.env['mail.notification'].create({
            'mail_message_id': msg_a.id,
            'res_partner_id': self.external_partner.id,
            'author_id': self.user_a.partner_id.id,
            'notification_type': 'email',
            'notification_status': 'bounce',
        })

        # Message 2 authored by User B sent to User A (User B's delivery failure)
        msg_b = self.env['mail.message'].create({
            'subject': 'Failure Message from User B',
            'body': '<p>User B email failed</p>',
            'author_id': self.user_b.partner_id.id,
            'message_type': 'email',
        })
        notif_b = self.env['mail.notification'].create({
            'mail_message_id': msg_b.id,
            'res_partner_id': self.user_a.partner_id.id,
            'author_id': self.user_b.partner_id.id,
            'notification_type': 'email',
            'notification_status': 'exception',
        })

        self.assertEqual(notif_a.notification_status, 'bounce')
        self.assertEqual(notif_b.notification_status, 'exception')

        # User A executes action_read_messages
        self.user_a.with_user(self.user_a).action_read_messages()

        # User A's own delivery failure (where User A is author) should be canceled
        self.assertEqual(notif_a.notification_status, 'canceled')
        # User B's delivery failure should NOT be cleared by User A (does not hide other authors' failures)
        self.assertEqual(notif_b.notification_status, 'exception')

    def test_03_discuss_channel_mark_as_read(self):
        """Test marking discuss channel messages as read using batch query."""
        channel = self.env['discuss.channel'].create({
            'name': 'Test Discuss Channel',
            'channel_member_ids': [
                (0, 0, {'partner_id': self.user_a.partner_id.id}),
            ],
        })
        message = channel.message_post(body="Hello Discuss Channel", message_type="comment")

        member = self.env['discuss.channel.member'].search([
            ('channel_id', '=', channel.id),
            ('partner_id', '=', self.user_a.partner_id.id),
        ])
        self.assertTrue(member)
        self.assertTrue(not member.seen_message_id or member.seen_message_id.id < message.id)

        # User A executes action_read_messages
        self.user_a.with_user(self.user_a).action_read_messages()

        self.assertEqual(member.seen_message_id.id, message.id)

    def test_04_security_access_rights(self):
        """Test that non-admin users cannot call action_read_messages on other users."""
        # Non-admin user A attempting to call action_read_messages on user B must raise AccessError
        with self.assertRaises(AccessError):
            self.user_b.with_user(self.user_a).action_read_messages()

        # Non-admin user A calling on themselves succeeds
        action = self.user_a.with_user(self.user_a).action_read_messages()
        self.assertEqual(action.get('type'), 'ir.actions.client')

        # Admin user calling on user B succeeds
        admin_user = self.env.ref('base.user_admin')
        action_admin = self.user_b.with_user(admin_user).action_read_messages()
        self.assertEqual(action_admin.get('type'), 'ir.actions.client')

    def test_05_admin_operates_on_target_user_record(self):
        """Test admin action_read_messages operates on target user record, not admin user."""
        message = self.env['mail.message'].create({
            'subject': 'Admin vs Target Test',
            'body': '<p>Target test</p>',
            'message_type': 'notification',
        })

        admin_user = self.env.ref('base.user_admin')
        admin_notif = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': admin_user.partner_id.id,
            'notification_type': 'inbox',
            'is_read': False,
        })
        user_b_notif = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.user_b.partner_id.id,
            'notification_type': 'inbox',
            'is_read': False,
        })

        # Admin views User B's form and clicks action_read_messages
        self.user_b.with_user(admin_user).action_read_messages()

        # User B's notification should be marked as read
        self.assertTrue(user_b_notif.is_read)
        # Admin's notification should NOT be marked as read
        self.assertFalse(admin_notif.is_read)

    def test_06_empty_recordset(self):
        """Test calling action_read_messages on an empty recordset."""
        action = self.env['res.users'].browse().action_read_messages()
        self.assertEqual(action, {'type': 'ir.actions.client', 'tag': 'reload'})
