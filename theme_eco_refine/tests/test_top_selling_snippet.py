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
class TestTopSellingSnippet(ThemeHttpCommon):
    """Tests for the /top_selling_products JSON route."""

    def test_skips_products_without_sales(self):
        products, _categories, _website, unique_id = self._call_snippet(
            '/top_selling_products')
        self.assertNotIn('Eco Test Product', [p['name'] for p in products])
        self.assertTrue(unique_id.startswith('pc-'))

    def test_returns_product_with_sales(self):
        partner = self.env['res.partner'].create({'name': 'Buyer'})
        order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.product_variant_id.id,
                'product_uom_qty': 2,
            })],
        })
        order.action_confirm()
        self.env.flush_all()
        products = self._call_snippet('/top_selling_products')[0]
        self.assertIn('Eco Test Product', [p['name'] for p in products])