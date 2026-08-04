# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase

class TestTextCommander(TransactionCase):

    def setUp(self):
        super(TestTextCommander, self).setUp()
        self.ir_model = self.env['ir.model']

    def test_01_check_model(self):
        """Test check_model retrieves correct model by description"""
        result = self.ir_model.check_model('Contact')
        self.assertTrue(result)
        self.assertEqual(result[0]['model'], 'res.partner')

    def test_02_check_fields_model(self):
        """Test check_fields_model retrieves correct field by description on a model"""
        data = {
            'model': 'res.partner',
            'field_string': ['Name']
        }
        result = self.ir_model.check_fields_model(data)
        self.assertTrue(result)
        self.assertEqual(result[0]['name'], 'name')

    def test_03_get_records_regex_1(self):
        """Test get_records with regex 1 (search by name)"""
        group = self.env['res.groups'].create({'name': 'Test Commander Group'})
        data = {
            'regex': 1,
            'model': 'res.groups',
            'record': 'Test Commander Group'
        }
        result = self.ir_model.get_records(data)
        self.assertIn(group.id, result)

    def test_04_get_records_regex_2_selection(self):
        """Test get_records with regex 2 for a selection field"""
        module = self.env['ir.module.module'].search([('state', '=', 'installed')], limit=1)
        data = {
            'regex': 2,
            'model': 'ir.module.module',
            'field_type': 'selection',
            'field': 'state',
            'field_string': 'Installed' # Label for 'installed' state
        }
        result = self.ir_model.get_records(data)
        if module:
            self.assertIn(module.id, result)
        else:
            self.assertTrue(True) # Fallback if no installed module found during tests (unlikely)

    def test_05_get_records_regex_2_many2one(self):
        """Test get_records with regex 2 for a many2one field"""
        company = self.env['res.company'].search([], limit=1)
        user = self.env['res.users'].search([('company_id', '=', company.id)], limit=1)
        data = {
            'regex': 2,
            'model': 'res.users',
            'field_type': 'many2one',
            'field_relation': 'res.company',
            'field': 'company_id',
            'field_string': str(company.name) if company else ''
        }
        result = self.ir_model.get_records(data)
        if company and user:
            self.assertIn(user.id, result)
        else:
            self.assertTrue(True)
