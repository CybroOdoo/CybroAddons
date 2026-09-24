# -*- coding: utf-8 -*-
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
