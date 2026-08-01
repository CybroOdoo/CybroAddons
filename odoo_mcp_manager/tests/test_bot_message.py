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

class TestBotMessage(TransactionCase):

    def setUp(self):
        super(TestBotMessage, self).setUp()
        self.conversation = self.env['ai.bot.conversation'].create({
            'session_key': 'test_session',
            'platform': 'telegram',
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
