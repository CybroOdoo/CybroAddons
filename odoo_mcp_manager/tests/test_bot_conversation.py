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

from odoo.tests.common import TransactionCase

class TestBotConversation(TransactionCase):

    def setUp(self):
        super(TestBotConversation, self).setUp()
        self.conversation = self.env['ai.bot.conversation'].create({
            'session_key': 'telegram:123456',
            'platform': 'telegram',
            'platform_user_id': '123456',
        })

    def test_01_add_message(self):
        """Test adding messages to a conversation."""
        self.conversation.add_message('user', 'Hello AI')
        self.assertEqual(len(self.conversation.message_ids), 1)
        self.assertEqual(self.conversation.message_ids[0].role, 'user')
        self.assertEqual(self.conversation.message_ids[0].content, 'Hello AI')

    def test_02_get_recent_messages(self):
        """Test retrieving recent messages in chronological order."""
        self.conversation.add_message('user', 'Msg 1')
        self.conversation.add_message('assistant', 'Msg 2')
        self.conversation.add_message('user', 'Msg 3')
        
        recent = self.conversation.get_recent_messages(limit=2)
        self.assertEqual(len(recent), 2)
        # Should be Msg 2 and Msg 3 in order
        self.assertEqual(recent[0]['content'], 'Msg 2')
        self.assertEqual(recent[1]['content'], 'Msg 3')
