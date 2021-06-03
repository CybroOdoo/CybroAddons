# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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

from odoo import http
from odoo.http import request


class WebsiteClassicCategory(http.Controller):

    @http.route('/classic_product_category', auth="public", type='json',
                website=True)
    def get_product_categories(self):
        product_ids = request.env['product.template'].sudo().search(
            [('website_published', '=', True)])

        product_category_ids = request.env[
            'product.public.category'].sudo().search([])

        product_categories_main_list = []
        for rec in product_category_ids:
            if rec.child_id:
                product_categories_main_list.append(rec)

        category_counter = {}
        for rec in product_category_ids:
            category_counter[rec] = 0

        for rec in product_ids:
            for cat in rec.public_categ_ids:
                if cat in product_category_ids:
                    category_counter[cat] += 1

        values = {
            'product_categories_main': product_categories_main_list,
            'counter': category_counter
        }

        response = http.Response(
            template='theme_classic_store.s_classic_store_categories',
            qcontext=values)
        return response.render()
