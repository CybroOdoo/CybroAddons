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

import json
from odoo.tests.common import TransactionCase

class TestMailMessage(TransactionCase):

    def setUp(self):
        super(TestMailMessage, self).setUp()
        self.message = self.env['mail.message'].create({
            'ai_role': 'assistant',
            'body_json': json.dumps({'tool_calls': [{'name': 'test_tool', 'arguments': {}}]}),
            'model': 'res.partner',
            'res_id': 1,
        })
        self.tool = self.env['ai.tool'].create({
            'name': 'test_tool',
            'description': 'Test Tool',
            'implementation': 'builtin',
        })

    def test_01_get_tool_calls(self):
        """Test extracting tool calls from message body."""
        calls = self.message.get_tool_calls()
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['name'], 'test_tool')

    def test_02_execute_tool_call(self):
        """Test executing a tool call through the message."""
        # We need a real tool handler or a builtin handler that works.
        # Since 'test_tool' doesn't have a builtin handler implemented,
        # it will fail in ai.tool.execute.
        # Let's use search_records which we know is implemented.
        self.tool.name = 'search_records'
        result = self.message.execute_tool_call('123', 'search_records', {'model': 'res.users', 'limit': 1})
        self.assertTrue(isinstance(result, list))
        
        # Verify the tool response message was created
        child_msg = self.env['mail.message'].search([('parent_id', '=', self.message.id)], limit=1)
        self.assertEqual(child_msg.ai_role, 'tool')
