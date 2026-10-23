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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from psycopg2 import IntegrityError

from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes, mute_logger


@tagged('post_install', '-at_install')
class TestProductBrand(TransactionCase):
    """Test cases for product.brand model in product_brand_sale module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductBrand = cls.env['product.brand']
        cls.ProductTemplate = cls.env['product.template']

        cls.brand = cls.ProductBrand.create({
            'name': 'Test Brand A',
            'brand_image': BinaryBytes(b'fake_image_bytes'),
        })

    def test_01_create_product_brand(self):
        """Test brand creation and initial state."""
        self.assertTrue(self.brand.id, "Product brand should be created successfully.")
        self.assertEqual(self.brand.name, 'Test Brand A')
        self.assertTrue(self.brand.brand_image, "Brand image should be saved.")
        self.assertEqual(self.brand.product_count, 0, "Initial product count should be 0.")
        self.assertFalse(self.brand.member_ids, "Initial member_ids should be empty.")

        # Test updating with base64 string
        self.brand.brand_image = 'R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'
        self.assertTrue(self.brand.brand_image)

        # Test clearing image
        self.brand.brand_image = False
        self.assertFalse(self.brand.brand_image)

    def test_02_product_count_computation(self):
        """Test product_count compute method when products are added and removed."""
        product_1 = self.ProductTemplate.create({
            'name': 'Product 1',
            'brand_id': self.brand.id,
        })
        self.assertEqual(self.brand.product_count, 1, "Product count should be 1 after adding one product.")

        product_2 = self.ProductTemplate.create({
            'name': 'Product 2',
            'brand_id': self.brand.id,
        })
        self.assertEqual(self.brand.product_count, 2, "Product count should be 2 after adding second product.")

        # Reassign one product to another brand
        other_brand = self.ProductBrand.create({'name': 'Test Brand B'})
        product_2.brand_id = other_brand.id

        self.assertEqual(self.brand.product_count, 1, "Product count should decrease to 1.")
        self.assertEqual(other_brand.product_count, 1, "New brand product count should be 1.")

        # Remove brand from product_1
        product_1.brand_id = False
        self.assertEqual(self.brand.product_count, 0, "Product count should be 0 after removing brand.")

    def test_03_member_ids_relation(self):
        """Test member_ids relation when linking products directly."""
        product_1 = self.ProductTemplate.create({'name': 'Template 1'})
        product_2 = self.ProductTemplate.create({'name': 'Template 2'})

        self.brand.write({
            'member_ids': [Command.link(product_1.id), Command.link(product_2.id)],
        })

        self.assertEqual(len(self.brand.member_ids), 2, "Brand should have 2 member products.")
        self.assertIn(product_1, self.brand.member_ids)
        self.assertIn(product_2, self.brand.member_ids)
        self.assertEqual(product_1.brand_id, self.brand)
        self.assertEqual(product_2.brand_id, self.brand)
        self.assertEqual(self.brand.product_count, 2)

    def test_04_brand_name_required(self):
        """Test that brand name is required."""
        with mute_logger('odoo.sql_db'), self.assertRaises(IntegrityError):
            self.ProductBrand.create({'name': None})
