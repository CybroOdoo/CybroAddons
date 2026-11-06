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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestCommissionProduct(TransactionCase):

    def setUp(self):
        super(TestCommissionProduct, self).setUp()
        self.category = self.env['product.category'].create({'name': 'Test Category'})

        # Create a dedicated product in a separate category so the test is
        # self-contained and not reliant on demo/existing data.
        other_cat = self.env['product.category'].create({'name': 'Other Category'})
        self.product = self.env['product.product'].create({
            'name': 'Test Commission Product',
            'sale_ok': True,
            'categ_id': other_cat.id,
        })

        self.commission = self.env['crm.commission'].create({
            'name': 'Product Plan',
            'date_from': date.today(),
            'date_to': date.today() + timedelta(days=10),
            'type': 'product',
        })
        self.ProductComm = self.env['commission.product']

    def test_compute_category_id(self):
        """Test that category changes remove incompatible products."""
        comm_rule = self.ProductComm.new({
            'commission_id': self.commission.id,
            'category_id': self.category.id,
            'product_id': self.product.id,
        })
        comm_rule._onchange_category_id()
        self.assertFalse(comm_rule.product_id)

        self.product.categ_id = self.category.id
        comm_rule.product_id = self.product.id
        comm_rule._onchange_category_id()
        self.assertEqual(comm_rule.product_id.id, self.product.id)

    def test_product_must_belong_to_selected_category(self):
        """Test that invalid product-category combinations cannot be saved."""
        with self.assertRaises(ValidationError):
            self.ProductComm.create({
                'commission_id': self.commission.id,
                'category_id': self.category.id,
                'product_id': self.product.id,
            })
