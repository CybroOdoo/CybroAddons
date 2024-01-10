# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (<https://www.cybrosys.com>)
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
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    """This class inherits controller portal"""
    def _prepare_home_portal_values(self, counters):
        """This function super the method and set count as none
        :param int counters: count of the product
        :param auth: The user must be authenticated and the current
        request will perform using the rights that the user was given.
        :param string type: HTTP Request and JSON Request,utilizing HTTP
        requests via the GET and POST methods. HTTP methods such as GET, POST,
        PUT, DELETE
        :return: values in counters
       """
        values = super()._prepare_home_portal_values(counters)
        if 'p_count' in counters:
            values['p_count'] = None
        return values

    @http.route('/my/products', type='http', auth="user", website=True)
    def portal_products(self, **kw):
        """Adding stock check option in portal"""
        return request.render("portal_stock_check.portal_product_availability")

    @http.route('/product/search', type='json', auth="user", website=True)
    def search_product(self, args):
        """To get corresponding products matching domain conditions
        :param args: Name input on search product
        :return: Result of input text given for searching the product
        """
        product = args['product']
        if product:
            domain = [('name', 'ilike', product), ('is_published', '=', True)]
            res = request.env['product.product'].sudo().search_read(
                domain=domain, fields=['id', 'display_name', 'qty_available'])
            return res
        return False
