# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestProductCategory(TransactionCase):
    """Test suite for the Product Category Management module."""

    @classmethod
    def setUpClass(cls):
        """Setup initial data for testing product category management features."""
        super(TestProductCategory, cls).setUpClass()
        cls.category_parent = cls.env['product.category'].create({
            'name': 'Parent Category',
            'description': 'Parent category description'
        })
        cls.category_child = cls.env['product.category'].create({
            'name': 'Child Category',
            'parent_id': cls.category_parent.id,
            'description': 'Child category description'
        })
        cls.product = cls.env['product.template'].search([], limit=1)
        if cls.product:
            cls.product.categ_id = cls.category_child.id

    def test_product_count(self):
        """Verify the computation of product count for categories."""
        self.category_child._compute_product_count()
        self.assertEqual(self.category_child.product_count, 1, "The product count for the child category should be 1.")
        self.category_parent._compute_product_count()
        self.assertEqual(self.category_parent.product_count, 0, "The product count for the parent category should be 0 (direct link).")

    def test_archive_constraint(self):
        """Ensure categories with linked products cannot be archived."""
        with self.assertRaises(ValidationError, msg="Should not be able to archive a category linked to a product."):
            self.category_child.active = False
            self.category_child._check_archive()
        with self.assertRaises(ValidationError, msg="Should not be able to archive a parent category if its children have products."):
            self.category_parent.active = False
            self.category_parent._check_archive()

    def test_hierarchy_html(self):
        """Verify the generation of the hierarchy HTML view."""
        self.category_parent._compute_category_hierarchy_html()
        self.assertTrue(self.category_parent.category_hierarchy_html, "Category hierarchy HTML should not be empty.")
        self.assertIn('Parent Category', self.category_parent.category_hierarchy_html)
        self.assertIn('Child Category', self.category_parent.category_hierarchy_html)
        self.assertIn('category-tree', self.category_parent.category_hierarchy_html)
