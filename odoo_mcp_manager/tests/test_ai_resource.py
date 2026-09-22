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

class TestAiResource(TransactionCase):

    def setUp(self):
        super(TestAiResource, self).setUp()
        self.resource = self.env['ai.resource'].create({
            'name': 'Partners',
            'model_name': 'res.partner',
        })

    def test_01_uri_computation(self):
        """Test odoo:// URI generation."""
        self.assertEqual(self.resource.uri, 'odoo://res.partner')

    def test_02_model_exists_computation(self):
        """Test model availability check."""
        self.assertTrue(self.resource.model_exists)
        self.resource.model_name = 'non.existent.model'
        self.assertFalse(self.resource.model_exists)

    def test_03_record_count_computation(self):
        """Test record count calculation safety."""
        # Create a few partners
        self.env['res.partner'].create([{'name': 'A'}, {'name': 'B'}])
        self.resource._compute_record_count()
        self.assertGreaterEqual(self.resource.record_count, 2)

    def test_04_mcp_definition(self):
        """Test MCP descriptor output."""
        defn = self.resource.mcp_definition()
        self.assertEqual(defn['uri'], 'odoo://res.partner')
        self.assertEqual(defn['name'], 'Partners')
        self.assertEqual(defn['mimeType'], 'application/json')
