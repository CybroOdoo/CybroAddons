# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestAiToolLog(TransactionCase):

    def setUp(self):
        super(TestAiToolLog, self).setUp()
        self.tool = self.env['ai.tool'].create({
            'name': 'logging_tool',
            'description': 'Test logging tool description',
            'implementation': 'builtin',
        })
        self.log = self.env['ai.tool.log'].create({
            'tool_id': self.tool.id,
            'status': 'success',
        })

    def test_01_display_name(self):
        """Test log record naming convention via display_name."""
        name = self.log.display_name
        self.assertIn('logging_tool', name)
        self.assertIn(str(self.log.timestamp.date()), name)
