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
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.dynamic_product_label_print.report.product_barcode_report import (
    _get_product_field_val,
    _prepare_datas,
)


@tagged('post_install', '-at_install')
class TestDynamicProductLabel(TransactionCase):
    """Test suite for Dynamic Product Label Printing."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test Label Category',
        })
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Label Product Template',
            'list_price': 49.99,
            'default_code': 'TLPT-01',
            'barcode': '1234567890128',
            'categ_id': cls.category.id,
        })
        cls.product = cls.product_tmpl.product_variant_ids[0]

        # Field definitions from ir.model.fields
        cls.field_name = cls.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'name'),
        ], limit=1)
        cls.field_price = cls.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'list_price'),
        ], limit=1)
        cls.field_categ = cls.env['ir.model.fields'].search([
            ('model', '=', 'product.product'),
            ('name', '=', 'categ_id'),
        ], limit=1)

        # Dynamic template
        cls.template = cls.env['dynamic.template'].create({
            'name': 'Standard Retail Label',
            'bc_height': 25,
            'bc_width': 45,
        })

        # Dynamic fields linked to template
        cls.d_field_name = cls.env['dynamic.fields'].create({
            'template_id': cls.template.id,
            'fd_name_id': cls.field_name.id,
            'size': '16px',
            'color': '#111111',
        })
        cls.d_field_price = cls.env['dynamic.fields'].create({
            'template_id': cls.template.id,
            'fd_name_id': cls.field_price.id,
            'size': '14px',
            'color': '#008800',
        })
        cls.d_field_categ = cls.env['dynamic.fields'].create({
            'template_id': cls.template.id,
            'fd_name_id': cls.field_categ.id,
            'size': '12px',
            'color': '#555555',
        })

    def test_01_dynamic_template_creation(self):
        """Verify dynamic template and dynamic fields attributes."""
        self.assertEqual(self.template.name, 'Standard Retail Label')
        self.assertEqual(self.template.bc_height, 25)
        self.assertEqual(self.template.bc_width, 45)
        self.assertEqual(len(self.template.dynamic_field_ids), 3)

        # Check default integer dimensions on a new template
        default_tmpl = self.env['dynamic.template'].create({
            'name': 'Default Dimension Template',
        })
        self.assertEqual(default_tmpl.bc_height, 15)
        self.assertEqual(default_tmpl.bc_width, 30)

        # Check related field_type on dynamic.fields
        self.assertEqual(self.d_field_name.field_type, self.field_name.ttype)
        self.assertEqual(self.d_field_price.field_type, self.field_price.ttype)

    def test_02_wizard_prepare_report_data_template(self):
        """Test wizard report data preparation with product.template."""
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, [self.product_tmpl.id])],
            'print_format': 'dynamic_template',
            'dynamic_template_id': self.template.id,
            'custom_quantity': 4,
        })
        wizard._onchange_dynamic_template_id()
        self.assertEqual(
            set(wizard.dynamic_field_ids.ids),
            set(self.template.dynamic_field_ids.ids),
        )

        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(
            xml_id,
            'dynamic_product_label_print.product_label_layout_form_dynamic',
        )
        self.assertEqual(data.get('active_model'), 'product.template')
        self.assertEqual(data.get('bc_height'), 25)
        self.assertEqual(data.get('bc_width'), 45)
        self.assertEqual(data.get('layout_wizard'), self.template.id)
        self.assertEqual(
            data.get('quantity_by_product'),
            {self.product_tmpl.id: 4},
        )
        self.assertTrue(data.get('dynamic_field_ids'))

    def test_03_wizard_prepare_report_data_product(self):
        """Test wizard report data preparation with product.product."""
        wizard = self.env['product.label.layout'].create({
            'product_ids': [(6, 0, [self.product.id])],
            'print_format': 'dynamic_template',
            'dynamic_template_id': self.template.id,
            'custom_quantity': 2,
        })
        xml_id, data = wizard._prepare_report_data()
        self.assertEqual(data.get('active_model'), 'product.product')
        self.assertEqual(
            data.get('quantity_by_product'),
            {self.product.id: 2},
        )

    def test_04_wizard_process(self):
        """Test wizard process execution and missing template error handling."""
        wizard = self.env['product.label.layout'].create({
            'product_tmpl_ids': [(6, 0, [self.product_tmpl.id])],
            'print_format': 'dynamic_template',
            'dynamic_template_id': self.template.id,
            'custom_quantity': 1,
        })
        action = wizard.process()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertTrue(action.get('close_on_report_download'))

        # Test UserError when xml_id is not found
        self.patch(
            type(wizard),
            '_prepare_report_data',
            lambda self: (False, {}),
        )
        with self.assertRaises(UserError):
            wizard.process()

    def test_05_report_data_generation(self):
        """Test report data formatting and helper function values."""
        raw_data = {
            'active_model': 'product.template',
            'quantity_by_product': {str(self.product_tmpl.id): 3},
            'layout_wizard': self.template.id,
            'bc_width': 45,
            'bc_height': 25,
        }
        res_data = _prepare_datas(self.env, raw_data)
        self.assertIn('quantity', res_data)
        self.assertIn(self.product_tmpl, res_data['quantity'])

        items = res_data['quantity'][self.product_tmpl]
        self.assertTrue(len(items) > 0)
        item = items[0]
        self.assertEqual(item['barcode'], '1234567890128')
        self.assertEqual(item['qty'], 3)
        self.assertEqual(item['product_name'], self.product_tmpl.name)
        self.assertEqual(item['price'], '49.99')

        # Test field helper for category, price, name, type
        cat_val = _get_product_field_val(self.product_tmpl, 'categ_id', self.env)
        self.assertEqual(cat_val, self.category.name)

        price_val = _get_product_field_val(
            self.product_tmpl, 'list_price', self.env
        )
        self.assertEqual(price_val, '49.99')

        name_val = _get_product_field_val(self.product_tmpl, 'name', self.env)
        self.assertEqual(name_val, self.product_tmpl.name)

        # Test abstract report model _get_report_values
        report_model = self.env[
            'report.dynamic_product_label_print.report_dynamic'
        ]
        report_values = report_model._get_report_values(
            docids=None, data=raw_data
        )
        self.assertIn('quantity', report_values)
