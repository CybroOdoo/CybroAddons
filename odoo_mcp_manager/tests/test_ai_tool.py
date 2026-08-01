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
from odoo.exceptions import UserError

class TestAiTool(TransactionCase):

    def setUp(self):
        super(TestAiTool, self).setUp()
        self.tool = self.env['ai.tool'].create({
            'name': 'test_search',
            'description': 'Test Search Tool',
            'implementation': 'builtin',
        })
        # Using res.groups instead of res.partner to avoid environment-specific constraints
        self.test_record = self.env['res.groups'].create({
            'name': 'Test Group',
        })
        # Grant the built-in tools full access to res.groups for these mechanic
        # tests (the allow-list itself is covered by dedicated tests). Reuse any
        # rule the default seeding may already have created.
        access_model = self.env['ai.tool.access']
        model_id = self.env['ir.model']._get_id('res.groups')
        grant = {
            'allow_read': True, 'allow_create': True, 'allow_update': True,
            'allow_delete': True, 'allow_unlink': True,
        }
        rule = access_model.search([('model_id', '=', model_id)], limit=1)
        if rule:
            rule.write(grant)
        else:
            access_model.create(dict(grant, model_id=model_id))

    def test_01_compute_tool_definition(self):
        """Test if the MCP tool definition is correctly computed."""
        self.tool.input_schema = json.dumps({
            'type': 'object',
            'properties': {'model': {'type': 'string'}}
        })
        self.assertIn('test_search', self.tool.tool_definition)
        self.assertIn('Test Search Tool', self.tool.tool_definition)

    def test_02_execute_builtin_search(self):
        """Test built-in search_records tool."""
        self.tool.name = 'search_records'
        params = {
            'model': 'res.groups',
            'domain': [('name', '=', 'Test Group')],
            'limit': 1
        }
        result = self.tool.execute(params)
        self.assertTrue(len(result) > 0)
        self.assertEqual(result[0]['name'], 'Test Group')

    def test_03_execute_builtin_create(self):
        """Test built-in create_record tool."""
        self.tool.name = 'create_record'
        params = {
            'model': 'res.groups',
            'values': {'name': 'New Group'}
        }
        result = self.tool.execute(params)
        self.assertEqual(result['display_name'], 'New Group')
        new_group = self.env['res.groups'].browse(result['id'])
        self.assertTrue(new_group.exists())

    def test_04_execute_builtin_update(self):
        """Test built-in update_record tool."""
        self.tool.name = 'update_record'
        params = {
            'model': 'res.groups',
            'res_id': self.test_record.id,
            'values': {'name': 'Updated Group'}
        }
        result = self.tool.execute(params)
        self.assertTrue(result)
        self.assertEqual(self.test_record.name, 'Updated Group')

    def test_05_execute_builtin_delete(self):
        """Test built-in delete_record tool."""
        self.tool.name = 'delete_record'
        params = {
            'model': 'res.groups',
            'res_id': self.test_record.id
        }
        result = self.tool.execute(params)
        self.assertTrue(result['deleted'])
        self.assertFalse(self.test_record.exists())

    def test_06_execute_invalid_model(self):
        """Test execution with an invalid model name."""
        self.tool.name = 'search_records'
        params = {'model': 'invalid.model'}
        with self.assertRaises(UserError):
            self.tool.execute(params)
