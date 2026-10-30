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
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMailMessageAutosuggestion(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_1 = cls.env['res.users'].create({
            'name': 'Test User 1',
            'login': 'test_user_1',
            'email': 'test1@example.com',
        })
        cls.user_2 = cls.env['res.users'].create({
            'name': 'Test User 2',
            'login': 'test_user_2',
            'email': 'test2@example.com',
        })
        cls.channel = cls.env['discuss.channel'].create({
            'name': 'General Test Channel',
        })

    def test_get_message_own_messages_only(self):
        """Test that get_message returns only the current user's own messages in discuss.channel."""
        # User 1 posts a message in discuss.channel
        self.env['mail.message'].create({
            'model': 'discuss.channel',
            'res_id': self.channel.id,
            'body': '<p>Hello from User 1</p>',
            'author_id': self.user_1.partner_id.id,
            'message_type': 'comment',
        })

        # User 2 posts a message in the same discuss.channel
        self.env['mail.message'].create({
            'model': 'discuss.channel',
            'res_id': self.channel.id,
            'body': '<p>Hello from User 2</p>',
            'author_id': self.user_2.partner_id.id,
            'message_type': 'comment',
        })

        # User 1 posts a message in a different model (res.partner)
        self.env['mail.message'].create({
            'model': 'res.partner',
            'res_id': self.user_1.partner_id.id,
            'body': '<p>User 1 partner note</p>',
            'author_id': self.user_1.partner_id.id,
            'message_type': 'comment',
        })

        # When User 1 calls get_message
        suggestions_user_1 = self.env['mail.message'].with_user(self.user_1).get_message()
        self.assertIn('Hello from User 1', suggestions_user_1)
        self.assertNotIn('Hello from User 2', suggestions_user_1)
        self.assertNotIn('User 1 partner note', suggestions_user_1)

        # When User 2 calls get_message
        suggestions_user_2 = self.env['mail.message'].with_user(self.user_2).get_message()
        self.assertIn('Hello from User 2', suggestions_user_2)
        self.assertNotIn('Hello from User 1', suggestions_user_2)

    def test_get_message_html_stripping_and_empty_bodies(self):
        """Test HTML markup removal and handling of empty or blank messages."""
        self.env['mail.message'].create({
            'model': 'discuss.channel',
            'res_id': self.channel.id,
            'body': '<div><b>Important:</b> <i>meeting at 3pm</i></div>',
            'author_id': self.user_1.partner_id.id,
        })
        self.env['mail.message'].create({
            'model': 'discuss.channel',
            'res_id': self.channel.id,
            'body': '<p><br/></p>',
            'author_id': self.user_1.partner_id.id,
        })

        suggestions = self.env['mail.message'].with_user(self.user_1).get_message()
        self.assertIn('Important: meeting at 3pm', suggestions)
        self.assertNotIn('', suggestions)
