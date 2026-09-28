# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('at_install', 'post_install')
class TestProductTemplateSearch(TransactionCase):

    def setUp(self):
        super(TestProductTemplateSearch, self).setUp()
        self.category = self.env['product.category'].create({
            'name': 'Test Category'
        })
        self.tax = self.env['account.tax'].create({
            'name': 'Test Tax 15%',
            'amount': 15.0,
            'type_tax_use': 'sale',
        })
        self.product = self.env['product.product'].create({
            'name': 'Test Product (Red, Large)',
            'barcode': '1234567890',
            'default_code': 'TEST-001',
            'type': 'consu',
            'list_price': 100.0,
            'categ_id': self.category.id,
            'taxes_id': [(6, 0, [self.tax.id])],
        })

    def test_get_selection_label(self):
        """Test getting the correct label for a selection field."""
        label = self.env['product.template'].get_selection_label('product.product', 'type', 'consu')
        self.assertEqual(label, 'Goods')

    def test_product_detail_search_found(self):
        """Test scanning a valid barcode returns product details."""
        details = self.env['product.template'].product_detail_search('1234567890')
        self.assertTrue(details, "Product details should be returned.")
        self.assertIsInstance(details, list)
        self.assertEqual(len(details), 1)

        product_data = details[0]
        self.assertEqual(product_data['id'], self.product.id)
        self.assertEqual(product_data['name'], 'Test Product (Red, Large)')
        self.assertEqual(product_data['type'], 'Goods')
        self.assertEqual(product_data['barcode'], '1234567890')
        self.assertEqual(product_data['default_code'], 'TEST-001')
        self.assertEqual(product_data['qty_available'], 0.0)
        self.assertEqual(product_data['list_price'], 100.0)
        self.assertEqual(product_data['category'], 'Test Category')
        self.assertEqual(product_data['tax_amount'], 'Test Tax 15%')
        self.assertEqual(product_data['symbol'], '$') # Assuming default currency is USD
        self.assertIn('Red', product_data['specification'][0])
        self.assertIn('Large', product_data['specification'][1])

    def test_product_detail_search_no_tax(self):
        """Test scanning a product without tax."""
        product_no_tax = self.env['product.product'].create({
            'name': 'Test Product No Tax (Blue)',
            'barcode': '0987654321',
            'type': 'consu',
            'taxes_id': [(5, 0, 0)],
        })
        details = self.env['product.template'].product_detail_search('0987654321')
        self.assertTrue(details)
        self.assertEqual(details[0]['tax_amount'], 'No tax')

    def test_product_detail_search_not_found(self):
        """Test scanning an invalid barcode returns False."""
        details = self.env['product.template'].product_detail_search('INVALID123')
        self.assertFalse(details, "Invalid barcode should return False")
