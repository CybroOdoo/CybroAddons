# -*- coding: utf-8 -*-
"""
Test suite for theme_diva module (v16.0.1.0.0)

Python modules covered:
  - models/product_template.py  →  Rating (inherits product.template)
      _compute_rating_count()   →  rating_count (Float, avg rating)
      _compute_rating_total()   →  rating_total (Integer, total ratings)

  - models/product_featured.py  →  FeaturedProducts (product.featured.relation)
                                    WebsiteProductFeatured (product.featured)
      _default_featured_list()  →  default for featured_list_ids (up to 8 products)
      Fields: name, website_published, featured_list_ids, user_id

Run with:
    odoo-bin -d <db> --test-enable --stop-after-init -i theme_diva
"""
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_product(env, name='Test Product', **kwargs):
    vals = {'name': name, 'type': 'consu', **kwargs}
    return env['product.template'].create(vals)


def _make_featured(env, **kwargs):
    defaults = {'name': 'Test Featured'}
    defaults.update(kwargs)
    return env['product.featured'].create(defaults)


# ===========================================================================
# 1. product.template — computed rating fields
# ===========================================================================

@tagged('post_install', '-at_install')
class TestRatingComputedFields(TransactionCase):
    """Tests for Rating._compute_rating_count and _compute_rating_total."""

    def setUp(self):
        super().setUp()
        self.product = _make_product(self.env)

    # -----------------------------------------------------------------------
    # 1a. rating_count  (_compute_rating_count → rating_get_stats()['avg'])
    # -----------------------------------------------------------------------

    def test_rating_count_field_exists(self):
        """rating_count field exists on product.template."""
        self.assertIn('rating_count', self.env['product.template']._fields)

    def test_rating_count_is_float(self):
        """rating_count is a Float field."""
        field = self.env['product.template']._fields['rating_count']
        from odoo.fields import Float
        self.assertIsInstance(field, Float)

    def test_rating_count_is_computed(self):
        """rating_count has a compute method set."""
        field = self.env['product.template']._fields['rating_count']
        self.assertTrue(field.compute,
            "rating_count must be a computed field.")

    def test_rating_count_returns_numeric(self):
        """rating_count evaluates to a number (no crash on access)."""
        val = self.product.rating_count
        self.assertIsInstance(val, (int, float),
            "rating_count should return a numeric value.")

    def test_rating_count_default_zero_or_none_when_no_ratings(self):
        """
        A brand-new product with no ratings should have rating_count = 0.0
        (rating_get_stats returns avg=0 when total=0).
        """
        self.assertAlmostEqual(self.product.rating_count, 0.0, places=2,
            msg="rating_count should be 0.0 for a product with no ratings.")

    def test_rating_count_maps_avg_key_from_stats(self):
        """
        _compute_rating_count reads the 'avg' key from rating_get_stats().
        Patch the helper to return a known avg and verify the field value.
        """
        from unittest.mock import patch
        fake_stats = {'avg': 4.5, 'total': 10, 'count': 10}
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value=fake_stats
        ):
            # Trigger recompute
            self.product._compute_rating_count()
            self.assertAlmostEqual(self.product.rating_count, 4.5, places=2,
                msg="rating_count should reflect the 'avg' from rating_get_stats.")

    def test_rating_count_handles_missing_avg_key(self):
        """
        If rating_get_stats() returns a dict without 'avg', rating_count
        must be None / 0 — not raise a KeyError.
        """
        from unittest.mock import patch
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'total': 0}   # no 'avg' key
        ):
            try:
                self.product._compute_rating_count()
            except KeyError:
                self.fail(
                    "_compute_rating_count raised KeyError when 'avg' is "
                    "absent from rating_get_stats().")

    def test_rating_count_computed_for_multiple_products(self):
        """_compute_rating_count iterates over recordset without error."""
        p2 = _make_product(self.env, name='Product B')
        batch = self.product | p2
        try:
            batch._compute_rating_count()
        except Exception as exc:
            self.fail(
                f"_compute_rating_count raised {exc!r} on a multi-record set.")

    # -----------------------------------------------------------------------
    # 1b. rating_total  (_compute_rating_total → rating_get_stats()['total'])
    # -----------------------------------------------------------------------

    def test_rating_total_field_exists(self):
        """rating_total field exists on product.template."""
        self.assertIn('rating_total', self.env['product.template']._fields)

    def test_rating_total_is_integer(self):
        """rating_total is an Integer field."""
        field = self.env['product.template']._fields['rating_total']
        from odoo.fields import Integer
        self.assertIsInstance(field, Integer)

    def test_rating_total_is_computed(self):
        """rating_total has a compute method set."""
        field = self.env['product.template']._fields['rating_total']
        self.assertTrue(field.compute,
            "rating_total must be a computed field.")

    def test_rating_total_returns_integer(self):
        """rating_total evaluates to an integer (no crash on access)."""
        val = self.product.rating_total
        self.assertIsInstance(val, int,
            "rating_total should return an integer value.")

    def test_rating_total_default_zero_when_no_ratings(self):
        """A new product with no ratings should have rating_total = 0."""
        self.assertEqual(self.product.rating_total, 0,
            "rating_total should be 0 for a product with no ratings.")

    def test_rating_total_maps_total_key_from_stats(self):
        """
        _compute_rating_total reads the 'total' key from rating_get_stats().
        Patch the helper to return a known total and verify the field value.
        """
        from unittest.mock import patch
        fake_stats = {'avg': 4.5, 'total': 17, 'count': 17}
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value=fake_stats
        ):
            self.product._compute_rating_total()
            self.assertEqual(self.product.rating_total, 17,
                "rating_total should reflect the 'total' from rating_get_stats.")

    def test_rating_total_handles_missing_total_key(self):
        """
        If rating_get_stats() returns a dict without 'total', rating_total
        must be None / 0 — not raise a KeyError.
        """
        from unittest.mock import patch
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 0.0}   # no 'total' key
        ):
            try:
                self.product._compute_rating_total()
            except KeyError:
                self.fail(
                    "_compute_rating_total raised KeyError when 'total' is "
                    "absent from rating_get_stats().")

    def test_rating_total_computed_for_multiple_products(self):
        """_compute_rating_total iterates over recordset without error."""
        p2 = _make_product(self.env, name='Product C')
        batch = self.product | p2
        try:
            batch._compute_rating_total()
        except Exception as exc:
            self.fail(
                f"_compute_rating_total raised {exc!r} on a multi-record set.")

    def test_rating_count_and_total_independent(self):
        """rating_count (avg) and rating_total (count) are independent fields."""
        from unittest.mock import patch
        fake_stats = {'avg': 3.2, 'total': 5}
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value=fake_stats
        ):
            self.product._compute_rating_count()
            self.product._compute_rating_total()

        self.assertAlmostEqual(self.product.rating_count, 3.2, places=2)
        self.assertEqual(self.product.rating_total, 5)


# ===========================================================================
# 2. product.featured.relation — join model
# ===========================================================================


# ===========================================================================
# 3. product.featured — main featured-product model
# ===========================================================================

