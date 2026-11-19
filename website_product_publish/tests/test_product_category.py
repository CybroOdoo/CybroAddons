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
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProductCategory(common.TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Category = cls.env['product.category']
        Template = cls.env['product.template']
        cls.category = Category.create({'name': 'Veg'})
        cls.child_category = Category.create({
            'name': 'Leafy',
            'parent_id': cls.category.id,
        })
        cls.other_category = Category.create({'name': 'Fruit'})

        cls.product = Template.create({
            'name': 'VegProduct',
            'categ_id': cls.category.id,
            'is_published': False,
        })
        cls.child_product = Template.create({
            'name': 'LeafyProduct',
            'categ_id': cls.child_category.id,
            'is_published': False,
        })
        cls.not_for_sale = Template.create({
            'name': 'VegNotForSale',
            'categ_id': cls.category.id,
            'sale_ok': False,
            'is_published': False,
        })
        cls.other_product = Template.create({
            'name': 'FruitProduct',
            'categ_id': cls.other_category.id,
            'is_published': False,
        })

    def _refresh_counts(self, category):
        """Computed fields have no @api.depends, so drop the cache."""
        category.invalidate_recordset(
            ['published_count', 'unpublished_count'])

    # ------------------------------------------------------------------
    # Publish / unpublish all
    # ------------------------------------------------------------------
    def test_action_publish_all_products(self):
        """Publish all sellable products of a category."""
        self.category.action_publish_all_products()
        self.assertTrue(
            self.product.is_published,
            "Product should be published after action_publish_all_products")

    def test_action_publish_all_includes_child_categories(self):
        """Products of child categories are published too (child_of)."""
        self.category.action_publish_all_products()
        self.assertTrue(self.child_product.is_published)

    def test_action_publish_all_skips_not_sale_ok(self):
        """Products with sale_ok=False are not published."""
        self.category.action_publish_all_products()
        self.assertFalse(self.not_for_sale.is_published)

    def test_action_publish_all_ignores_other_categories(self):
        """Products of unrelated categories stay untouched."""
        self.category.action_publish_all_products()
        self.assertFalse(self.other_product.is_published)

    def test_action_publish_all_on_child_does_not_touch_parent(self):
        """Publishing a child category must not publish parent products."""
        self.child_category.action_publish_all_products()
        self.assertTrue(self.child_product.is_published)
        self.assertFalse(self.product.is_published)

    def test_action_unpublish_all_products(self):
        """Unpublish all sellable products of a category."""
        (self.product | self.child_product).write({'is_published': True})
        self.category.action_unpublish_all_products()
        self.assertFalse(
            self.product.is_published,
            "Product should be unpublished after "
            "action_unpublish_all_products")
        self.assertFalse(self.child_product.is_published)

    def test_action_unpublish_all_ignores_other_categories(self):
        """Products of unrelated categories stay published."""
        self.product.write({'is_published': True})
        self.other_product.write({'is_published': True})
        self.category.action_unpublish_all_products()
        self.assertFalse(self.product.is_published)
        self.assertTrue(self.other_product.is_published)

    def test_actions_on_empty_category(self):
        """Actions on a category without products must not fail."""
        empty = self.env['product.category'].create({'name': 'Empty'})
        empty.action_publish_all_products()
        empty.action_unpublish_all_products()
        self.assertEqual(empty.published_count, 0)
        self.assertEqual(empty.unpublished_count, 0)

    # ------------------------------------------------------------------
    # Counts
    # ------------------------------------------------------------------
    def test_published_unpublished_count(self):
        """Verify published and unpublished product counts."""
        self.product.write({'is_published': True})
        self._refresh_counts(self.category)
        # child_product is unpublished; not_for_sale is excluded
        self.assertEqual(self.category.published_count, 1)
        self.assertEqual(self.category.unpublished_count, 1)

        self.product.write({'is_published': False})
        self._refresh_counts(self.category)
        self.assertEqual(self.category.published_count, 0)
        self.assertEqual(self.category.unpublished_count, 2)

    def test_count_includes_child_categories(self):
        """Parent counts include products of child categories."""
        self.child_product.write({'is_published': True})
        self._refresh_counts(self.category)
        self.assertEqual(self.category.published_count, 1)
        self._refresh_counts(self.child_category)
        self.assertEqual(self.child_category.published_count, 1)
        self.assertEqual(self.child_category.unpublished_count, 0)

    def test_count_excludes_not_sale_ok(self):
        """Products with sale_ok=False are not counted."""
        self.not_for_sale.write({'is_published': True})
        self._refresh_counts(self.category)
        self.assertEqual(self.category.published_count, 0)

    # ------------------------------------------------------------------
    # Smart button actions
    # ------------------------------------------------------------------
    def test_action_view_published_products(self):
        """Published action lists only published sellable products."""
        self.product.write({'is_published': True})
        action = self.category.action_view_published_products()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.template')
        found = self.env['product.template'].search(action['domain'])
        self.assertEqual(found, self.product)

    def test_action_view_unpublished_products(self):
        """Unpublished action lists only unpublished sellable products."""
        self.product.write({'is_published': True})
        action = self.category.action_view_unpublished_products()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'product.template')
        found = self.env['product.template'].search(action['domain'])
        self.assertEqual(found, self.child_product)
