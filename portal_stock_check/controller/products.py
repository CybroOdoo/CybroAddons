# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        """Set the count as None"""

        if 'p_count' in counters:
            values['p_count'] = None
        return values

    @http.route('/my/products', type='http', auth="user", website=True)
    def portal_products(self, **kw):
        """Adding stock check option in portal"""
        return request.render("portal_stock_check.portal_product_availability")

    @http.route('/product/search', type='json', auth="user", website=True)
    def search_product(self, **kw, ):
        """To get corresponding products"""
        product = kw.get('name')
        if product:
            res = request.env['product.product'].sudo().search_read(
                [('name', 'ilike', product), ('is_published', '=', True)])
            return res
        else:
            return False
