# -*- coding: utf-8 -*-

from odoo import http
from odoo.addons.website_sale.controllers import main


class WebsiteSaleExtend(main.WebsiteSale):
    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>'
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        """
        Overrided function to update the response with products objects.Here we are updating qcontext.
        :param page:
        :param category:
        :param search:
        :param ppg:
        :param post:
        :return:
        """
        response = super(WebsiteSaleExtend, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
        response.qcontext.update({
            'get_attribute_value_ids': self.get_attribute_value_ids,
            'rating_status': response.qcontext.get('rating_product'),
        })
        return response
