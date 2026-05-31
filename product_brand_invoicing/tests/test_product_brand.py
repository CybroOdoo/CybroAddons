# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil Ashok(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo import fields


class TestProductBrand(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create Brand
        cls.brand = cls.env['product.brand'].create({
            'name': 'Test Brand',
        })

        # Create Product Category
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
        })

        # Create Product
        cls.product = cls.env['product.template'].create({
            'name': 'Test Product',
            'categ_id': cls.category.id,
            'brand_id': cls.brand.id,
            'list_price': 100.0,
        })

        # Create Customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Create Invoice
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': cls.product.product_variant_id.id,
                'quantity': 1,
                'price_unit': 100.0,
                'name': 'Test Invoice Line',
            })]
        })

        cls.invoice.action_post()

    def test_product_count(self):
        """Test computed product count for brand"""
        self.assertEqual(
            int(self.brand.product_count),
            1,
            "Product count should be 1"
        )

    def test_brand_linked_to_product(self):
        """Test brand is properly linked with product"""
        self.assertEqual(
            self.product.brand_id,
            self.brand,
            "Brand should be linked to product"
        )

    def test_account_invoice_report_brand(self):
        """Test brand_id appears in account.invoice.report"""

        report = self.env['account.invoice.report'].search([
            ('product_id', '=', self.product.product_variant_id.id)
        ], limit=1)

        self.assertTrue(
            report,
            "Invoice report record should exist"
        )

        self.assertEqual(
            report.brand_id,
            self.brand,
            "Brand should appear in invoice report"
        )

    def test_select_contains_brand_id(self):
        """Test _select method contains brand_id"""

        query = self.env['account.invoice.report']._select()

        self.assertIn(
            'template.brand_id as brand_id',
            query,
            "_select should contain brand_id"
        )
