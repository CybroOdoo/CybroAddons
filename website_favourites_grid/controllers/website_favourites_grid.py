# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import json
from odoo.http import request, route
from odoo.addons.website_sale_wishlist.controllers.main import \
    WebsiteSaleWishlist


class WebsiteSaleWishlist(WebsiteSaleWishlist):
    """Which will be used to call the website wishlist controller"""
    @route(['/shop/wishlist'], type='http', auth="public", website=True,
           sitemap=False)
    def get_wishlist(self, count=False, view_type='grid', **kw):
        """Returns product_wishlist template with initially the view_type
         as grid"""
        values = request.env['product.wishlist'].with_context(
            display_default_code=False).current()
        if count:
            return request.make_response(
                json.dumps(values.mapped('product_id').ids))
        if not len(values):
            return request.redirect("/shop")
        return request.render("website_sale_wishlist.product_wishlist",
                              dict(wishes=values, view_type=view_type))
