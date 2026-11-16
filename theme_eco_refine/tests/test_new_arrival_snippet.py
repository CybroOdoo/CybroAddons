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
class TestNewArrivalSnippet(ThemeHttpCommon):
    """Tests for the /new_arrival_products JSON route."""

    def test_contains_published_product(self):
        products, categories, _website, unique_id = self._call_snippet(
            '/new_arrival_products')
        self.assertIn('Eco Test Product', [p['name'] for p in products])
        self.assertIn(self.category.id, [c['id'] for c in categories])
        self.assertTrue(unique_id.startswith('uc-'))

    def test_excludes_unpublished_product(self):
        self.product.is_published = False
        products = self._call_snippet('/new_arrival_products')[0]
        self.assertNotIn('Eco Test Product', [p['name'] for p in products])

    def test_newest_first(self):
        self.env.cr.execute(
            "UPDATE product_template SET create_date = create_date - interval '1 day' "
            "WHERE id = %s", [self.product.id])
        self.product.invalidate_recordset(['create_date'])
        self.env['product.template'].create({
            'name': 'Newer Product',
            'is_published': True,
            'public_categ_ids': [(6, 0, self.category.ids)],
        })
        names = [p['name'] for p in self._call_snippet('/new_arrival_products')[0]]
        self.assertLess(names.index('Newer Product'),
                        names.index('Eco Test Product'))