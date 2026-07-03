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

class TestSeoPublicCategory(TransactionCase):
    """Test cases for the SeoPublicCategory model
    (inherits product.public.category)."""

    def setUp(self):
        super().setUp()
        self.Category = self.env['product.public.category']

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _create_category(self, name='Test Category', **kwargs):
        vals = {'name': name}
        vals.update(kwargs)
        return self.Category.create(vals)

    # ------------------------------------------------------------------
    # Field existence on the inherited model
    # ------------------------------------------------------------------

    def test_is_auto_seo_field_exists(self):
        """is_auto_seo field should be present on product.public.category."""
        cat = self._create_category()
        self.assertIn('is_auto_seo', cat._fields)

    def test_category_description_field_exists(self):
        """category_description field should be present on
        product.public.category."""
        cat = self._create_category()
        self.assertIn('category_description', cat._fields)

    # ------------------------------------------------------------------
    # Default values
    # ------------------------------------------------------------------

    def test_is_auto_seo_default_false(self):
        """is_auto_seo should default to False."""
        cat = self._create_category()
        self.assertFalse(cat.is_auto_seo)

    def test_category_description_default_empty(self):
        """category_description should default to False/empty."""
        cat = self._create_category()
        self.assertFalse(cat.category_description)

    # ------------------------------------------------------------------
    # is_auto_seo toggling
    # ------------------------------------------------------------------

    def test_enable_is_auto_seo(self):
        """Setting is_auto_seo=True on a category should persist correctly."""
        cat = self._create_category(is_auto_seo=True)
        self.assertTrue(cat.is_auto_seo)

    def test_disable_is_auto_seo(self):
        """Setting is_auto_seo=False on a category that had it True should
        persist correctly."""
        cat = self._create_category(is_auto_seo=True)
        cat.write({'is_auto_seo': False})
        self.assertFalse(cat.is_auto_seo)

    # ------------------------------------------------------------------
    # category_description
    # ------------------------------------------------------------------

    def test_set_category_description(self):
        """category_description should store a text value correctly."""
        desc = 'Best SEO category for outdoor gear.'
        cat = self._create_category(category_description=desc)
        self.assertEqual(cat.category_description, desc)

    def test_update_category_description(self):
        """Updating category_description should reflect the new value."""
        cat = self._create_category(category_description='Old description')
        cat.write({'category_description': 'New description'})
        self.assertEqual(cat.category_description, 'New description')

    def test_clear_category_description(self):
        """Clearing category_description should set it to False."""
        cat = self._create_category(category_description='Some text')
        cat.write({'category_description': False})
        self.assertFalse(cat.category_description)

    def test_category_description_long_text(self):
        """category_description should accept long text values (Text field)."""
        long_desc = 'A' * 5000
        cat = self._create_category(category_description=long_desc)
        self.assertEqual(len(cat.category_description), 5000)

    # ------------------------------------------------------------------
    # Inherited fields are unaffected
    # ------------------------------------------------------------------

    def test_name_still_required(self):
        """The inherited 'name' field should still be required."""
        with self.assertRaises(Exception):
            self.Category.create({'is_auto_seo': True})

    def test_parent_id_still_works(self):
        """Parent-child relationship from the base model should still work."""
        parent = self._create_category(name='Parent Cat')
        child = self._create_category(name='Child Cat', parent_id=parent.id)
        self.assertEqual(child.parent_id, parent)

    # ------------------------------------------------------------------
    # Search / filtering by is_auto_seo
    # ------------------------------------------------------------------

    def test_search_auto_seo_true(self):
        """Searching for is_auto_seo=True should return only enabled
        categories."""
        self._create_category(name='Auto SEO On', is_auto_seo=True)
        self._create_category(name='Auto SEO Off', is_auto_seo=False)
        enabled = self.Category.search([('is_auto_seo', '=', True)])
        self.assertTrue(
            all(c.is_auto_seo for c in enabled),
            "All results of is_auto_seo=True filter should have is_auto_seo set."
        )
        names = enabled.mapped('name')
        self.assertIn('Auto SEO On', names)
        self.assertNotIn('Auto SEO Off', names)

    def test_search_auto_seo_false(self):
        """Searching for is_auto_seo=False should return only disabled
        categories."""
        self._create_category(name='Enabled Cat', is_auto_seo=True)
        self._create_category(name='Disabled Cat', is_auto_seo=False)
        disabled = self.Category.search([('is_auto_seo', '=', False)])
        self.assertTrue(
            all(not c.is_auto_seo for c in disabled),
            "All results of is_auto_seo=False filter should not have is_auto_seo set."
        )

    # ------------------------------------------------------------------
    # Interaction: category_description + is_auto_seo together
    # ------------------------------------------------------------------

    def test_auto_seo_and_description_set_together(self):
        """A category can have both is_auto_seo=True and a
        category_description at the same time."""
        cat = self._create_category(
            name='Full SEO Cat',
            is_auto_seo=True,
            category_description='Rich SEO description here.',
        )
        self.assertTrue(cat.is_auto_seo)
        self.assertEqual(cat.category_description, 'Rich SEO description here.')

    def test_multiple_categories_independent_flags(self):
        """Multiple categories should maintain their own independent
        is_auto_seo flags."""
        cat1 = self._create_category(name='Cat A', is_auto_seo=True)
        cat2 = self._create_category(name='Cat B', is_auto_seo=False)
        cat3 = self._create_category(name='Cat C', is_auto_seo=True)

        self.assertTrue(cat1.is_auto_seo)
        self.assertFalse(cat2.is_auto_seo)
        self.assertTrue(cat3.is_auto_seo)

    # ------------------------------------------------------------------
    # Unlink
    # ------------------------------------------------------------------

    def test_delete_category(self):
        """Deleting a category should remove it from the database."""
        cat = self._create_category(name='Deletable Cat')
        cat_id = cat.id
        cat.unlink()
        self.assertFalse(self.Category.browse(cat_id).exists())
