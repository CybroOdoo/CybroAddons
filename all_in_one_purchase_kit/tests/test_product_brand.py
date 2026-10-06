# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.

###############################################################################
from odoo.tests.common import TransactionCase

class TestProductBrand(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.brand = cls.env['product.brand'].create({
            'name': 'Test Brand',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Test Product for Brand',
            'brand_id': cls.brand.id,
        })

    def test_compute_count_products(self):
        """Test the computation of product count associated with a brand."""
        self.brand._compute_count_products()
        self.assertEqual(int(self.brand.product_count), 1, "Product count should be 1")

        # Add another product
        self.env['product.template'].create({
            'name': 'Second Test Product for Brand',
            'brand_id': self.brand.id,
        })
        self.brand._compute_count_products()
        self.assertEqual(int(self.brand.product_count), 2, "Product count should be 2 after adding another product")
