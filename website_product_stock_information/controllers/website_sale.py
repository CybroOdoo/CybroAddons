# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    """to pass stock details to shop page"""

    @http.route()
    def shop(self, **post):
        """To include stock values during rendering of the shop page."""
        result = super().shop(**post)
        if request.website.is_view_active('website_product_stock_information.product_stock_information'):
            result.qcontext['stocks'] = {product.id: self.get_stock_info(product) for
                                         product in result.qcontext['products']}
        return request.render("website_sale.products", result.qcontext)

    def get_stock_info(self, product):
        """function to get stock details"""
        if not product.is_storable:
            return False

        combination_info = product.sudo().with_context(website_sale_stock_get_quantity=True)._get_combination_info()
        free_qty = combination_info.get('free_qty', 0)
        return 'in_stock' if free_qty > 0 else 'out_of_stock'
