# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import logging
import requests
from odoo.addons.website_sale.controllers.wishlist import ProductWishlist
from odoo.http import request, route

_logger = logging.getLogger(__name__)


class SaleWishlist(ProductWishlist):
    """Extends the functionality of website sale wishlist by adding
       additional analytics tracking when a product is added to the wishlist.
       """

    @route('/shop/wishlist/add', type='jsonrpc', auth='public', website=True)
    def add_to_wishlist(self, product_id, **kw):
        """Function for adding a product to the wishlist.
            :param product_id: ID of the product to be added to the wishlist.
            :param kw: Additional keyword arguments.
            :return: Result of adding the product to the wishlist."""
        res = super().add_to_wishlist(product_id, **kw)
        try:
            product = request.env['product.product'].browse(product_id)
            product.check_access('read')
            if not product.exists():
                return res
            enable_analytics = request.env[
                'ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.enable_analytics'
            )
            measurement_id = request.env[
                'ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.measurement_id_analytics'
            )
            api_secret = request.env['ir.config_parameter'].sudo().get_str(
                'google_analytics_odoo.api_secret'
            )
            if enable_analytics and measurement_id and api_secret:
                url = f"https://www.google-analytics.com/mp/collect?measurement_id={measurement_id}&api_secret={api_secret}"
                data = {
                    "client_id": str(request.env.user.id),
                    "events": [{
                        "name": "Add_To_Wishlist",
                        "params": {
                            "Product_Name": product.name,
                            "Amount": product.list_price,
                            "Customer": request.env.user.name,
                        }
                    }]
                }
                requests.post(url, json=data, timeout=5)
        except Exception as e:
            _logger.warning("Google Analytics Add_To_Wishlist error: %s", e)
        return res
