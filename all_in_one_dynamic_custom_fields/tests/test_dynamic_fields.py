# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestDynamicFields(TransactionCase):
    """Test cases for the DynamicFields model (dynamic.fields)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Get res.bank model
        cls.bank_model = cls.env['ir.model'].search([('model', '=', 'res.bank')], limit=1)

        # Get a position field (e.g. name field on bank)
        cls.position_field = cls.env['ir.model.fields'].search([
            ('model', '=', 'res.bank'),
            ('name', '=', 'name')
        ], limit=1)

        # Get standard bank form and tree views
        cls.bank_form_view = cls.env.ref('base.view_res_bank_form')
        cls.bank_tree_view = cls.env.ref('base.view_res_bank_tree')

        # Create a dynamic field widget
        cls.widget = cls.env['dynamic.field.widgets'].create({
            'name': 'char_widget',
            'data_type': 'char',
            'description': 'Char Widget',
        })

    def test_onchange_model_id(self):
        """Test _onchange_model_id computes model name and view lists."""
        dynamic_field = self.env['dynamic.fields'].create({
            'name': 'x_test_onchange',
            'field_description': 'Test Onchange',
            'model_id': self.bank_model.id,
            'field_type': 'char',
            'position_field_id': self.position_field.id,
            'position': 'after',
            'form_view_id': self.bank_form_view.id,
        })

        dynamic_field._onchange_model_id()

        self.assertEqual(dynamic_field.model, 'res.bank')
        self.assertIn(self.bank_form_view, dynamic_field.form_view_ids)
        self.assertIn(self.bank_tree_view, dynamic_field.tree_view_ids)

    def test_action_create_dynamic_field_without_tree(self):
        """Test action_create_dynamic_field creates a custom field and inherited form view."""
        dynamic_field = self.env['dynamic.fields'].create({
            'name': 'x_test_field_form',
            'field_description': 'Test Field Form',
            'model_id': self.bank_model.id,
            'field_type': 'char',
            'position_field_id': self.position_field.id,
            'position': 'after',
            'form_view_id': self.bank_form_view.id,
            'widget_id': self.widget.id,
            'add_field_in_tree': False,
        })

        # Run creation
        dynamic_field.action_create_dynamic_field()

        # Check status changed
        self.assertEqual(dynamic_field.status, 'form')

        # Check ir.model.fields record is created
        custom_field = self.env['ir.model.fields'].search([
            ('model', '=', 'res.bank'),
            ('name', '=', 'x_test_field_form')
        ])
        self.assertTrue(custom_field.exists(), "Custom field should exist in ir.model.fields.")
        self.assertTrue(custom_field.is_dynamic_field, "is_dynamic_field should be set to True.")

        # Check inherited form view is created
        form_view = dynamic_field.created_form_view_id
        self.assertTrue(form_view.exists(), "Form view extension should be created.")
        self.assertEqual(form_view.type, 'form')
        self.assertEqual(form_view.model, 'res.bank')
        self.assertEqual(form_view.mode, 'extension')
        self.assertTrue(form_view.active)
        self.assertIn('x_test_field_form', form_view.arch_base)
        self.assertIn('widget="char_widget"', form_view.arch_base)

    def test_action_create_dynamic_field_with_tree(self):
        """Test action_create_dynamic_field creates custom field, form view, and tree view."""
        dynamic_field = self.env['dynamic.fields'].create({
            'name': 'x_test_field_tree',
            'field_description': 'Test Field Tree',
            'model_id': self.bank_model.id,
            'field_type': 'char',
            'position_field_id': self.position_field.id,
            'position': 'after',
            'form_view_id': self.bank_form_view.id,
            'add_field_in_tree': True,
            'tree_view_id': self.bank_tree_view.id,
        })

        # Compute tree field ids and set tree field
        dynamic_field._compute_tree_field_ids()
        self.assertTrue(dynamic_field.tree_field_ids, "Candidate tree fields should be found.")

        # Set first candidate field as anchor
        dynamic_field.tree_field_id = dynamic_field.tree_field_ids[0].id
        dynamic_field.tree_field_position = 'after'
        dynamic_field.is_visible_in_tree_view = True

        # Run creation
        dynamic_field.action_create_dynamic_field()

        # Check custom tree view is created
        tree_view = dynamic_field.created_tree_view_id
        self.assertTrue(tree_view.exists(), "Tree/List view extension should be created.")
        self.assertEqual(tree_view.type, 'list')
        self.assertEqual(tree_view.model, 'res.bank')
        self.assertEqual(tree_view.mode, 'extension')
        self.assertTrue(tree_view.active)
        self.assertIn('x_test_field_tree', tree_view.arch_base)
        self.assertIn('optional="show"', tree_view.arch_base)

    def test_unlink_deactivates_views(self):
        """Test that unlinking a dynamic field deactivates its form and tree views."""
        dynamic_field = self.env['dynamic.fields'].create({
            'name': 'x_test_field_unlink',
            'field_description': 'Test Field Unlink',
            'model_id': self.bank_model.id,
            'field_type': 'char',
            'position_field_id': self.position_field.id,
            'position': 'after',
            'form_view_id': self.bank_form_view.id,
            'add_field_in_tree': True,
            'tree_view_id': self.bank_tree_view.id,
        })

        dynamic_field._compute_tree_field_ids()
        dynamic_field.tree_field_id = dynamic_field.tree_field_ids[0].id
        dynamic_field.tree_field_position = 'after'

        # Create
        dynamic_field.action_create_dynamic_field()

        form_view = dynamic_field.created_form_view_id
        tree_view = dynamic_field.created_tree_view_id

        self.assertTrue(form_view.active)
        self.assertTrue(tree_view.active)

        # Unlink/delete
        dynamic_field.unlink()

        # Verify views are deactivated
        self.assertFalse(form_view.active, "Form view should be deactivated.")
        self.assertFalse(tree_view.active, "Tree view should be deactivated.")
