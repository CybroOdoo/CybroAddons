# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged

from .common import ClassicStoreHttpCase


@tagged('post_install', '-at_install')
class TestClassicStoreSnippetRoutes(ClassicStoreHttpCase):

    def test_category_route(self):
        parent = self.env['product.public.category'].create(
            {'name': 'ClassicStoreTest Parent'})
        child = self.env['product.public.category'].create(
            {'name': 'ClassicStoreTest Child', 'parent_id': parent.id})
        self.product.public_categ_ids = [(4, child.id)]

        result = self.make_jsonrpc_request('/classic_product_category')
        entry = next(
            (r for r in result if r['main_category_id'] == parent.id), None)
        self.assertTrue(entry, "Parent category should be returned")
        self.assertEqual(entry['children'].get('ClassicStoreTest Child'), 1)

    def test_trending_route_manual_products(self):
        config = self.env['classic.store.config'].search([], limit=1)
        config.trending_product_ids = [(6, 0, self.product.ids)]

        result = self.make_jsonrpc_request('/classic_product_trending')
        ids = [p['id'] for p in result['trending_products']]
        self.assertIn(self.product.id, ids)

    def test_trending_route_fallback(self):
        """Without configured products, published products are returned."""
        config = self.env['classic.store.config'].search([], limit=1)
        config.trending_product_ids = [(5, 0, 0)]

        result = self.make_jsonrpc_request('/classic_product_trending')
        self.assertIn('trending_products', result)
        self.assertTrue(result['trending_products'])

    def test_trending_route_counts_recent_visits(self):
        """Fallback ranks products by website.track visits of the last 7 days (read-only)."""
        import uuid
        config = self.env['classic.store.config'].search([], limit=1)
        config.trending_product_ids = [(5, 0, 0)]
        visitor = self.env['website.visitor'].create({
            'access_token': uuid.uuid4().hex,
            'website_id': self.website.id,
        })
        self.env['website.track'].create({
            'visitor_id': visitor.id,
            'product_id': self.product.product_variant_id.id,
        })

        result = self.make_jsonrpc_request('/classic_product_trending')
        ids = [p['id'] for p in result['trending_products']]
        self.assertIn(self.product.id, ids)
