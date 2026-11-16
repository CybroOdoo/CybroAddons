# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged

from .common import ThemeHttpCommon


@tagged('post_install', '-at_install', 'theme_eco_refine')
class TestTopRatedSnippet(ThemeHttpCommon):
    """Tests for the /top_rated_products JSON route."""

    def test_returns_rated_product(self):
        if 'rating.rating' not in self.env:
            self.skipTest('rating module not installed')
        self.env['rating.rating'].create({
            'res_model_id': self.env['ir.model']._get_id('product.template'),
            'res_id': self.product.id,
            'rating': 5,
        })
        products = self._call_snippet('/top_rated_products')[0]
        self.assertIn('Eco Test Product', [p['name'] for p in products])

    def test_without_ratings_is_empty(self):
        products = self._call_snippet('/top_rated_products')[0]
        self.assertNotIn('Eco Test Product', [p['name'] for p in products])

    def test_product_with_two_ratings_is_listed_once(self):
        if 'rating.rating' not in self.env:
            self.skipTest('rating module not installed')
        model_id = self.env['ir.model']._get_id('product.template')
        for value in (5, 3):
            self.env['rating.rating'].create({
                'res_model_id': model_id,
                'res_id': self.product.id,
                'rating': value,
            })
        products = self._call_snippet('/top_rated_products')[0]
        names = [p['name'] for p in products]
        self.assertEqual(names.count('Eco Test Product'), 1)