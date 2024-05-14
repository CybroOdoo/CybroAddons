"""Top-selling products controller"""
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request


class TopSellingProducts(http.Controller):
    """This class is for the getting top most sold products
        products_categories:
                          Function for passing top most sold products to js,
                          and it returns products, unique categories and the
                           current website
    """

    @http.route('/top_products/categories', type='json', auth='public')
    def products_categories(self):
        """Function for getting the current website, top most sold products and
           its categories.
            Return
                  products-most sold products
                  unique_categories-categories of all products
                  current_website-the current website for checking products or
                  categories are available on that website
        """
        current_website = request.env['website'].sudo().get_current_website().id
        public_categ_id = request.env[
            'product.public.category'].sudo().search_read(
            [('parent_id', '=', False)], ['name',
                                          'website_id'])
        products = []
        public_categories = []
        for category in public_categ_id:
            products_search_read = request.env['product.template'].with_user(
                request.env.ref('base.user_admin')).search_read(
                [('is_published', '=', True),
                 ('public_categ_ids.id', '=', category['id'])],
                ['name', 'image_1920', 'public_categ_ids', 'website_id',
                 'sales_count'])
            for product in products_search_read:
                if product['sales_count'] != 0:
                    products.append(product)
                    public_categories.append(category)
        unique_categories = [dict(categories) for categories in
                             {tuple(sorted(record.items())) for record in
                              public_categories}]
        return products, unique_categories, current_website
