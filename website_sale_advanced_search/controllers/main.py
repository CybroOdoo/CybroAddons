# -*- coding: utf-8 -*-

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
            product_as_category = request.env['product.template'].search(
                domain)
            sql = """select id as res_id, name as name, name as value from product_template where name ILIKE '{}'"""
            extra_query = ''
            if product_as_category:
                extra_query = " and id in {}"
            limit = " limit 15"
            qry = sql + extra_query + limit
            product_list = []
            if len(product_as_category.ids) == 1:
                product_list = product_as_category.ids
                product_list.append(0)
            request.cr.execute(qry.format(strings, tuple(
                product_as_category and product_list if len(
                    product_as_category.ids) == 1 else product_as_category.ids)))
            name = request.cr.dictfetchall()
        except:
            name = {'name': 'None', 'value': 'None'}
        return json.dumps(name)
