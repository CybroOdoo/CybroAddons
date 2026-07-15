# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from unittest.mock import patch
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'theme_diva')
class TestProductTemplateRating(TransactionCase):
    """Tests for the rating_count and rating_total computed fields on product.template."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.template'].create({
            'name': 'Rating Test Product',
            'type': 'service',
        })

    # ------------------------------------------------------------------
    # 1. Field presence & metadata
    # ------------------------------------------------------------------

    def test_field_rating_count_is_float(self):
        field = self.env['product.template']._fields['rating_count']
        self.assertEqual(field.type, 'float')

    def test_field_rating_total_is_integer(self):
        field = self.env['product.template']._fields['rating_total']
        self.assertEqual(field.type, 'integer')

    def test_field_rating_count_is_computed(self):
        field = self.env['product.template']._fields['rating_count']
        self.assertTrue(field.compute)

    def test_field_rating_total_is_computed(self):
        field = self.env['product.template']._fields['rating_total']
        self.assertTrue(field.compute)

    def test_field_rating_count_not_stored(self):
        """rating_count must not be stored in the database."""
        field = self.env['product.template']._fields['rating_count']
        self.assertFalse(field.store)

    def test_field_rating_total_not_stored(self):
        """rating_total must not be stored in the database."""
        field = self.env['product.template']._fields['rating_total']
        self.assertFalse(field.store)

    # ------------------------------------------------------------------
    # 2. _compute_rating_count
    # ------------------------------------------------------------------

    def test_rating_count_returns_avg_from_stats(self):
        """rating_count must return the 'avg' value from rating_get_stats()."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 4.5, 'total': 10}
        ):
            self.product.invalidate_recordset(['rating_count'])
            self.assertAlmostEqual(self.product.rating_count, 4.5)

    def test_rating_count_zero_when_no_stats(self):
        """rating_count must be 0 (falsy) when avg is 0."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 0, 'total': 0}
        ):
            self.product.invalidate_recordset(['rating_count'])
            self.assertEqual(self.product.rating_count, 0)

    def test_rating_count_none_when_avg_missing(self):
        """rating_count must be None/falsy when 'avg' key is absent."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={}
        ):
            self.product.invalidate_recordset(['rating_count'])
            self.assertFalse(self.product.rating_count)

    def test_rating_count_float_precision(self):
        """rating_count must preserve float precision from avg."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 3.75, 'total': 4}
        ):
            self.product.invalidate_recordset(['rating_count'])
            self.assertAlmostEqual(self.product.rating_count, 3.75, places=2)

    # ------------------------------------------------------------------
    # 3. _compute_rating_total
    # ------------------------------------------------------------------

    def test_rating_total_returns_total_from_stats(self):
        """rating_total must return the 'total' value from rating_get_stats()."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 4.0, 'total': 25}
        ):
            self.product.invalidate_recordset(['rating_total'])
            self.assertEqual(self.product.rating_total, 25)

    def test_rating_total_zero_when_no_reviews(self):
        """rating_total must be 0 when total is 0."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 0, 'total': 0}
        ):
            self.product.invalidate_recordset(['rating_total'])
            self.assertEqual(self.product.rating_total, 0)

    def test_rating_total_none_when_key_missing(self):
        """rating_total must be None/falsy when 'total' key is absent."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={}
        ):
            self.product.invalidate_recordset(['rating_total'])
            self.assertFalse(self.product.rating_total)

    def test_rating_total_is_integer_value(self):
        """rating_total must be an integer (not float)."""
        with patch.object(
            type(self.product), 'rating_get_stats',
            return_value={'avg': 3.0, 'total': 7}
        ):
            self.product.invalidate_recordset(['rating_total'])
            self.assertIsInstance(self.product.rating_total, int)

    # ------------------------------------------------------------------
    # 4. Multi-record compute
    # ------------------------------------------------------------------

    def test_compute_called_per_record_in_batch(self):
        """Both fields must be computed independently for each product."""
        p1 = self.env['product.template'].create({
            'name': 'Batch Product 1', 'type': 'service'
        })
        p2 = self.env['product.template'].create({
            'name': 'Batch Product 2', 'type': 'service'
        })

        call_count = {'n': 0}
        stats_map = {p1.id: {'avg': 4.0, 'total': 5},
                     p2.id: {'avg': 2.0, 'total': 3}}

        original = type(p1).rating_get_stats

        def patched_stats(self_rec):
            call_count['n'] += 1
            return stats_map.get(self_rec.id, {'avg': 0, 'total': 0})

        with patch.object(type(p1), 'rating_get_stats', patched_stats):
            (p1 | p2).invalidate_recordset(['rating_count', 'rating_total'])
            _ = p1.rating_count
            _ = p2.rating_count

        self.assertGreaterEqual(call_count['n'], 2,
                                "rating_get_stats should be called for each record")