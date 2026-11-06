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
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestProductDiscountLimit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a category with a discount limit
        cls.category = cls.env['product.category'].create({
            'name': 'Test Category',
            'desc_limit': 10.0,
        })

        # Create a category without a discount limit
        cls.category_no_limit = cls.env['product.category'].create({
            'name': 'Test Category No Limit',
            'desc_limit': 0.0,
        })

        # Create a product with a discount limit (inherits from product.template field)
        cls.product_with_limit = cls.env['product.product'].create({
            'name': 'Product with Limit',
            'list_price': 100.0,
            'desc_limit': 15.0,
            'categ_id': cls.category.id,
        })

        # Create a product without a limit (should use category limit)
        cls.product_no_limit = cls.env['product.product'].create({
            'name': 'Product no Limit',
            'list_price': 100.0,
            'categ_id': cls.category.id,
        })

        # Create a product without limit and category without limit
        cls.product_zero_limit = cls.env['product.product'].create({
            'name': 'Product Zero Limit',
            'list_price': 100.0,
            'desc_limit': 0.0,
            'categ_id': cls.category_no_limit.id,
        })

        # Create a user without allow_discount
        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Restricted User',
            'login': 'restricted_user_test',
            'email': 'restricted@example.com',
            'group_ids': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])]
        })

        # Create a user with allow_discount
        cls.manager_user = cls.env['res.users'].create({
            'name': 'Manager User',
            'login': 'manager_user_test',
            'email': 'manager@example.com',
            'allow_discount': True,
            'group_ids': [(6, 0, [cls.env.ref('sales_team.group_sale_salesman').id])]
        })

        # Create a partner for the sale order
        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})

    def test_01_product_limit_restricted_user(self):
        """Test product discount limit for a restricted user."""
        sale_order = self.env['sale.order'].with_user(self.restricted_user).create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].with_user(self.restricted_user).create({
            'order_id': sale_order.id,
            'product_id': self.product_with_limit.id,
        })

        # Applying discount within limit (15%)
        order_line.discount = 10.0
        order_line._onchange_discount()
        self.assertEqual(order_line.discount, 10.0)

        # Applying discount exceeding limit (15%)
        with self.assertRaises(UserError) as cm:
            order_line.discount = 20.0
            order_line._onchange_discount()
        self.assertIn('product', str(cm.exception))

    def test_02_category_limit_restricted_user(self):
        """Test category discount limit for a restricted user when product has no limit."""
        sale_order = self.env['sale.order'].with_user(self.restricted_user).create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].with_user(self.restricted_user).create({
            'order_id': sale_order.id,
            'product_id': self.product_no_limit.id,
        })

        # Applying discount within category limit (10%)
        order_line.discount = 5.0
        order_line._onchange_discount()
        self.assertEqual(order_line.discount, 5.0)

        # Applying discount exceeding category limit (10%)
        with self.assertRaises(UserError) as cm:
            order_line.discount = 12.0
            order_line._onchange_discount()
        self.assertIn('category', str(cm.exception))

    def test_03_manager_user_no_limit(self):
        """Test that a user with 'Allow Discount Over Limit' can bypass limits."""
        sale_order = self.env['sale.order'].with_user(self.manager_user).create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].with_user(self.manager_user).create({
            'order_id': sale_order.id,
            'product_id': self.product_with_limit.id,
        })

        # Manager should be able to apply 50% discount even if limit is 15%
        order_line.discount = 50.0
        order_line._onchange_discount()  # Should not raise UserError
        self.assertEqual(order_line.discount, 50.0)

    def test_04_no_limit_restricted_user(self):
        """Test when neither product nor category has a discount limit."""
        sale_order = self.env['sale.order'].with_user(self.restricted_user).create({
            'partner_id': self.partner.id,
        })
        order_line = self.env['sale.order.line'].with_user(self.restricted_user).create({
            'order_id': sale_order.id,
            'product_id': self.product_zero_limit.id,
        })

        # Restricted user can apply discount when no limit is configured
        order_line.discount = 40.0
        order_line._onchange_discount()
        self.assertEqual(order_line.discount, 40.0)