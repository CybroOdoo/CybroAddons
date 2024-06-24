# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo.http import request, route
from odoo import http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website.models.ir_http import sitemap_qs2dom


class CustomerBlacklist(WebsiteSale):
    """this class is inherited to to check whether the customer is
    blacklisted"""

    @http.route(['/shop/<model("product.template"):product>'], type='http',
                auth="public", website=True, sitemap=True)
    def product(self, product, category='', search='', **kwargs):
        """Updated the context to check whether the customer is blacklisted
        and cleared the cache"""
        res = super(CustomerBlacklist, self).product(product=product,
                                                     category=category,
                                                     search=search, **kwargs)
        is_blacklisted = request.env.user.partner_id.blacklisted_partner
        res.qcontext['is_blacklisted'] = is_blacklisted
        request.env.registry.clear_caches()
        return res

    def sitemap_shop(env, rule, qs):
        """Generate sitemap entries for the Odoo eCommerce shop categories"""
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}
        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """Updated the context to check whether the customer is blacklisted
                and cleared the cache"""
        res = super(CustomerBlacklist, self).shop(page=page, category=category,
                                                  search=search,
                                                  min_price=min_price,
                                                  max_price=max_price, ppg=ppg,
                                                  **post)
        is_blacklisted = request.env.user.partner_id.blacklisted_partner
        res.qcontext['is_blacklisted'] = is_blacklisted
        request.env.registry.clear_caches()
        return res
