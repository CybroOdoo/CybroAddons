# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solution (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import http
from odoo.tools import lazy
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class ProductVisibilityWebsite(WebsiteSale):
    """updating the domain for filtering out the products and category based on the configurations"""

    @http.route(type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super(ProductVisibilityWebsite, self).shop(page, category, search, min_price, max_price, ppg,
                                                              **post)
        Category = request.env['product.public.category']
        user = request.env.user
        website = request.env['website'].get_current_website()
        website_domain = website.website_domain()
        search_product = response.qcontext['products']
        available_products, available_categ, parent_categs = website.get_available_product_categories(user)
        mode = website.get_user_mode(user, available_products, available_categ)
        available_categ_final = Category
        if available_products and mode == 'product_only':
            product_category = available_products.mapped('public_categ_ids') | parent_categs
            category = set(response.qcontext['categories'].ids).intersection(set(product_category.ids))
            available_categ_final = Category.browse(category)
        elif available_categ and mode == 'categ_only':
            available_categ |= parent_categs
            category = set(response.qcontext['categories'].ids).intersection(set(available_categ.ids))
            available_categ_final = Category.browse(category)
        categs_domain = [('parent_id', '=', False)] + website_domain
        if available_categ_final or mode in ['product_only', 'categ_only']:
            categs_domain += [('id', 'in', available_categ_final.ids)]
            search_categories = Category.search(categs_domain)
        elif search:
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain
            ).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
        else:
            search_categories = available_categ_final
        categs = lazy(lambda: Category.search(categs_domain))
        response.qcontext['categories'] = categs
        response.qcontext['search_categories_ids'] = search_categories
        return response
