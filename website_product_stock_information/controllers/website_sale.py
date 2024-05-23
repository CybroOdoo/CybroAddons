# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fouzan M (odoo@cybrosys.com)
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
        result.qcontext['stocks'] = {product: self.get_stock_info(product) for
                                     product in result.qcontext['products']}
        return request.render("website_sale.products", result.qcontext)

    def get_stock_info(self, product):
        """function to get stock details"""
        combination_info = product.sudo()._get_combination_info()
        return combination_info['stock'] if product.detailed_type == 'product' \
            else False
