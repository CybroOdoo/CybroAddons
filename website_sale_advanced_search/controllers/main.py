# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
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
#############################################################################

import json
from odoo import http
from odoo.http import request


class WebsiteSearch(http.Controller):

    @http.route('/shop/search', csrf=False, type="http",
                methods=['POST', 'GET'], auth="public", website=True)
    def search_contents(self, **kw):
        """
        Searches products according to the category selected on front,
        :param kw: dict contains the category and search key
        :return: Dict with params as name, res_id, value
        """
        strings = '%' + kw.get('name') + '%'
        category = int(kw.get('category')) if not kw.get(
            'category') == 'all' else ''
        try:
            domain = [('public_categ_ids', 'child_of',
                       [category])] if category else []
            domain.append(('website_published', '=', True))
            product_as_category = request.env['product.template'].search(domain)
            sql = """select id as res_id, name as name, name as value from product_template where name ILIKE %s"""
            extra_query = ''
            if product_as_category:
                extra_query = " and id in %s"
            limit = " limit 15"
            request.cr.execute(sql + extra_query + limit, \
                               (tuple([strings]), tuple(
                                   product_as_category and product_as_category.ids)))
            name = request.cr.dictfetchall()
        except:
            name = {'name': 'None', 'value': 'None'}
        return json.dumps(name)
