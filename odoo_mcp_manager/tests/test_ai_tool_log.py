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

class TestAiToolLog(TransactionCase):

    def setUp(self):
        super(TestAiToolLog, self).setUp()
        self.tool = self.env['ai.tool'].create({
            'name': 'logging_tool',
            'description': 'Tool used for log tests',
            'implementation': 'builtin',
        })
        self.log = self.env['ai.tool.log'].create({
            'tool_id': self.tool.id,
            'status': 'success',
        })

    def test_01_display_name(self):
        """Test log record naming convention."""
        name = self.log.display_name
        self.assertIn('logging_tool', name)
        self.assertIn(str(self.log.timestamp.date()), name)
