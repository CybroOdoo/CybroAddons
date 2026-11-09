# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
"""Unit tests for project_dynamic_fields."""
from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'project_dynamic_fields')
class TestProjectDynamicFields(TransactionCase):
    """Test suite for project_dynamic_fields module."""
    # pylint: disable=protected-access

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProjectProject = cls.env['project.project']
        cls.IrModelFields = cls.env['ir.model.fields']
        cls.ProjectDynamicFields = cls.env['project.dynamic.fields']
        cls.group_custom_fields = cls.env.ref(
            'project_dynamic_fields.group_add_project_custom_fields'
        )
        cls.group_custom_fields.user_ids = [(4, cls.env.user.id)]
        cls.project_model_id = cls.env['ir.model'].search(
            [('model', '=', 'project.project')], limit=1
        )
        cls.existing_field = cls.IrModelFields.search([
            ('model_id', '=', cls.project_model_id.id),
            ('name', '=', 'name'),
        ], limit=1)

    def test_01_get_possible_field_types(self):
        """Test that excluded types are not in the list."""
        types = self.ProjectDynamicFields.get_possible_field_types()
        type_names = [t[0] for t in types]
        self.assertNotIn('one2many', type_names)
        self.assertNotIn('reference', type_names)
        self.assertNotIn('properties', type_names)
        self.assertIn('char', type_names)
        self.assertIn('boolean', type_names)

    def test_02_widget_id_domain(self):
        """Test computed widget_id_domain based on field_type."""
        wizard = self.ProjectDynamicFields.new({'field_type': 'binary'})
        wizard._compute_widget_id_domain()
        self.assertEqual(wizard.widget_id_domain[0][2], 'image')

        wizard = self.ProjectDynamicFields.new({'field_type': 'float'})
        wizard._compute_widget_id_domain()
        self.assertEqual(wizard.widget_id_domain[0][2], 'monetary')

        wizard = self.ProjectDynamicFields.new({'field_type': 'selection'})
        wizard._compute_widget_id_domain()
        self.assertIn('radio', wizard.widget_id_domain[0][2])

        wizard = self.ProjectDynamicFields.new({'field_type': 'many2many'})
        wizard._compute_widget_id_domain()
        self.assertIn('many2many_tags', wizard.widget_id_domain[0][2])

        wizard = self.ProjectDynamicFields.new({'field_type': 'many2one'})
        wizard._compute_widget_id_domain()
        self.assertEqual(wizard.widget_id_domain[0][2], 'selection')

        wizard = self.ProjectDynamicFields.new({'field_type': False})
        wizard._compute_widget_id_domain()
        self.assertEqual(wizard.widget_id_domain[0][2], False)

        # Test onchange resets widget_id
        widget = self.env['project.field.widgets'].search([], limit=1)
        wizard.widget_id = widget
        wizard._onchange_field_type()
        self.assertFalse(wizard.widget_id)

    def test_03_action_create_fields(self):
        """Test creating a dynamic field and its extension view."""
        wizard = self.ProjectDynamicFields.create({
            'name': 'x_test_char',
            'field_description': 'Test Char Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()

        field = self.IrModelFields.search([
            ('name', '=', 'x_test_char'),
            ('model_id', '=', self.project_model_id.id),
        ])
        self.assertTrue(field, "Dynamic field should exist in ir.model.fields")
        self.assertTrue(field.is_project_dynamic)

        view = wizard.form_view_id
        self.assertTrue(view, "Extension view should be created")
        self.assertEqual(view.model, 'project.project')
        self.assertTrue(view.active)

    def test_04_unlink_dynamic_fields(self):
        """Test unlinking a dynamic field and its view."""
        wizard = self.ProjectDynamicFields.create({
            'name': 'x_test_unlink',
            'field_description': 'Test Unlink Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()
        field = self.IrModelFields.search([
            ('name', '=', 'x_test_unlink'),
            ('model_id', '=', self.project_model_id.id),
        ])
        self.assertTrue(field)
        view = wizard.form_view_id
        self.assertTrue(view)
        self.assertTrue(view.active)

        # 1. Transient wizard vacuum/unlink should NOT delete the real field or view
        wizard.unlink()
        self.assertTrue(
            field.exists(),
            "Transient wizard unlink must NOT delete real ir.model.fields",
        )
        self.assertTrue(
            view.active,
            "Transient wizard unlink must NOT deactivate extension view",
        )

        # 2. Unlinking the ir.model.fields record deletes it and deactivates the view
        field.unlink()
        field_after = self.IrModelFields.search([
            ('name', '=', 'x_test_unlink'),
            ('model_id', '=', self.project_model_id.id),
        ])
        self.assertFalse(field_after)
        self.assertFalse(view.active)

        # 3. Fallback unlink when dynamic_form_view_id is False
        field_no_view = self.IrModelFields.sudo().create({
            'name': 'x_test_no_view_unlink',
            'field_description': 'No View Dynamic Field',
            'model_id': self.project_model_id.id,
            'ttype': 'char',
            'is_project_dynamic': True,
        })
        field_no_view.unlink()

    def test_05_project_project_dynamic_fields_read(self):
        """Test reading dynamic fields on project.project natively."""
        wizard = self.ProjectDynamicFields.create({
            'name': 'x_test_read_dyn',
            'field_description': 'Test Dynamic Read Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()

        project = self.ProjectProject.create({
            'name': 'Test Dynamic Project',
            'x_test_read_dyn': 'Value 123',
        })
        fields_info = project.fields_get()
        self.assertIn('x_test_read_dyn', fields_info)

        read_res = project.read(['name', 'x_test_read_dyn'])
        self.assertTrue(read_res)
        self.assertEqual(read_res[0].get('x_test_read_dyn'), 'Value 123')

    def test_06_set_domain_and_set_default(self):
        """Test domain helpers on dynamic field wizard."""
        wizard = self.ProjectDynamicFields.new()
        domain = wizard.set_domain()
        self.assertTrue(domain)
        default_model = wizard._set_default()
        self.assertEqual(default_model[0][2], self.project_model_id.id)

    def test_07_project_field_widgets_records(self):
        """Test project.field.widgets data records."""
        widgets = self.env['project.field.widgets'].search([])
        self.assertTrue(len(widgets) >= 5)
        widget_names = widgets.mapped('name')
        self.assertIn('image', widget_names)
        self.assertIn('many2many_tags', widget_names)
        self.assertIn('radio', widget_names)

    def test_08_security_group_restriction(self):
        """Test that unauthorized users without group cannot create dynamic fields."""
        standard_user = self.env['res.users'].create({
            'name': 'Standard Test User',
            'login': 'standard_user_proj_dyn',
        })
        with self.assertRaises(AccessError):
            self.ProjectDynamicFields.with_user(standard_user).create({
                'name': 'x_unauthorized_field',
                'field_description': 'Unauthorized',
                'model_id': self.project_model_id.id,
                'field_type': 'char',
                'position_field_id': self.existing_field.id,
                'position': 'after',
            })

    def test_09_project_field_widgets_readonly_for_standard_user(self):
        """Test that standard users can only read project.field.widgets."""
        standard_user = self.env['res.users'].create({
            'name': 'Standard User For Widget Check',
            'login': 'standard_user_widget_check',
        })
        widgets = self.env['project.field.widgets'].with_user(standard_user).search([])
        self.assertTrue(widgets, "Standard user should have read access to widgets")

        with self.assertRaises(AccessError):
            self.env['project.field.widgets'].with_user(standard_user).create({
                'name': 'malicious_widget',
                'description': 'Malicious Widget',
            })

        sample_widget = widgets[0]
        with self.assertRaises(AccessError):
            sample_widget.with_user(standard_user).write({
                'description': 'Tampered Description',
            })

        with self.assertRaises(AccessError):
            sample_widget.with_user(standard_user).unlink()

    def test_10_invalid_identifier_validation(self):
        """Test that dangerous or invalid field/widget names raise ValidationError."""
        with self.assertRaises(ValidationError):
            wizard = self.ProjectDynamicFields.create({
                'name': 'x_bad name" extra_attr="1',
                'field_description': 'Bad Field',
                'model_id': self.project_model_id.id,
                'field_type': 'char',
                'position_field_id': self.existing_field.id,
                'position': 'after',
            })
            wizard.action_create_fields()

        # Unsafe widget name
        malicious_widget = self.env['project.field.widgets'].sudo().create({
            'name': 'bad_widget" onclick="alert(1)',
            'description': 'Bad Widget',
        })
        wizard2 = self.ProjectDynamicFields.create({
            'name': 'x_valid_field_name',
            'field_description': 'Valid Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
            'widget_id': malicious_widget.id,
        })
        with self.assertRaises(ValidationError):
            wizard2.action_create_fields()

    def test_11_access_rules_ir_model_fields(self):
        """Test that group_add_project_custom_fields has read/delete access on dynamic fields."""
        access_rule = self.env['ir.access'].search([
            ('model_id.model', '=', 'ir.model.fields'),
            ('group_id', '=', self.group_custom_fields.id),
        ], limit=1)
        self.assertTrue(access_rule, "Access rule for ir.model.fields must exist.")
        self.assertEqual(access_rule.operation, 'rd', "Access rule must have 'rd' permission.")
        self.assertEqual(
            access_rule.domain,
            "[('is_project_dynamic', '=', True)]",
            "Access rule domain must limit access to project dynamic fields.",
        )

    def test_12_custom_field_user_permissions(self):
        """Test strict permissions (read & delete only) for custom field user."""
        custom_user = self.env['res.users'].create({
            'name': 'Custom Field User',
            'login': 'custom_field_user_test',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.group_custom_fields.id,
            ])],
        })

        # 1. User can create dynamic fields via wizard
        wizard = self.ProjectDynamicFields.with_user(custom_user).create({
            'name': 'x_test_user_field',
            'field_description': 'User Dynamic Field',
            'model_id': self.project_model_id.id,
            'field_type': 'char',
            'position_field_id': self.existing_field.id,
            'position': 'after',
        })
        wizard.action_create_fields()

        dyn_field = self.IrModelFields.search([
            ('name', '=', 'x_test_user_field'),
            ('model_id', '=', self.project_model_id.id),
        ])
        self.assertTrue(dyn_field)

        # 2. User can read dynamic fields
        read_data = dyn_field.with_user(custom_user).read(['name', 'field_description'])
        self.assertEqual(read_data[0]['name'], 'x_test_user_field')

        # 3. User cannot create ir.model.fields directly (no 'c' permission)
        with self.assertRaises(AccessError):
            self.IrModelFields.with_user(custom_user).create({
                'name': 'x_direct_create',
                'field_description': 'Direct Create',
                'model_id': self.project_model_id.id,
                'ttype': 'char',
                'is_project_dynamic': True,
            })

        # 4. User cannot write to ir.model.fields (no 'u' permission)
        with self.assertRaises(AccessError):
            dyn_field.with_user(custom_user).write({
                'field_description': 'Modified Description',
            })

        # 5. User cannot delete standard (non-dynamic) fields
        with self.assertRaises(AccessError):
            self.existing_field.with_user(custom_user).unlink()

        # 6. User can delete dynamic fields
        dyn_field.with_user(custom_user).unlink()
        self.assertFalse(dyn_field.exists())
