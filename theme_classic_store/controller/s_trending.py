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

from odoo import http, fields
from odoo.http import request
import datetime


class WebsiteClassicTrending(http.Controller):

    @http.route('/classic_product_trending', auth="public", type='json',
                website=True)
    def get_trending_products(self):

        classic_config = request.env[
            'classic_store.config'].sudo().search([])
        trending_products = classic_config.trending_product_ids

        if not trending_products:
            products = request.env['product.template'].sudo().search([])
            for each in products:
                each.views = 0
                each.most_viewed = False
            date = fields.Datetime.now()
            date_before = date - datetime.timedelta(days=7)
            products = request.env['website.track'].sudo().search(
                [('visit_datetime', '<=', date),
                 ('visit_datetime', '>=', date_before),
                 ('product_id', '!=', False)])
            for pro in products:
                pro.product_id.views = pro.product_id.views + 1

            trending_products = request.env['product.template'].sudo().search(
                [('is_published', '=', True),
                 ('views', '!=', 0)],
                order='views desc', limit=4)

        values = {
            'trending_products': trending_products
        }

        response = http.Response(
            template='theme_classic_store.s_classic_store_trending',
            qcontext=values)
        return response.render()
