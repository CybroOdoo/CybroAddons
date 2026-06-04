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
from odoo import fields
from odoo.tests.common import TransactionCase


class TestResUsersReadMessages(TransactionCase):
    """
    Tests for ResUsers.action_read_messages() (odoo_read_messages module)
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use the admin user as the acting user throughout
        cls.user = cls.env.ref('base.user_admin')
        cls.partner = cls.user.partner_id

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _create_channel(self, name='Test Channel'):
        """Create a mail.channel and add the current user as a member."""
        channel = self.env['mail.channel'].create({'name': name})
        # Ensure the admin partner is a member (Odoo 16 public API)
        channel.sudo().add_members(partner_ids=[self.partner.id])
        return channel

    def _post_channel_message(self, channel):
        """Post a non-notification message to *channel* and return it."""
        return channel.sudo().message_post(
            body='Test message body',
            message_type='comment',
            subtype_xmlid='mail.mt_comment',
        )

    def _get_member(self, channel):
        """Return the mail.channel.member record for admin in *channel*."""
        return self.env['mail.channel.member'].search([
            ('channel_id', '=', channel.id),
            ('partner_id', '=', self.partner.id),
        ], limit=1)

    def _create_unread_notification(self, message=None):
        """
        Create an unread mail.notification for the admin partner.
        If *message* is not supplied, a minimal one is created.
        """
        if message is None:
            message = self.env['mail.message'].create({
                'subject': 'Test notification subject',
                'body': 'Test notification body',
                'message_type': 'comment',
                'model': False,
                'res_id': False,
            })
        notif = self.env['mail.notification'].sudo().create({
            'mail_message_id': message.id,
            'res_partner_id': self.partner.id,
            'notification_type': 'inbox',
            'is_read': False,
        })
        return notif

    def _create_exception_notification(self, message=None):
        """Create a mail.notification with notification_status='exception'."""
        if message is None:
            message = self.env['mail.message'].create({
                'subject': 'Exception subject',
                'body': 'Exception body',
                'message_type': 'email',
                'model': False,
                'res_id': False,
            })
        notif = self.env['mail.notification'].sudo().create({
            'mail_message_id': message.id,
            'res_partner_id': self.partner.id,
            'notification_type': 'email',
            'notification_status': 'exception',
        })
        return notif

    # -----------------------------------------------------------------------
    # 1. Method existence
    # -----------------------------------------------------------------------

    def test_action_read_messages_method_exists(self):
        """action_read_messages must be defined on res.users."""
        self.assertTrue(
            hasattr(self.env['res.users'], 'action_read_messages'),
            "action_read_messages() must be defined on res.users",
        )

    # -----------------------------------------------------------------------
    # 2. Exception notification cancellation
    # -----------------------------------------------------------------------

    def test_exception_notifications_cancelled(self):
        """action_read_messages() must set exception notifications to 'canceled'."""
        notif = self._create_exception_notification()
        self.assertEqual(notif.notification_status, 'exception')

        self.user.action_read_messages()

        self.assertEqual(
            notif.notification_status,
            'canceled',
            "Exception notification must be set to 'canceled' after action_read_messages()",
        )

    def test_multiple_exception_notifications_all_cancelled(self):
        """All exception notifications must be cancelled, regardless of partner."""
        n1 = self._create_exception_notification()
        n2 = self._create_exception_notification()
        self.user.action_read_messages()
        self.assertEqual(n1.notification_status, 'canceled')
        self.assertEqual(n2.notification_status, 'canceled')

    def test_non_exception_notification_status_unchanged(self):
        """Notifications with status 'sent' must not be affected."""
        message = self.env['mail.message'].create({
            'subject': 'Sent msg', 'body': 'body',
            'message_type': 'email', 'model': False, 'res_id': False,
        })
        sent_notif = self.env['mail.notification'].sudo().create({
            'mail_message_id': message.id,
            'res_partner_id': self.partner.id,
            'notification_type': 'email',
            'notification_status': 'sent',
        })
        self.user.action_read_messages()
        self.assertEqual(sent_notif.notification_status, 'sent')

    # -----------------------------------------------------------------------
    # 3. Unread notification mark-as-read
    # -----------------------------------------------------------------------

    def test_unread_notifications_marked_as_read(self):
        """action_read_messages() must set is_read=True on all unread notifications."""
        notif = self._create_unread_notification()
        self.assertFalse(notif.is_read)

        self.user.action_read_messages()

        notif.invalidate_recordset()
        self.assertTrue(
            notif.is_read,
            "is_read must be True after action_read_messages()",
        )

    def test_multiple_unread_notifications_all_marked(self):
        """All unread notifications for the partner must be marked as read."""
        notifs = [self._create_unread_notification() for _ in range(3)]
        self.user.action_read_messages()
        for n in notifs:
            n.invalidate_recordset()
            self.assertTrue(n.is_read, f"Notification {n.id} must be marked as read")

    def test_already_read_notification_unchanged(self):
        """Notifications already read must remain read."""
        notif = self._create_unread_notification()
        notif.sudo().write({'is_read': True})
        self.user.action_read_messages()
        self.assertTrue(notif.is_read)

    def test_unread_notification_of_other_partner_not_marked(self):
        """Unread notifications belonging to other partners must not be touched."""
        other_partner = self.env['res.partner'].create({'name': 'Other Partner'})
        message = self.env['mail.message'].create({
            'subject': 'Other msg', 'body': 'body',
            'message_type': 'comment', 'model': False, 'res_id': False,
        })
        other_notif = self.env['mail.notification'].sudo().create({
            'mail_message_id': message.id,
            'res_partner_id': other_partner.id,
            'notification_type': 'inbox',
            'is_read': False,
        })
        self.user.action_read_messages()
        self.assertFalse(
            other_notif.is_read,
            "Notifications for other partners must not be marked as read",
        )

    # -----------------------------------------------------------------------
    # 4. Channel member seen_message_id / fetched_message_id update
    # -----------------------------------------------------------------------

    def test_channel_member_seen_message_updated(self):
        """seen_message_id must be advanced to the latest channel message."""
        channel = self._create_channel('ReadChannel')
        msg = self._post_channel_message(channel)
        member = self._get_member(channel)

        self.user.action_read_messages()

        member.invalidate_recordset()
        self.assertEqual(
            member.seen_message_id.id,
            msg.id,
            "seen_message_id must equal the latest message after action_read_messages()",
        )

    def test_channel_member_fetched_message_updated(self):
        """fetched_message_id must be advanced to the latest channel message."""
        channel = self._create_channel('FetchedChannel')
        msg = self._post_channel_message(channel)
        member = self._get_member(channel)

        self.user.action_read_messages()

        member.invalidate_recordset()
        self.assertEqual(
            member.fetched_message_id.id,
            msg.id,
            "fetched_message_id must equal the latest message after action_read_messages()",
        )

    def test_last_seen_dt_updated(self):
        """last_seen_dt must be updated (non-False) after action_read_messages()."""
        channel = self._create_channel('LastSeenChannel')
        self._post_channel_message(channel)
        member = self._get_member(channel)

        before = fields.Datetime.now()
        self.user.action_read_messages()
        member.invalidate_recordset()

        self.assertTrue(
            member.last_seen_dt,
            "last_seen_dt must be set after action_read_messages()",
        )
        self.assertGreaterEqual(
            member.last_seen_dt,
            before,
            "last_seen_dt must be >= the time before the call",
        )

    # -----------------------------------------------------------------------
    # 5. No notifications / no messages — no-op safety
    # -----------------------------------------------------------------------

    def test_no_exception_notifications_no_crash(self):
        """action_read_messages() must not crash when there are no exception notifications."""
        self.env['mail.notification'].sudo().search([
            ('notification_status', '=', 'exception')
        ]).write({'notification_status': 'canceled'})
        try:
            self.user.action_read_messages()
        except Exception as exc:
            self.fail(f"action_read_messages() raised with no exception notifications: {exc}")

    def test_no_unread_notifications_no_crash(self):
        """action_read_messages() must not crash when there are no unread notifications."""
        self.env['mail.notification'].sudo().search([
            ('res_partner_id', '=', self.partner.id),
            ('is_read', '=', False),
        ]).write({'is_read': True})
        try:
            self.user.action_read_messages()
        except Exception as exc:
            self.fail(f"action_read_messages() raised with no unread notifications: {exc}")

    # -----------------------------------------------------------------------
    # 6. Idempotency
    # -----------------------------------------------------------------------

    def test_idempotent_unread_notifications(self):
        """Calling action_read_messages() twice leaves is_read=True."""
        notif = self._create_unread_notification()
        self.user.action_read_messages()
        self.user.action_read_messages()
        notif.invalidate_recordset()
        self.assertTrue(notif.is_read)

    def test_idempotent_channel_member_update(self):
        """Calling action_read_messages() twice must leave member fields consistent."""
        channel = self._create_channel('IdempotentChannel')
        msg = self._post_channel_message(channel)
        member = self._get_member(channel)

        self.user.action_read_messages()
        self.user.action_read_messages()

        member.invalidate_recordset()
        self.assertEqual(member.seen_message_id.id, msg.id)
        self.assertEqual(member.fetched_message_id.id, msg.id)