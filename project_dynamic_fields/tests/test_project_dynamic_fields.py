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

class TestProjectDynamicFields(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env
        cls.ProjectProject = cls.env['project.project']
        cls.IrModelFields = cls.env['ir.model.fields']
        cls.ProjectDynamicFields = cls.env['project.dynamic.fields']
        cls.project_model_id = cls.env['ir.model'].search([('model', '=', 'project.project')], limit=1)
        cls.existing_field = cls.IrModelFields.search([('model_id', '=', cls.project_model_id.id), ('name', '=', 'name')], limit=1)

    def test_01_get_possible_field_types(self):
        """Test that excluded types are not in the list"""
        types = self.ProjectDynamicFields.get_possible_field_types()
        type_names = [t[0] for t in types]
        self.assertNotIn('one2many', type_names)
        self.assertNotIn('reference', type_names)
        self.assertNotIn('properties', type_names)

    def test_02_onchange_field_type(self):
        """Test onchange for field type returns correct widget domains"""
        wizard = self.ProjectDynamicFields.new({'field_type': 'binary'})
        domain = wizard.onchange_field_type()
        self.assertEqual(domain.get('domain', {}).get('widget', [])[0][2], 'image')
        
        wizard = self.ProjectDynamicFields.new({'field_type': 'float'})
        domain = wizard.onchange_field_type()
        self.assertEqual(domain.get('domain', {}).get('widget', [])[0][2], 'monetary')

    def test_03_action_create_fields(self):
        """Test creating a dynamic field"""
        wizard = self.ProjectDynamicFields.create({
            'name': 'x_test_char',
            'field_description': 'Test Char Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()
        
        # Check if the field was created
        field = self.IrModelFields.search([('name', '=', 'x_test_char'), ('model_id', '=', self.project_model_id.id)])
        self.assertTrue(field)
        self.assertTrue(field.is_project_dynamic)
        
        # Check if view was created
        view = wizard.form_view_id
        self.assertTrue(view)
        self.assertEqual(view.model, 'project.project')
        
    def test_04_unlink_dynamic_fields(self):
        """Test unlinking a dynamic field and its view"""
        wizard = self.ProjectDynamicFields.create({
            'name': 'x_test_unlink',
            'field_description': 'Test Unlink Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()
        field = self.IrModelFields.search([('name', '=', 'x_test_unlink'), ('model_id', '=', self.project_model_id.id)])
        self.assertTrue(field)
        view = wizard.form_view_id
        self.assertTrue(view)
        
        wizard.unlink()
        
        # Check if field was deleted
        field_after = self.IrModelFields.search([('name', '=', 'x_test_unlink'), ('model_id', '=', self.project_model_id.id)])
        self.assertFalse(field_after)
        # Check if view was deactivated
        self.assertFalse(view.active)
