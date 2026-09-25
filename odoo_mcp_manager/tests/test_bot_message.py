# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestBotMessage(TransactionCase):

    def setUp(self):
        super(TestBotMessage, self).setUp()
        self.conversation = self.env['ai.bot.conversation'].create({
            'session_key': 'test_session',
            'platform_user_id': 'user123',
        })

    def test_01_create_user_message(self):
        """Test basic message creation."""
        msg = self.env['ai.bot.message'].create({
            'conversation_id': self.conversation.id,
            'role': 'user',
            'content': 'Hello AI',
        })
        self.assertEqual(msg.role, 'user')
        self.assertEqual(msg.content, 'Hello AI')

    def test_02_create_assistant_message(self):
        """Test assistant message with tool info."""
        msg = self.env['ai.bot.message'].create({
            'conversation_id': self.conversation.id,
            'role': 'assistant',
            'content': 'I found your records.',
            'tool_used': 'search_records',
        })
        self.assertEqual(msg.role, 'assistant')
        self.assertEqual(msg.tool_used, 'search_records')
