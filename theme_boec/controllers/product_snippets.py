# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import http
from odoo.http import request


class WebsiteProduct(http.Controller):
    @http.route('/get_product_tab', auth="public", type='json', website=True)
    def get_product_tab(self):
        """Get the website published products for snippet"""
        new_arrivals = request.env['product.template'].sudo().search(
            [('website_published', '=', True)],
            order='create_date desc', limit=12)
        hot_deals = request.env['product.template'].sudo().search(
            [('website_published', '=', True),
             ('hot_deals', '=', True)], limit=12)
        values = {
            'new_arrivals': new_arrivals,
            'hot_deals': hot_deals
        }
        response = http.Response(template='theme_boec.product_tab',
                                 qcontext=values)
        return response.render()


class DealWeek(http.Controller):
    @http.route('/get_product', auth='public', type='json', website=True)
    def get_products(self, **kwargs):
        """Allows to get deal of the week product."""
        boec_configuration = request.env.ref('theme_boec.boec_config_data')
        product_id = boec_configuration.deal_week_product_id
        values = {'product_id': product_id}
        response = http.Response(template='theme_boec.deal_week',
                                 qcontext=values)
        return response.render()

    @http.route('/get_countdown', auth='public', type='json', website=True)
    def get_countdown(self, **kwargs):
        """End date for the deal"""
        boec_configuration = request.env.ref('theme_boec.boec_config_data')
        end_date = boec_configuration.date_end
        return end_date

