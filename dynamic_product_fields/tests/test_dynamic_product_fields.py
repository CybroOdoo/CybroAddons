# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDynamicProductFields(TransactionCase):
    """Unit and integration tests for Dynamic Product Fields module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_model = cls.env['ir.model'].search([('model', '=', 'product.template')], limit=1)
        cls.position_field = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.product_model.id),
            ('name', '=', 'name'),
        ], limit=1)
        group_user = cls.env.ref('dynamic_product_fields.dynamic_product_fields_user')
        cls.env.user.group_ids = [(4, group_user.id)]

    def test_01_module_installed_and_widgets_loaded(self):
        """Verify module is installed and default widget data records exist."""
        module = self.env['ir.module.module'].search([('name', '=', 'dynamic_product_fields')])
        self.assertTrue(module, "Module dynamic_product_fields must be found.")
        self.assertEqual(module.state, 'installed', "Module dynamic_product_fields must be installed.")

        widgets = self.env['field.widget'].search([])
        self.assertGreaterEqual(len(widgets), 5, "Default widgets should be preloaded.")
        image_widget = self.env.ref('dynamic_product_fields.field_widgets_image_widget', raise_if_not_found=False)
        self.assertTrue(image_widget, "Image widget record must exist.")
        self.assertEqual(image_widget.data_type, 'binary')

    def test_02_wizard_domain_and_types(self):
        """Test wizard domain methods and possible field types."""
        wizard = self.env['product.dynamic.fields'].create({
            'name': 'test_temp_field',
            'field_description': 'Test Temp Field',
            'model_id': self.product_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })
        types = wizard.get_possible_field_types()
        type_keys = [t[0] for t in types]
        self.assertIn('char', type_keys)
        self.assertIn('integer', type_keys)
        self.assertIn('boolean', type_keys)
        self.assertIn('many2one', type_keys)
        self.assertNotIn('one2many', type_keys)

        domain = wizard.set_domain()
        self.assertTrue(any(item[0] == 'model_id' for item in domain))
        model_domain = wizard._get_model_domain()
        self.assertEqual(model_domain, [('id', '=', self.product_model.id)])

    def test_03_wizard_onchange_many2many_binary(self):
        """Test onchange handlers for many2many_binary widget."""
        m2m_binary_widget = self.env.ref(
            'dynamic_product_fields.field_widgets_many2many_binary_widget',
            raise_if_not_found=False,
        )
        if not m2m_binary_widget:
            m2m_binary_widget = self.env['field.widget'].create({
                'name': 'many2many_binary',
                'description': 'Many2many Binary',
                'data_type': 'many2many',
            })

        wizard = self.env['product.dynamic.fields'].new({
            'name': 'test_binary_m2m',
            'field_description': 'Test Binary M2M',
            'model_id': self.product_model.id,
            'field_type': 'many2many',
            'widget': m2m_binary_widget.id,
        })
        wizard._onchange_widget()
        attachment_model = self.env.ref('base.model_ir_attachment')
        self.assertEqual(wizard.ref_model_id, attachment_model)

        # Trigger wrong model validation warning
        wizard.ref_model_id = self.product_model
        res = wizard._onchange_ref_model_id()
        self.assertIsInstance(res, dict)
        self.assertIn('warning', res)

    def test_04_create_dynamic_char_field(self):
        """Verify dynamic creation of a custom char field and inherited view."""
        wizard = self.env['product.dynamic.fields'].create({
            'name': 'test_custom_color',
            'field_description': 'Test Custom Color',
            'model_id': self.product_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })
        res = wizard.create_fields()
        self.assertEqual(res.get('type'), 'ir.actions.client')

        field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.product_model.id),
            ('name', '=', 'x_test_custom_color'),
        ], limit=1)
        self.assertTrue(field, "Dynamic field x_test_custom_color must be created in ir.model.fields.")
        self.assertTrue(field.is_dynamic, "is_dynamic flag must be True.")

        view = self.env['ir.ui.view'].search([
            ('name', '=', 'product.template.dynamic.x_test_custom_color'),
        ], limit=1)
        self.assertTrue(view, "Inherited view for dynamic field must be created.")
        self.assertIn('x_test_custom_color', view.arch_base or view.arch)

    def test_05_create_dynamic_selection_field_with_widget(self):
        """Verify dynamic creation of a selection field with priority widget."""
        priority_widget = self.env.ref(
            'dynamic_product_fields.field_widgets_priority_widget',
            raise_if_not_found=False,
        )
        wizard = self.env['product.dynamic.fields'].create({
            'name': 'test_custom_priority',
            'field_description': 'Test Custom Priority',
            'model_id': self.product_model.id,
            'field_type': 'selection',
            'selection_field': "[('0', 'Low'), ('1', 'Normal'), ('2', 'High')]",
            'widget': priority_widget.id if priority_widget else False,
            'position_field': self.position_field.id,
            'position': 'after',
        })
        wizard.create_fields()

        field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.product_model.id),
            ('name', '=', 'x_test_custom_priority'),
        ], limit=1)
        self.assertTrue(field, "Dynamic field x_test_custom_priority must be created.")
        self.assertTrue(field.is_dynamic)

    def test_06_security_groups_and_privileges(self):
        """Verify module security groups and privileges."""
        group = self.env.ref('dynamic_product_fields.dynamic_product_fields_user', raise_if_not_found=False)
        self.assertTrue(group, "User group dynamic_product_fields_user must exist.")
        category = self.env.ref('dynamic_product_fields.module_dynamic_product_field', raise_if_not_found=False)
        self.assertTrue(category, "Module category must exist.")
        self.assertIn("Product Custom Fields", category.description)

    def test_07_unauthorized_user_cannot_create_fields(self):
        """Verify user without dynamic_product_fields_user group cannot create fields."""
        unauthorized_user = self.env['res.users'].create({
            'name': 'Unauthorized User',
            'login': 'unauthorized_dynamic_user',
            'email': 'unauth@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        wizard = self.env['product.dynamic.fields'].create({
            'name': 'test_unauth_field',
            'field_description': 'Test Unauth Field',
            'model_id': self.product_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })
        with self.assertRaises(AccessError):
            wizard.with_user(unauthorized_user).create_fields()

        with self.assertRaises(AccessError):
            self.env['product.dynamic.fields'].with_user(unauthorized_user).create({
                'name': 'test_unauth_create',
                'field_description': 'Test',
                'model_id': self.product_model.id,
                'field_type': 'char',
                'position_field': self.position_field.id,
                'position': 'after',
            })

    def test_08_invalid_model_rejected(self):
        """Verify attempting to create fields on non-product model is rejected."""
        partner_model = self.env['ir.model'].search([('model', '=', 'res.partner')], limit=1)
        partner_field = self.env['ir.model.fields'].search([
            ('model_id', '=', partner_model.id),
            ('name', '=', 'name'),
        ], limit=1)
        wizard = self.env['product.dynamic.fields'].create({
            'name': 'test_invalid_model_field',
            'field_description': 'Test Invalid Model Field',
            'model_id': partner_model.id,
            'field_type': 'char',
            'position_field': partner_field.id,
            'position': 'after',
        })
        with self.assertRaises(UserError):
            wizard.create_fields()

