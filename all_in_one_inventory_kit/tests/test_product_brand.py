# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests.common import TransactionCase


class TestProductBrand(TransactionCase):
    def setUp(self):
        super(TestProductBrand, self).setUp()
        self.brand = self.env['product.brand'].create({
            'name': 'Test Brand',
        })
    
    def test_product_brand_creation(self):
        """Test if product brand is created successfully"""
        self.assertEqual(self.brand.name, 'Test Brand')
        
    def test_product_brand_count(self):
        """Test count of products in a brand"""
        product = self.env['product.template'].create({
            'name': 'Test Product',
            'brand_id': self.brand.id,
        })
        self.brand.get_count_products()
        self.assertEqual(self.brand.product_count, "1")
