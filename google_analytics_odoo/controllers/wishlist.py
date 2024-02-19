# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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
import requests
from odoo.addons.website_sale_wishlist.controllers.main import \
    WebsiteSaleWishlist
from odoo.http import request


class SaleWishlist(WebsiteSaleWishlist):
    """Extends the functionality of website sale wishlist by adding
       additional analytics tracking when a product is added to the wishlist.
       """
    def add_to_wishlist(self, product_id, **kw):
        """Function
         for adding a product to the wishlist.
            :param product_id: ID of the product to be added to the wishlist.
            :param kw: Additional keyword arguments.
            :return: Result of adding the product to the wishlist."""
        res = super().add_to_wishlist(product_id, **kw)
        product = request.env['product.product'].sudo().browse(product_id)
        enable_analytics = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.enable_analytics'),
        measurement_id = request.env[
            'ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.measurement_id_analytics')
        api_secret = request.env['ir.config_parameter'].sudo().get_param(
            'google_analytics_odoo.api_secret')
        if enable_analytics:
            url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
            data = {
                "client_id": str(request.env.user.id),
                "events": [{
                    "name": "Add_To_Wishlist",
                    "params": {
                        "Product_Name": product.name,
                        "Amount": product.list_price,
                        'Customer': request.env.user.name
                    }
                }]
            }
            requests.post(url, json=data)
        return res
