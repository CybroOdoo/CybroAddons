# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleWishlist(WebsiteSale):
    """This function helps to override the functionalities of a wishlist"""

    @http.route()
    def add_to_wishlist(self, product_id, **kw):
        """Function to check product is exits in wishlist list or not"""
        if kw.get('is_template'):
            product_id = request.env['product.template'].sudo().browse(
                product_id)._get_first_possible_variant_id()
        wish = request.env['product.wishlist'].sudo().search([
            ('product_id', '=', product_id)
        ])
        return False if wish else super().add_to_wishlist(product_id, **kw)
