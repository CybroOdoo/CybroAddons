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
import io

from odoo.tests.common import TransactionCase, tagged


class DummyResponse:
    """Helper response container with stream attribute."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestStockProductReport(TransactionCase):
    """Test stock.product.report wizard methods and queries."""

    @classmethod
    def setUpClass(cls):
        """Set up test data for stock product report wizard."""
        super().setUpClass()
        cls.company = cls.env.company
        cls.category = cls.env['product.category'].create({
            'name': 'Stock Product Test Category',
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Stock Report Test Product',
            'categ_id': cls.category.id,
            'is_storable': True,
        })
        cls.stock_location = cls.env['stock.location'].search([
            ('usage', '=', 'internal'),
            ('company_id', 'in', [cls.company.id, False]),
        ], limit=1)
        if not cls.stock_location:
            cls.stock_location = cls.env['stock.location'].create({
                'name': 'Test Internal Location',
                'usage': 'internal',
                'company_id': cls.company.id,
            })
        cls.customer_location = cls.env['stock.location'].search([
            ('usage', '=', 'customer'),
        ], limit=1)
        if not cls.customer_location:
            cls.customer_location = cls.env['stock.location'].create({
                'name': 'Test Customer Location',
                'usage': 'customer',
            })
        cls.supplier_location = cls.env['stock.location'].search([
            ('usage', '=', 'supplier'),
        ], limit=1)
        if not cls.supplier_location:
            cls.supplier_location = cls.env['stock.location'].create({
                'name': 'Test Supplier Location',
                'usage': 'supplier',
            })

        # Set 25 units on-hand
        cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.stock_location.id,
            'quantity': 25.0,
        })

        # Set 10 units incoming
        cls.env['stock.move'].create({
            'description_picking': 'Test Incoming Move',
            'product_id': cls.product.id,
            'product_uom_qty': 10.0,
            'location_id': cls.supplier_location.id,
            'location_dest_id': cls.stock_location.id,
            'company_id': cls.company.id,
            'state': 'confirmed',
        })

        # Set 5 units outgoing
        cls.env['stock.move'].create({
            'description_picking': 'Test Outgoing Move',
            'product_id': cls.product.id,
            'product_uom_qty': 5.0,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.customer_location.id,
            'company_id': cls.company.id,
            'state': 'confirmed',
        })

    def test_get_report_data(self):
        """Test report data preparation helper."""
        wiz = self.env['stock.product.report'].create({
            'product_category_id': self.category.id,
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        data = wiz._get_report_data()
        self.assertEqual(data.get('product_name'), 'Stock Report Test Product')
        self.assertEqual(data.get('company_name'), self.company.name)
        self.assertTrue('stock_product' in data)

    def test_get_stock_products(self):
        """Test SQL data extraction for stock products with content verification."""
        # Filter with category
        wiz = self.env['stock.product.report'].create({
            'product_category_id': self.category.id,
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        res = wiz._get_stock_products()
        self.assertTrue(len(res) >= 1)
        found = next((r for r in res if r.get('product_id') == self.product.id), None)
        self.assertIsNotNone(found)
        # Verify content rather than just result types
        self.assertEqual(found['product_name'], 'Stock Report Test Product')
        self.assertEqual(found['category_name'], 'Stock Product Test Category')
        self.assertEqual(found['category_id'], self.category.id)
        self.assertEqual(found['qty_available'], 25.0)
        self.assertEqual(found['incoming_qty'], 10.0)
        self.assertEqual(found['outgoing_qty'], 5.0)
        self.assertEqual(found['free_qty'], 25.0)

        # Filter without category
        wiz_no_cat = self.env['stock.product.report'].create({
            'product_id': self.product.id,
            'company_id': self.company.id,
        })
        res_no_cat = wiz_no_cat._get_stock_products()
        self.assertTrue(len(res_no_cat) >= 1)
        found_no_cat = next((r for r in res_no_cat if r.get('product_id') == self.product.id), None)
        self.assertIsNotNone(found_no_cat)
        self.assertEqual(found_no_cat['product_name'], 'Stock Report Test Product')
        self.assertEqual(found_no_cat['category_name'], 'Stock Product Test Category')
        self.assertEqual(found_no_cat['qty_available'], 25.0)
        self.assertEqual(found_no_cat['incoming_qty'], 10.0)
        self.assertEqual(found_no_cat['outgoing_qty'], 5.0)

    def test_company_filter_and_view(self):
        """Test company_id scoping and ensure company_id is present and visible in the view."""
        # Check view architecture ensures company_id is exposed and not hidden
        view = self.env.ref('warehouse_reports.stock_product_report_view_form')
        self.assertIn('name="company_id"', view.arch)
        self.assertNotIn('name="company_id" invisible="1"', view.arch)

        # Test company scoping
        other_company = self.env['res.company'].search([('id', '!=', self.company.id)], limit=1)
        if other_company:
            other_product = self.env['product.product'].create({
                'name': 'Other Company Scoped Product',
                'categ_id': self.category.id,
                'company_id': other_company.id,
            })
            wiz = self.env['stock.product.report'].create({
                'company_id': self.company.id,
            })
            res = wiz._get_stock_products()
            product_ids = [r['product_id'] for r in res]
            self.assertIn(self.product.id, product_ids)
            self.assertNotIn(other_product.id, product_ids)

    def test_actions_and_xlsx_generation(self):
        """Test PDF, XLS actions and Excel output stream."""
        wiz = self.env['stock.product.report'].create({
            'product_id': self.product.id,
        })

        pdf_act = wiz.action_print_pdf_report()
        self.assertIn(pdf_act.get('type'), ['ir.actions.report', 'ir.actions.act_window'])

        xls_act = wiz.action_print_xls_report()
        self.assertEqual(xls_act.get('report_type'), 'xlsx')

        data = {
            'company_name': self.company.name,
            'stock_product': [
                {
                    'product_name': 'Stock Report Test Product',
                    'category_name': 'Stock Product Test Category',
                    'qty_available': 10.0,
                    'free_qty': 4.0,
                    'incoming_qty': 7.0,
                    'outgoing_qty': 3.0,
                }
            ],
        }
        dummy_resp = DummyResponse()
        wiz.get_xlsx_report(data, dummy_resp)
        data_bytes = dummy_resp.stream.getvalue()
        self.assertTrue(len(data_bytes) > 0)
        self.assertTrue(data_bytes.startswith(b'PK\x03\x04'))
