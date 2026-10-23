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
"""Unit tests for product.brand model in product_brand_purchase."""
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestProductBrand(TransactionCase):
    """Test cases for 'product.brand' model in product_brand_purchase."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.brand = cls.env['product.brand'].create({
            'name': 'Acme Brand',
        })

    def test_name_required(self):
        """Test name field is mandatory on product.brand."""
        with mute_logger('odoo.sql_db'), self.assertRaises((ValidationError, IntegrityError, Exception)):
            self.env['product.brand'].create({
                'name': False,
            })

    def test__compute_product_count(self):
        """Test _compute_product_count computes product count properly as an integer."""
        # 1. Initially no products assigned
        self.brand._compute_product_count()
        self.assertEqual(self.brand.product_count, 0)

        # 2. Add two product templates under this brand
        tmpl_1 = self.env['product.template'].create({
            'name': 'Brand Product 1',
            'brand_id': self.brand.id,
        })
        tmpl_2 = self.env['product.template'].create({
            'name': 'Brand Product 2',
            'brand_id': self.brand.id,
        })
        self.brand._compute_product_count()
        self.assertEqual(self.brand.product_count, 2)

        # 3. Remove one product template from brand
        tmpl_1.brand_id = False
        self.brand._compute_product_count()
        self.assertEqual(self.brand.product_count, 1)

    test_compute_product_count = test__compute_product_count
