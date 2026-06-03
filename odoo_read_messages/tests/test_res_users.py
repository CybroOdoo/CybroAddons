# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestActionReadMessages(TransactionCase):
    """Tests for ResUsers.action_read_messages()"""

    def setUp(self):
        super().setUp()
        self.test_user = self.env['res.users'].create({
            'name': 'Test Read User',
            'login': 'test_read_user@example.com',
            'email': 'test_read_user@example.com',
        })
        self.other_user = self.env['res.users'].create({
            'name': 'Other User',
            'login': 'other_user@example.com',
            'email': 'other_user@example.com',
        })

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def _create_channel_and_post(self, name='Test Channel'):
        """Create a channel, add test_user, post a non-notification message."""
        channel = self.env['discuss.channel'].create({
            'name': name,
            'channel_type': 'channel',
        })
        channel.add_members(partner_ids=[self.test_user.partner_id.id])
        message = channel.with_user(self.other_user).message_post(
            body=f'Hello from {name}',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )
        return channel, message

    def _get_member(self, channel):
        return self.env['discuss.channel.member'].search([
            ('channel_id', '=', channel.id),
            ('partner_id', '=', self.test_user.partner_id.id),
        ], limit=1)

    # ------------------------------------------------------------------
    # 1. Return value — always correct
    # ------------------------------------------------------------------

    def test_returns_reload_action(self):
        """action_read_messages always returns a client reload action."""
        result = self.test_user.with_user(self.test_user).action_read_messages()
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('tag'), 'reload')

    # ------------------------------------------------------------------
    # 2. Exception notifications — works correctly
    # ------------------------------------------------------------------

    def test_exception_notifications_are_cancelled(self):
        """Exception-status notifications are moved to 'canceled'."""
        message = self.env['mail.message'].create({
            'body': 'Test message body',
            'message_type': 'email',
            'subtype_id': self.env.ref('mail.mt_comment').id,
        })
        notification = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.test_user.partner_id.id,
            'notification_type': 'email',
            'notification_status': 'exception',
        })

        self.test_user.with_user(self.test_user).action_read_messages()

        notification.invalidate_recordset()
        self.assertEqual(notification.notification_status, 'canceled')

    def test_non_exception_notifications_are_untouched(self):
        """Notifications not in 'exception' status are left unchanged."""
        message = self.env['mail.message'].create({
            'body': 'Sent message body',
            'message_type': 'email',
            'subtype_id': self.env.ref('mail.mt_comment').id,
        })
        notification = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.test_user.partner_id.id,
            'notification_type': 'email',
            'notification_status': 'sent',
        })

        self.test_user.with_user(self.test_user).action_read_messages()

        notification.invalidate_recordset()
        self.assertEqual(notification.notification_status, 'sent')

    def test_multiple_exception_notifications_all_cancelled(self):
        """All exception notifications across any partner are cancelled."""
        for i in range(3):
            msg = self.env['mail.message'].create({
                'body': f'Batch message {i}',
                'message_type': 'email',
                'subtype_id': self.env.ref('mail.mt_comment').id,
            })
            self.env['mail.notification'].create({
                'mail_message_id': msg.id,
                'res_partner_id': self.test_user.partner_id.id,
                'notification_type': 'email',
                'notification_status': 'exception',
            })

        self.test_user.with_user(self.test_user).action_read_messages()

        remaining = self.env['mail.notification'].search([
            ('notification_status', '=', 'exception'),
            ('res_partner_id', '=', self.test_user.partner_id.id),
        ])
        self.assertFalse(remaining)

    # ------------------------------------------------------------------
    # 3. Channel member update — verifies it works correctly
    # ------------------------------------------------------------------

    def test_channel_member_write_branch_fires(self):
        """
        seen_message_id / fetched_message_id / last_seen_dt are updated
        after calling action_read_messages.
        """
        channel, message = self._create_channel_and_post()
        member = self._get_member(channel)

        self.test_user.with_user(self.test_user).action_read_messages()

        member.invalidate_recordset()
        self.assertEqual(member.seen_message_id.id, message.id)
        self.assertEqual(member.fetched_message_id.id, message.id)
        self.assertTrue(member.last_seen_dt)

    # ------------------------------------------------------------------
    # 4. Inbox needaction handling
    # ------------------------------------------------------------------

    def test_inbox_needaction_notifications_marked_as_read(self):
        """Verify that inbox needaction notifications are successfully marked as read."""
        message = self.env['mail.message'].create({
            'body': 'Inbox message body',
            'message_type': 'comment',
            'subtype_id': self.env.ref('mail.mt_comment').id,
        })
        notification = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.test_user.partner_id.id,
            'notification_type': 'inbox',
            'is_read': False,
        })

        self.assertFalse(notification.is_read)

        self.test_user.with_user(self.test_user).action_read_messages()

        notification.invalidate_recordset()
        self.assertTrue(notification.is_read)

    # ------------------------------------------------------------------
    # 5. Edge cases — no crash
    # ------------------------------------------------------------------

    def test_no_channel_members_no_crash(self):
        """No channel memberships : completes without error."""
        self.env['discuss.channel.member'].search([
            ('partner_id', '=', self.test_user.partner_id.id),
        ]).unlink()

        result = self.test_user.with_user(self.test_user).action_read_messages()
        self.assertEqual(result.get('tag'), 'reload')

    def test_no_messages_in_channel_no_crash(self):
        """No qualifying messages : completes without error."""
        channel = self.env['discuss.channel'].create({
            'name': 'Empty Channel',
            'channel_type': 'channel',
        })
        channel.add_members(partner_ids=[self.test_user.partner_id.id])

        result = self.test_user.with_user(self.test_user).action_read_messages()
        self.assertEqual(result.get('tag'), 'reload')

    def test_only_notification_type_messages_no_crash(self):
        """Only notification-type messages : completes without error."""
        channel = self.env['discuss.channel'].create({
            'name': 'Notification Only',
            'channel_type': 'channel',
        })
        channel.add_members(partner_ids=[self.test_user.partner_id.id])
        channel.message_post(body='System note', message_type='notification')

        result = self.test_user.with_user(self.test_user).action_read_messages()
        self.assertEqual(result.get('tag'), 'reload')
