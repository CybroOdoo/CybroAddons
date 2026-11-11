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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestProductRestrictionUsers(TransactionCase):
    """Test suite verifying product and category restrictions on users."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_user = cls.env.ref('base.group_user')
        cls.group_erp_manager = cls.env.ref('base.group_erp_manager')

        cls.restricted_user = cls.env['res.users'].create({
            'name': 'Test Restricted User',
            'login': 'restricted_user@example.com',
            'email': 'restricted_user@example.com',
            'group_ids': [(6, 0, [cls.group_user.id])],
        })

        cls.admin_user = cls.env['res.users'].create({
            'name': 'Test Admin User',
            'login': 'admin_user@example.com',
            'email': 'admin_user@example.com',
            'group_ids': [(6, 0, [cls.group_user.id, cls.group_erp_manager.id])],
        })

        cls.parent_category = cls.env['product.category'].create({
            'name': 'Electronics',
        })
        cls.child_category = cls.env['product.category'].create({
            'name': 'Smartphones',
            'parent_id': cls.parent_category.id,
        })
        cls.other_category = cls.env['product.category'].create({
            'name': 'Furniture',
        })

        cls.product_laptop = cls.env['product.template'].create({
            'name': 'Laptop',
            'categ_id': cls.parent_category.id,
        })
        cls.product_phone = cls.env['product.template'].create({
            'name': 'Phone',
            'categ_id': cls.child_category.id,
        })
        cls.product_chair = cls.env['product.template'].create({
            'name': 'Office Chair',
            'categ_id': cls.other_category.id,
        })

    def test_compute_is_admin(self):
        """Verify _compute_is_admin logic for standard users and managers."""
        self.assertFalse(self.restricted_user.is_admin)
        self.assertTrue(self.admin_user.is_admin)

    def test_product_restriction_by_product(self):
        """Verify user is restricted to allowed products when type is 'product'."""
        self.restricted_user.write({
            'restricted_type': 'product',
            'allowed_product_ids': [(6, 0, [self.product_laptop.id])],
        })
        products = self.env['product.template'].with_user(self.restricted_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertEqual(products, self.product_laptop)

    def test_product_restriction_by_category(self):
        """Verify user is restricted to allowed categories including child categories."""
        self.restricted_user.write({
            'restricted_type': 'category',
            'allowed_product_category_ids': [(6, 0, [self.parent_category.id])],
        })
        products = self.env['product.template'].with_user(self.restricted_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertIn(self.product_laptop, products)
        self.assertIn(self.product_phone, products)
        self.assertNotIn(self.product_chair, products)

    def test_empty_restriction_fallback(self):
        """Verify that when no allowed products/categories are set, all products are accessible."""
        self.restricted_user.write({
            'restricted_type': 'product',
            'allowed_product_ids': [(5, 0, 0)],
        })
        products = self.env['product.template'].with_user(self.restricted_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertEqual(len(products), 3)

        self.restricted_user.write({
            'restricted_type': 'category',
            'allowed_product_category_ids': [(5, 0, 0)],
        })
        products_cat = self.env['product.template'].with_user(self.restricted_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertEqual(len(products_cat), 3)

    def test_admin_user_bypass(self):
        """Verify ERP managers bypass all product restrictions."""
        self.admin_user.write({
            'restricted_type': 'product',
            'allowed_product_ids': [(6, 0, [self.product_laptop.id])],
        })
        products = self.env['product.template'].with_user(self.admin_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertEqual(len(products), 3)

    def test_unrestricted_user_access(self):
        """Verify user with no restricted_type configured can access all products."""
        self.restricted_user.write({
            'restricted_type': False,
        })
        products = self.env['product.template'].with_user(self.restricted_user).search([
            ('id', 'in', [self.product_laptop.id, self.product_phone.id, self.product_chair.id]),
        ])
        self.assertEqual(len(products), 3)

    def test_product_template_write_cache_clear(self):
        """Verify write on product.template with restrict_user_ids executes properly."""
        self.product_laptop.write({
            'restrict_user_ids': [(6, 0, [self.restricted_user.id])],
        })
        self.assertIn(self.restricted_user, self.product_laptop.restrict_user_ids)
        self.assertIn(self.product_laptop, self.restricted_user.allowed_product_ids)
