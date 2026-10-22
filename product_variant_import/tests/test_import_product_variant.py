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
"""Test suite for product_variant_import wizard, security, and actions."""
import base64
from odoo.exceptions import AccessError, UserError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestImportProductVariant(TransactionCase):
    """Unit tests for the Import Product Variant wizard and security."""

    @classmethod
    def setUpClass(cls):
        """Set up manager group and internal test user."""
        super().setUpClass()
        cls.manager_group = cls.env.ref(
            'product_variant_import.product_variant_access'
        )
        cls.test_user = cls.env['res.users'].create({
            'name': 'Test Variant User',
            'login': 'test_variant_user',
            'email': 'variant_user@test.com',
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])],
        })

    def test_01_wizard_fields_and_defaults(self):
        """Verify field definitions and selection options on wizard."""
        wizard_model = self.env['import.product.variant']
        import_file_selection = [
            item[0] for item in wizard_model._fields['import_file'].selection
        ]
        self.assertIn('csv', import_file_selection)
        self.assertIn('excel', import_file_selection)

        method_selection = [
            item[0] for item in wizard_model._fields['method'].selection
        ]
        self.assertIn('create', method_selection)
        self.assertIn('update', method_selection)
        self.assertIn('update_product', method_selection)

    def test_02_action_import_missing_file(self):
        """Verify action_import_product_variant raises UserError if no file."""
        wizard = self.env['import.product.variant'].new({
            'import_file': 'csv',
            'method': 'create',
            'file': False,
        })
        with self.assertRaises(UserError) as error:
            wizard.action_import_product_variant()
        self.assertIn("Please select a file to upload.", str(error.exception))

    def test_03_action_import_csv_create_product(self):
        """Verify wizard creates base_import and returns client action."""
        sample_csv = base64.b64encode(
            b"name,barcode\nWidget A,123456\n"
        ).decode('utf-8')
        wizard = self.env['import.product.variant'].create({
            'import_file': 'csv',
            'method': 'create',
            'file': sample_csv,
            'filename': 'my_products.csv',
        })
        res = wizard.action_import_product_variant()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get('type'), 'ir.actions.client')
        self.assertEqual(res.get('tag'), 'import')

        params = res.get('params', {})
        self.assertEqual(params.get('model'), 'product.template')
        self.assertEqual(params.get('file_name'), 'my_products.csv')

        import_id = params.get('import_id')
        self.assertTrue(import_id)
        base_import = self.env['base_import.import'].browse(import_id)
        self.assertTrue(base_import.exists())
        self.assertEqual(base_import.res_model, 'product.template')
        self.assertEqual(base_import.file_type, 'text/csv')

    def test_04_action_import_csv_default_filename(self):
        """Verify default CSV filename when filename is not specified."""
        sample_csv = base64.b64encode(b"name\nWidget B\n").decode('utf-8')
        wizard = self.env['import.product.variant'].create({
            'import_file': 'csv',
            'method': 'update',
            'file': sample_csv,
            'filename': False,
        })
        res = wizard.action_import_product_variant()
        params = res.get('params', {})
        self.assertEqual(params.get('file_name'), 'import_file.csv')
        self.assertEqual(params.get('model'), 'product.template')

    def test_05_action_import_excel_update_product_variant(self):
        """Verify Excel upload targeting product.product model."""
        sample_data = base64.b64encode(
            b"dummy excel binary stream"
        ).decode('utf-8')
        wizard = self.env['import.product.variant'].create({
            'import_file': 'excel',
            'method': 'update_product',
            'file': sample_data,
            'filename': False,
        })
        res = wizard.action_import_product_variant()
        params = res.get('params', {})
        self.assertEqual(params.get('model'), 'product.product')
        self.assertEqual(params.get('file_name'), 'import_file.xlsx')

        import_id = params.get('import_id')
        base_import = self.env['base_import.import'].browse(import_id)
        self.assertEqual(base_import.res_model, 'product.product')
        self.assertEqual(
            base_import.file_type,
            'application/vnd.openxmlformats-officedocument.'
            'spreadsheetml.sheet',
        )

    def test_06_security_group_and_access_rights(self):
        """Verify user without product_variant_access cannot use wizard."""
        sample_csv = base64.b64encode(b"name\nWidget C\n").decode('utf-8')
        # User without manager group should be denied access
        with self.assertRaises(AccessError):
            self.env['import.product.variant'].with_user(
                self.test_user
            ).create({
                'import_file': 'csv',
                'method': 'create',
                'file': sample_csv,
            })

        # Add user to manager group
        self.test_user.write({
            'group_ids': [(4, self.manager_group.id)],
        })

        # User should now be granted access
        wizard = self.env['import.product.variant'].with_user(
            self.test_user
        ).create({
            'import_file': 'csv',
            'method': 'create',
            'file': sample_csv,
        })
        self.assertTrue(wizard.id)
        res = wizard.action_import_product_variant()
        self.assertEqual(res.get('tag'), 'import')

    def test_07_menu_and_action_configuration(self):
        """Verify menuitem and window action configuration."""
        menu = self.env.ref(
            'product_variant_import.import_product_variant_menu_action'
        )
        self.assertEqual(
            menu.parent_id,
            self.env.ref('stock.menu_stock_inventory_control'),
        )
        self.assertIn(self.manager_group, menu.group_ids)

        action = self.env.ref(
            'product_variant_import.import_product_variant_action'
        )
        self.assertEqual(action.res_model, 'import.product.variant')
        self.assertEqual(action.view_mode, 'form')
        self.assertEqual(action.target, 'new')
