# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.addons.product_barcode.models.product_product import ean_checksum, check_ean, generate_ean

class TestProductProduct(TransactionCase):

    def setUp(self):
        super(TestProductProduct, self).setUp()

    def test_ean_functions(self):
        # test check_ean with valid, invalid, empty
        self.assertTrue(check_ean(False))
        self.assertFalse(check_ean('123'))
        self.assertFalse(check_ean('abc1234567890'))
        
        # test generate_ean
        ean = generate_ean('1')
        self.assertEqual(len(ean), 13)
        self.assertEqual(ean, '0000000000104')
        
        ean_empty = generate_ean(False)
        self.assertEqual(ean_empty, '0000000000000')
        
    def test_product_create_barcode(self):
        product = self.env['product.product'].create({
            'name': 'Test EAN13 Product',
            'type': 'product',
        })
        self.assertTrue(product.barcode)
        self.assertTrue(product.barcode.startswith('21'))
        self.assertEqual(len(product.barcode), 13)
