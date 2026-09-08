# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase


class TestWmWasteCategory(TransactionCase):
    """Unit tests verifying waste category validation rules and uniqueness constraints."""

    def setUp(self):
        """ Set up test case preconditions and test data. """
        super().setUp()
        self.category = self.env['wm.waste.category'].create({
            'name': 'Test Category For Products',
            'code': 'TCFP01',
        })

    def test_product_ids_relation(self):
        """
        Test that products assigned to a waste category appear in
        category.product_ids.
        """
        product_1 = self.env['product.template'].create({
            'name': 'Test Waste Product 1',
            'is_waste_material': True,
            'wm_waste_category_id': self.category.id,
        })
        product_2 = self.env['product.template'].create({
            'name': 'Test Waste Product 2',
            'is_waste_material': True,
            'wm_waste_category_id': self.category.id,
        })

        self.assertIn(product_1, self.category.product_ids)
        self.assertIn(product_2, self.category.product_ids)
        self.assertEqual(len(self.category.product_ids), 2)
