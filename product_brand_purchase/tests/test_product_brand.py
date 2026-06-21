# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductBrand(TransactionCase):
    """Test cases for Product Brand"""

    def setUp(self):
        super(TestProductBrand, self).setUp()
        self.brand = self.env['product.brand'].create({'name': 'Test Brand'})
        self.product1 = self.env['product.template'].create({
            'name': 'Test Product 1',
            'brand_id': self.brand.id,
        })
        self.product2 = self.env['product.template'].create({
            'name': 'Test Product 2',
            'brand_id': self.brand.id,
        })

    def test_compute_product_count(self):
        """Test the compute function for product count."""
        self.assertEqual(self.brand.product_count, '2')
        
        self.env['product.template'].create({
            'name': 'Test Product 3',
            'brand_id': self.brand.id,
        })
        self.assertEqual(self.brand.product_count, '3')
