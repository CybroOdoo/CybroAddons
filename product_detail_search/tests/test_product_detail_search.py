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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductDetailSearch(TransactionCase):
    """Test suite for product_detail_search module covering barcode search,
    product detail extraction, selection labels, and stock view actions.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Category
        cls.category = cls.env['product.category'].create({
            'name': 'Test POS Category',
        })

        # Taxes
        cls.tax_vat = cls.env['account.tax'].create({
            'name': 'Test VAT 10%',
            'amount': 10.0,
            'amount_type': 'percent',
            'company_id': cls.company.id,
        })
        cls.tax_service = cls.env['account.tax'].create({
            'name': 'Test Service Tax 5%',
            'amount': 5.0,
            'amount_type': 'percent',
            'company_id': cls.company.id,
        })

        # Product 1: Consumable product with barcode, single tax, company, specifications
        cls.product_with_tax = cls.env['product.product'].create({
            'name': 'Ergonomic Desk Chair',
            'barcode': 'BARCODE_TEST_CHAIR_001',
            'default_code': 'CHAIR-001',
            'list_price': 199.99,
            'type': 'consu',
            'categ_id': cls.category.id,
            'taxes_id': [(6, 0, [cls.tax_vat.id])],
            'company_id': cls.company.id,
        })

        # Product 2: Product without tax, no company, with variant spec in name
        cls.product_no_tax = cls.env['product.product'].create({
            'name': 'Modular Sofa (Grey, Velvet)',
            'barcode': 'BARCODE_TEST_SOFA_002',
            'default_code': 'SOFA-002',
            'list_price': 450.00,
            'type': 'consu',
            'categ_id': cls.category.id,
            'taxes_id': [(6, 0, [])],
            'company_id': False,
        })

        # Product 3: Service product with multiple taxes
        cls.product_multi_tax = cls.env['product.product'].create({
            'name': 'Installation Service',
            'barcode': 'BARCODE_TEST_SRV_003',
            'default_code': 'SRV-003',
            'list_price': 80.00,
            'type': 'service',
            'categ_id': cls.category.id,
            'taxes_id': [(6, 0, [cls.tax_vat.id, cls.tax_service.id])],
            'company_id': cls.company.id,
        })

    def test_product_detail_search_with_single_tax(self):
        """Test searching a product with a single tax assigned."""
        result = self.env['product.template'].product_detail_search(
            self.product_with_tax.barcode
        )
        self.assertTrue(result, "Search should return details for valid barcode.")
        self.assertEqual(len(result), 1)

        details = result[0]
        self.assertEqual(details['id'], self.product_with_tax.id)
        self.assertEqual(details['name'], self.product_with_tax.name)
        self.assertEqual(details['display_name'], self.product_with_tax.display_name)
        self.assertEqual(details['barcode'], self.product_with_tax.barcode)
        self.assertEqual(details['default_code'], self.product_with_tax.default_code)
        self.assertEqual(details['list_price'], self.product_with_tax.list_price)
        self.assertEqual(details['category'], self.category.name)
        self.assertEqual(details['company_id'], [self.company.id, self.company.name])
        self.assertEqual(details['taxes_id'], [self.tax_vat.id])
        self.assertEqual(details['tax_amount'], 'Test VAT 10%')
        self.assertEqual(details['specification'], [])

        expected_type_label = self.env['product.template'].get_selection_label(
            'product.product', 'type', 'consu'
        )
        self.assertEqual(details['type'], expected_type_label)
        self.assertEqual(details['symbol'], str(self.product_with_tax.currency_id.symbol))

    def test_product_detail_search_without_tax_and_with_specifications(self):
        """Test searching a product without tax and parsing variant specifications."""
        result = self.env['product.template'].product_detail_search(
            self.product_no_tax.barcode
        )
        self.assertTrue(result)
        details = result[0]

        self.assertEqual(details['id'], self.product_no_tax.id)
        self.assertEqual(details['tax_amount'], 'No tax')
        self.assertFalse(details['company_id'])
        self.assertIn('Grey', details['specification'])
        self.assertIn('Velvet', details['specification'])

    def test_product_detail_search_with_multiple_taxes(self):
        """Test searching a product that has multiple taxes assigned."""
        result = self.env['product.template'].product_detail_search(
            self.product_multi_tax.barcode
        )
        self.assertTrue(result)
        details = result[0]

        self.assertEqual(details['id'], self.product_multi_tax.id)
        self.assertIn('Test VAT 10%', details['tax_amount'])
        self.assertIn('Test Service Tax 5%', details['tax_amount'])

        expected_type_label = self.env['product.template'].get_selection_label(
            'product.product', 'type', 'service'
        )
        self.assertEqual(details['type'], expected_type_label)

    def test_product_detail_search_non_existent_barcode(self):
        """Test searching with an unknown barcode returns False."""
        result = self.env['product.template'].product_detail_search(
            'UNKNOWN_NON_EXISTENT_BARCODE_XYZ'
        )
        self.assertFalse(result, "Search should return False for unknown barcode.")
        self.assertFalse(self.env['product.template'].product_detail_search(''))
        self.assertFalse(self.env['product.template'].product_detail_search(False))

    def test_get_selection_label(self):
        """Test retrieving the translated selection label for fields."""
        tmpl = self.env['product.template']

        label_consu = tmpl.get_selection_label('product.product', 'type', 'consu')
        self.assertTrue(label_consu, "Selection label for consu should not be empty.")

        label_service = tmpl.get_selection_label('product.product', 'type', 'service')
        self.assertTrue(label_service, "Selection label for service should not be empty.")
        self.assertNotEqual(label_consu, label_service)

    def test_product_detail_search_without_type(self):
        """Test product_detail_search when get_selection_label returns False."""
        from unittest.mock import patch

        with patch.object(
            type(self.env['product.template']),
            'get_selection_label',
            return_value=False
        ):
            result = self.env['product.template'].product_detail_search(
                self.product_with_tax.barcode
            )
            self.assertTrue(result)
            self.assertFalse(result[0]['type'], "Type should be False when label returns False.")

    def test_stock_client_action_and_menu(self):
        """Test that the stock barcode find client action and menu exist."""
        action = self.env.ref(
            'product_detail_search.product_detail_search_barcode_action_main_menu'
        )
        self.assertTrue(action.exists(), "Client action should exist.")
        self.assertEqual(action.tag, 'product_detail_search_barcode_main_menu')

        menu = self.env.ref(
            'product_detail_search.product_detail_search_barcode_menu'
        )
        self.assertTrue(menu.exists(), "Find product menu should exist.")
        self.assertEqual(menu.action.id, action.id)
        self.assertEqual(menu.parent_id, self.env.ref('stock.menu_stock_root'))
