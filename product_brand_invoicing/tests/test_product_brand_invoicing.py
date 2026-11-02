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
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo import Command


@tagged('post_install', '-at_install')
class TestProductBrandInvoicing(AccountTestInvoicingCommon):
    """Test suite for product_brand_invoicing module covering models,
    relationships, compute methods, invoice analysis reports, and permissions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand_model = cls.env['product.brand']
        cls.product_model = cls.env['product.product']

        cls.brand_a = cls.brand_model.create({
            'name': 'Alpha Brand',
        })
        cls.brand_b = cls.brand_model.create({
            'name': 'Beta Brand',
        })

    def test_product_brand_creation_and_defaults(self):
        """Test brand creation, fields, and default count."""
        brand = self.brand_model.create({
            'name': 'Gamma Brand',
            'brand_image': 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7',
        })
        self.assertEqual(brand.name, 'Gamma Brand')
        self.assertEqual(brand.product_count, 0)
        self.assertTrue(brand.brand_image)

        # Brand name is required
        with self.assertRaises(Exception):
            self.brand_model.create({'name': False})

    def test_product_brand_compute_count(self):
        """Test product count computation and inverse relationship."""
        product_1 = self.product_model.create({
            'name': 'Brand Product 1',
            'brand_id': self.brand_a.id,
        })
        product_2 = self.product_model.create({
            'name': 'Brand Product 2',
            'brand_id': self.brand_a.id,
        })

        # Test count after adding products
        self.assertEqual(self.brand_a.product_count, 2)
        self.assertIn(product_1.product_tmpl_id, self.brand_a.member_ids)
        self.assertIn(product_2.product_tmpl_id, self.brand_a.member_ids)

        # Reassign product to brand_b
        product_2.product_tmpl_id.brand_id = self.brand_b.id
        self.assertEqual(self.brand_a.product_count, 1)
        self.assertEqual(self.brand_b.product_count, 1)

        # Associate via member_ids directly
        product_3 = self.product_model.create({
            'name': 'Brand Product 3',
        })
        self.brand_b.member_ids = [Command.link(product_3.product_tmpl_id.id)]
        self.assertEqual(self.brand_b.product_count, 2)
        self.assertEqual(product_3.product_tmpl_id.brand_id, self.brand_b)

        # Remove product from brand
        product_1.product_tmpl_id.brand_id = False
        self.assertEqual(self.brand_a.product_count, 0)

    def test_account_invoice_report_with_brand(self):
        """Test that account.invoice.report correctly includes and groups brand_id."""
        self.product_a.product_tmpl_id.brand_id = self.brand_a.id

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2026-10-31',
            'invoice_line_ids': [
                Command.create({
                    'product_id': self.product_a.id,
                    'quantity': 2,
                    'price_unit': 100.0,
                }),
            ],
        })
        invoice.action_post()

        # Query invoice report
        report = self.env['account.invoice.report'].search([
            ('move_id', '=', invoice.id),
        ])
        self.assertTrue(report, "Invoice report record should exist for the posted invoice")
        self.assertEqual(report.brand_id, self.brand_a, "Invoice report should reflect the product's brand")

        # Test searching with brand_id domain
        reports_with_brand = self.env['account.invoice.report'].search([
            ('brand_id', '=', self.brand_a.id),
        ])
        self.assertIn(report, reports_with_brand)

    def test_account_invoice_report_without_brand(self):
        """Test that account.invoice.report handles products without a brand."""
        product_no_brand = self.product_model.create({
            'name': 'Generic Product',
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_date': '2026-10-31',
            'invoice_line_ids': [
                Command.create({
                    'product_id': product_no_brand.id,
                    'quantity': 1,
                    'price_unit': 50.0,
                }),
            ],
        })
        invoice.action_post()

        report = self.env['account.invoice.report'].search([
            ('move_id', '=', invoice.id),
        ])
        self.assertTrue(report)
        self.assertFalse(report.brand_id)

    def test_brand_access_rights(self):
        """Test that internal user (base.group_user) has access to product.brand."""
        demo_user = self.env['res.users'].create({
            'name': 'Brand Test User',
            'login': 'brand_test_user',
            'email': 'brand_test_user@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })

        brand_as_user = self.brand_model.with_user(demo_user).create({
            'name': 'User Created Brand',
        })
        self.assertEqual(brand_as_user.name, 'User Created Brand')
        read_data = brand_as_user.read(['name', 'product_count'])
        self.assertTrue(read_data)
        self.assertEqual(read_data[0]['name'], 'User Created Brand')
