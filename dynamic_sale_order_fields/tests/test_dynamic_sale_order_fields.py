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
#############################################################################
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import AccessError, UserError


@tagged('post_install', '-at_install')
class TestDynamicSaleOrderFields(TransactionCase):
    """Test suite for validating the dynamic sale order fields module logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Find the sale.order model
        cls.sale_order_model = cls.env['ir.model'].search([('model', '=', 'sale.order')], limit=1)

        # Find a field from sale.order that is present in the standard sale.view_order_form
        cls.position_field = cls.env['ir.model.fields'].search([
            ('model_id', '=', cls.sale_order_model.id),
            ('name', '=', 'partner_id')
        ], limit=1)

        # Ensure the test admin user has the custom fields group
        cls.custom_field_group = cls.env.ref('dynamic_sale_order_fields.group_add_sale_custom_fields')
        cls.env.user.write({'group_ids': [(4, cls.custom_field_group.id)]})

    def test_01_widget_creation_and_retrieval(self):
        """Verify that field.widget records exist and properties are retrieved correctly."""
        # Verify that default widgets from data/field_widget_data.xml were loaded
        widgets = self.env['field.widget'].search([])
        self.assertTrue(widgets, "Default widgets should be loaded in the database.")

        # Test searching for a specific widget, e.g., 'many2many_binary'
        binary_widget = self.env['field.widget'].search([('name', '=', 'many2many_binary')], limit=1)
        self.assertTrue(binary_widget, "The 'many2many_binary' widget should exist.")
        self.assertEqual(binary_widget.data_type, 'many2many', "The data_type for many2many_binary widget must be 'many2many'.")

    def test_02_ir_model_fields_inheritance(self):
        """Verify the inherited 'is_dynamic' boolean field exists in ir.model.fields."""
        self.assertIn('is_dynamic', self.env['ir.model.fields']._fields, "'is_dynamic' field should exist on ir.model.fields.")

        # Test default is_dynamic value for a standard system field
        self.assertFalse(self.position_field.is_dynamic, "Standard fields should not be marked as dynamic (is_dynamic=False).")

    def test_03_wizard_helpers(self):
        """Verify the helper methods: get_possible_field_types, set_domain, and _set_default."""
        # Instantiate a new wizard record in-memory
        wizard = self.env['sale.order.dynamic.field'].new()

        # 1. Test get_possible_field_types()
        types = wizard.get_possible_field_types()
        type_keys = [t[0] for t in types]
        self.assertIn('char', type_keys, "'char' type should be returned as a possible field type.")
        self.assertNotIn('one2many', type_keys, "'one2many' should be excluded from possible field types.")
        self.assertNotIn('reference', type_keys, "'reference' should be excluded from possible field types.")

        # 2. Test _set_default()
        default_model = wizard._set_default()
        self.assertEqual(default_model, [('id', '=', self.sale_order_model.id)], "The default model domain should restrict to 'sale.order'.")

        # 3. Test set_domain()
        domain = wizard.set_domain()
        self.assertEqual(domain[0], ('model_id', '=', self.sale_order_model.id), "Domain should filter by sale.order model ID.")
        self.assertEqual(domain[1], ('state', '=', 'base'), "Domain should filter for base/standard fields.")
        self.assertEqual(domain[2][0], 'name', "Domain should filter field names.")
        self.assertEqual(domain[2][1], 'in', "Domain should use the 'in' operator.")
        # 'partner_id' is a field present on the standard sale order form view, so it should be in the list of field names.
        self.assertIn('partner_id', domain[2][2], "'partner_id' should be included in the domain field names list.")

    def test_04_wizard_onchanges(self):
        """Verify the widget and ref_model_id interactive behavior (onchanges)."""
        attachment_model = self.env.ref('base.model_ir_attachment')
        partner_model = self.env.ref('base.model_res_partner')

        # Locate the 'many2many_binary' widget
        m2m_binary_widget = self.env['field.widget'].search([('name', '=', 'many2many_binary')], limit=1)
        self.assertTrue(m2m_binary_widget, "The 'many2many_binary' widget must be loaded.")

        # Instantiate a wizard in-memory
        wizard = self.env['sale.order.dynamic.field'].new({
            'widget': m2m_binary_widget.id,
            'field_type': 'many2many',
        })

        # Trigger widget onchange
        wizard._onchange_widget()
        self.assertEqual(wizard.ref_model_id, attachment_model, "Selecting 'many2many_binary' widget should set ref_model_id to ir.attachment.")

        # Trigger ref_model_id onchange with incorrect model
        wizard.ref_model_id = partner_model
        with self.assertRaises(UserError, msg="Choosing a non-Attachment model for many2many_binary widget should raise a UserError."):
            wizard._onchange_ref_model_id()

    def test_05_create_simple_field(self):
        """Verify the wizard successfully creates a simple Char custom field and updates the sale order view."""
        wizard = self.env['sale.order.dynamic.field'].create({
            'name': 'x_test_char_field',
            'field_description': 'Test Custom Char Field',
            'model_id': self.sale_order_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })

        # Call the create_fields wizard action
        action = wizard.create_fields()
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'reload')

        # Check if the field was created in ir.model.fields
        created_field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.sale_order_model.id),
            ('name', '=', 'x_test_char_field')
        ], limit=1)
        self.assertTrue(created_field, "The custom field 'x_test_char_field' should be created.")
        self.assertTrue(created_field.is_dynamic, "The field should have is_dynamic=True.")
        self.assertEqual(created_field.ttype, 'char')

        # Verify that an inherited/extension view was created
        extension_view = self.env['ir.ui.view'].search([
            ('model', '=', 'sale.order'),
            ('mode', '=', 'extension'),
            ('inherit_id', '=', self.env.ref('sale.view_order_form').id),
            ('name', '=', 'sale.order.dynamic.field')
        ], order='id desc', limit=1)
        self.assertTrue(extension_view, "An extension view should be created.")
        self.assertIn('x_test_char_field', extension_view.arch_base, "The view arch should contain the new custom field name.")

    def test_06_create_field_with_widget(self):
        """Verify the wizard successfully creates a custom field with a specific widget."""
        m2m_binary_widget = self.env['field.widget'].search([('name', '=', 'many2many_binary')], limit=1)
        attachment_model = self.env.ref('base.model_ir_attachment')

        wizard = self.env['sale.order.dynamic.field'].create({
            'name': 'x_test_m2m_field',
            'field_description': 'Test Custom M2M Field',
            'model_id': self.sale_order_model.id,
            'field_type': 'many2many',
            'ref_model_id': attachment_model.id,
            'widget': m2m_binary_widget.id,
            'position_field': self.position_field.id,
            'position': 'before',
        })

        # Call the create_fields wizard action
        action = wizard.create_fields()
        self.assertEqual(action.get('type'), 'ir.actions.client')

        # Check if the field was created
        created_field = self.env['ir.model.fields'].search([
            ('model_id', '=', self.sale_order_model.id),
            ('name', '=', 'x_test_m2m_field')
        ], limit=1)
        self.assertTrue(created_field, "The custom field 'x_test_m2m_field' should be created.")
        self.assertEqual(created_field.ttype, 'many2many')
        self.assertEqual(created_field.relation, 'ir.attachment')

        # Check that the view contains the widget attribute
        extension_view = self.env['ir.ui.view'].search([
            ('model', '=', 'sale.order'),
            ('mode', '=', 'extension'),
            ('inherit_id', '=', self.env.ref('sale.view_order_form').id),
            ('name', '=', 'sale.order.dynamic.field')
        ], order='id desc', limit=1)
        self.assertTrue(extension_view, "An extension view should be created.")
        self.assertIn('widget="many2many_binary"', extension_view.arch_base, "The view arch should contain the widget specification.")

    def test_07_access_rights_and_security(self):
        """Verify that only authorized users can execute create_fields and non-admin users cannot write to field.widget."""
        # Create standard user without group_add_sale_custom_fields
        standard_user = self.env['res.users'].create({
            'name': 'Standard Test User',
            'login': 'standard_test_user',
            'email': 'standard@example.com',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })

        wizard = self.env['sale.order.dynamic.field'].create({
            'name': 'x_test_unauthorized_field',
            'field_description': 'Test Unauthorized Field',
            'model_id': self.sale_order_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })

        # User without group should be blocked from create_fields
        with self.assertRaises(AccessError, msg="Users without group_add_sale_custom_fields should not be allowed to create custom fields."):
            wizard.with_user(standard_user).create_fields()

        # Standard internal user should not be able to create new field.widget records
        with self.assertRaises(AccessError, msg="Standard users should not have write/create access on field.widget."):
            self.env['field.widget'].with_user(standard_user).create({
                'name': 'test_widget',
                'description': 'Test Widget',
                'data_type': 'char',
            })

    def test_08_model_id_validation(self):
        """Verify server-side validation that model_id must be sale.order."""
        partner_model = self.env.ref('base.model_res_partner')
        wizard = self.env['sale.order.dynamic.field'].create({
            'name': 'x_test_wrong_model',
            'field_description': 'Wrong Model Field',
            'model_id': partner_model.id,
            'field_type': 'char',
            'position_field': self.position_field.id,
            'position': 'after',
        })

        with self.assertRaises(UserError, msg="Attempting to create a custom field on a non-sale.order model should raise UserError."):
            wizard.create_fields()

    def test_09_widget_domain_and_field_type_onchange(self):
        """Verify dynamic widget filtering and field_type reset logic."""
        # Verify that widget field has dynamic domain string
        widget_field = self.env['sale.order.dynamic.field']._fields['widget']
        self.assertEqual(widget_field.domain, "[('data_type', '=', field_type)]")

        m2m_binary_widget = self.env['field.widget'].search([('name', '=', 'many2many_binary')], limit=1)
        wizard = self.env['sale.order.dynamic.field'].new({
            'field_type': 'many2many',
            'widget': m2m_binary_widget.id,
        })
        self.assertEqual(wizard.widget, m2m_binary_widget)

        # Changing field_type to 'char' should clear incompatible widget
        wizard.field_type = 'char'
        wizard._onchange_field_type()
        self.assertFalse(wizard.widget, "Changing field_type should clear incompatible widget.")

    def test_10_invalid_field_types_excluded(self):
        """Verify invalid or unsupported field types are not returned in get_possible_field_types."""
        types = self.env['sale.order.dynamic.field'].get_possible_field_types()
        type_keys = [t[0] for t in types]
        invalid_types = ['id', 'many2onereference', 'propertiesdefinition', 'properties', 'command', 'one2many', 'reference']
        for inv_type in invalid_types:
            self.assertNotIn(inv_type, type_keys, f"Invalid or unsupported type '{inv_type}' should not be in possible field types.")
