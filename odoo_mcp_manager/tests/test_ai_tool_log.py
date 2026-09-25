# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestAiToolLog(TransactionCase):

    def setUp(self):
        super(TestAiToolLog, self).setUp()
        self.tool = self.env['ai.tool'].create({
            'name': 'logging_tool',
            'implementation': 'builtin',
            'builtin_action': 'search_records',
        })
        self.log = self.env['ai.tool.log'].create({
            'tool_id': self.tool.id,
            'status': 'success',
        })

    def test_01_name_get(self):
        """Test log record naming convention."""
        name = self.log.name_get()[0][1]
        self.assertIn('logging_tool', name)
        self.assertIn(str(self.log.timestamp.date()), name)
