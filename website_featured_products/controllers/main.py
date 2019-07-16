# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import http
from odoo.http import request
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
        Overrided function to update the response with featured products objects.Here we are updating qcontext.
        :param page:
        :param category:
        :param search:
        :param ppg:
        :param post:
        :return:
        """
        response = super(WebsiteSaleExtend, self).shop(page=0, category=None, search='', ppg=False, **post)
        env = request.env
        published_list_ids = env['product.featured'].sudo().search([('website_published', '=', True)]).ids
        featured_products = env['product.featured.relation'].sudo().search([('featured_rel', 'in', published_list_ids)])
        response.qcontext.update({
            'featured_products': featured_products,
        })
        return response
