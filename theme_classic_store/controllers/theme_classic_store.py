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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import datetime
from odoo import fields, http
from odoo.http import request


class WebsiteClassicCategory(http.Controller):
    """This controller method returns a JSON object that categorizes products based
     on their product categories.
    :return: a JSON object containing the main product categories and their
    respective product counts
    :rtype: dict"""

    @http.route('/classic_product_category', auth="public", type='jsonrpc', website=True)
    def get_product_categories(self):
        """Categorize products based on product categories
        The counter "category_counter" is used to keep track of the product
        count in each category"""

        products = request.env['product.template'].sudo().search([
            ('is_published', '=', True)
        ])
        main_categories = request.env['product.public.category'].sudo().search([
            ('parent_id', '=', False)
        ])
        child_categories = request.env['product.public.category'].sudo().search([
            ('parent_id', '!=', False)
        ])
        result = []
        for main_category in main_categories:
            category_data = {
                'main_category': main_category.name,
                'main_category_id': main_category.id,
                'children': {}
            }
            children = child_categories.filtered(
                lambda c: c.parent_id.id == main_category.id
            )
            for child in children:
                product_count = len(
                    products.filtered(lambda p: child.id in p.public_categ_ids.ids)
                )
                category_data['children'][child.name] = product_count
            result.append(category_data)
        return result

    @http.route('/classic_product_trending', auth="public", type='jsonrpc', website=True)
    def get_trending_products(self):
        """Return the trending products: the ones chosen in the Classic Store
        configuration, otherwise the most visited products of the last 7 days.
        The route is public, so it only reads data and never writes."""
        env = request.env
        classic_config = env['classic.store.config'].sudo().search([], limit=1)
        trending_products = classic_config.trending_product_ids.read(
            ['name', 'id', 'list_price'])

        if not trending_products:
            date_before = fields.Datetime.now() - datetime.timedelta(days=7)
            groups = env['website.track'].sudo()._read_group(
                [('visit_datetime', '>=', date_before),
                 ('product_id', '!=', False)],
                groupby=['product_id'],
                aggregates=['__count'],
                order='__count desc',
                limit=36,
            )
            template_ids = []
            for product, _count in groups:
                if product.product_tmpl_id.id not in template_ids:
                    template_ids.append(product.product_tmpl_id.id)
            if template_ids:
                templates = env['product.template'].sudo().search_read(
                    [('is_published', '=', True),
                     ('id', 'in', template_ids)],
                    fields=['name', 'id', 'list_price'],
                )
                # keep the visit ranking
                templates.sort(key=lambda t: template_ids.index(t['id']))
                trending_products = templates[:12]

        # Final fallback: any published products if we still have too few
        if len(trending_products) < 3:
            more_products = env['product.template'].sudo().search_read(
                [('is_published', '=', True),
                 ('id', 'not in', [p['id'] for p in trending_products])],
                fields=['name', 'id', 'list_price'],
                limit=12 - len(trending_products),
            )
            trending_products.extend(more_products)

        return {'trending_products': trending_products}
