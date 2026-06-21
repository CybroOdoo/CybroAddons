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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase, tagged
from odoo import fields


@tagged('post_install', '-at_install')
class TestReadMessages(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestReadMessages, cls).setUpClass()
        # Retrieve test user and partner
        cls.user = cls.env.user
        cls.partner = cls.user.partner_id

    def test_action_read_messages_cancel_exception_notifications(self):
        """Test that action_read_messages cancels notifications in 'exception' status."""
        # Create a mail.message to link the notification to
        message = self.env['mail.message'].create({
            'model': 'res.partner',
            'res_id': self.partner.id,
            'message_type': 'comment',
            'body': 'Test Notification Message',
        })

        # Create a notification with status 'exception'
        notification = self.env['mail.notification'].create({
            'mail_message_id': message.id,
            'res_partner_id': self.partner.id,
            'notification_status': 'exception',
            'notification_type': 'email',
        })

        self.assertEqual(notification.notification_status, 'exception')

        # Execute read messages action on the current user
        res = self.user.action_read_messages()

        # Check return action is client reload
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'reload')

        # Check that notification status is updated to 'canceled'
        self.assertEqual(notification.notification_status, 'canceled')

    def test_action_read_messages_mark_channels_read(self):
        """Test that action_read_messages marks discuss channels as read up to the latest message."""
        # Create discuss channel
        channel = self.env['discuss.channel'].create({
            'name': 'Test Channel',
            'channel_type': 'channel',
        })

        # Ensure discuss channel member exists for current user
        member = self.env['discuss.channel.member'].search([
            ('channel_id', '=', channel.id),
            ('partner_id', '=', self.partner.id),
        ])
        if not member:
            member = self.env['discuss.channel.member'].create({
                'channel_id': channel.id,
                'partner_id': self.partner.id,
            })

        # Create a message in the channel (model is mail.channel as targeted by action_read_messages search)
        message = self.env['mail.message'].create({
            'model': 'mail.channel',
            'res_id': channel.id,
            'message_type': 'comment',
            'body': 'Hello Channel',
            'reply_to': 'test@example.com',
        })

        # Verify initial state has no seen_message_id
        self.assertFalse(member.seen_message_id)

        # Run the action on current user
        res = self.user.action_read_messages()

        # Assert client reload action returned
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'reload')

        # Assert channel member has seen the message
        self.assertEqual(member.seen_message_id.id, message.id)
        self.assertEqual(member.fetched_message_id.id, message.id)
        self.assertTrue(member.last_seen_dt)
