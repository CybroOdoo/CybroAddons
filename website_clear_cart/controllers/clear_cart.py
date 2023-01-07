#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import http
from odoo.http import request


class WebsiteClearCart(http.Controller):

    @http.route(['/shop/remove_items'], type="http", auth="public", website=True)
    def remove_cart_items(self):
        """It will remove all items from cart and redirect to shop page"""
        current_orders = request.website.sale_get_order()
        if current_orders:
            for line in current_orders.website_order_line:
                line.unlink()
        return request.redirect('/shop/cart')
