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
from odoo.tests import common
from ..models.product_product import ean_checksum, check_ean, generate_ean


class TestProductProductBarcode(common.TransactionCase):

    def test_barcode_generation_on_product_create(self):
        """Test that a barcode is automatically generated and set correctly when a new product is created."""
        product_1 = self.env['product.product'].create({
            'name': 'Barcode Test Product 1',
        })
        self.assertTrue(product_1.barcode, "Barcode should be generated and set on creation")
        self.assertEqual(len(product_1.barcode), 13, "Generated barcode must be 13 characters long")
        self.assertTrue(product_1.barcode.startswith('21'), "Generated barcode must start with '21'")

        expected_ean = generate_ean(str(product_1.id))
        expected_barcode = '21' + expected_ean[2:]
        self.assertEqual(product_1.barcode, expected_barcode, "Generated barcode does not match expected barcode format")

        product_2 = self.env['product.product'].create({
            'name': 'Barcode Test Product 2',
        })
        self.assertNotEqual(product_1.barcode, product_2.barcode, "Each product should get a unique barcode")
        self.assertTrue(product_2.barcode.startswith('21'), "Second generated barcode must also start with '21'")

        # Test that pre-existing barcode in vals is preserved
        product_existing = self.env['product.product'].create({
            'name': 'Barcode Test Product Pre-set',
            'barcode': '1234567890128',
        })
        self.assertEqual(product_existing.barcode, '1234567890128', "Existing barcode in vals must not be replaced")

        # Test batch creation (multiple products at once)
        multi_products = self.env['product.product'].create([
            {'name': 'Multi Product 1'},
            {'name': 'Multi Product 2'},
        ])
        self.assertEqual(len(multi_products), 2)
        self.assertTrue(multi_products[0].barcode, "Batch product 1 should have barcode generated")
        self.assertTrue(multi_products[1].barcode, "Batch product 2 should have barcode generated")
        self.assertNotEqual(multi_products[0].barcode, multi_products[1].barcode, "Batch products must have unique barcodes")

    def test_helper_ean_checksum(self):
        """Test the custom ean_checksum helper function."""
        self.assertEqual(ean_checksum("123456789"), -1)
        self.assertEqual(ean_checksum("12345678901234"), -1)

        self.assertEqual(ean_checksum("4006381333930"), 1)

    def test_helper_check_ean(self):
        """Test the custom check_ean helper function."""
        self.assertTrue(check_ean(""))
        self.assertTrue(check_ean(None))

        self.assertFalse(check_ean("12345"))

        self.assertFalse(check_ean("123456789012a"))

        self.assertFalse(check_ean("4006381333930"))
        self.assertTrue(check_ean("4006381333931"))
        self.assertTrue(check_ean(generate_ean("1")))

    def test_helper_generate_ean(self):
        """Test the custom generate_ean helper function."""
        self.assertEqual(generate_ean(""), "0000000000000")
        self.assertEqual(generate_ean(None), "0000000000000")

        self.assertEqual(generate_ean("1"), "0000000000109")