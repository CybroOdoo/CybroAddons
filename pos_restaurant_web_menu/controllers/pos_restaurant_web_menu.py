# -*- coding: utf-8 -*-
#############################################################################
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
#############################################################################
import base64
from odoo import http, modules
from odoo.http import request
from odoo.tools import file_open


class PosRestaurantWebMenu(http.Controller):
    """ This is the controller for the POS Web Menu App
        There is one main route that the user will use to access the
        POS Web menu: /menu"""

    @http.route("/menu/<config_id>", auth="public", website=True, sitemap=True)
    def pos_web_menu_start(self, config_id=None):
        """This route will render the LANDING PAGE of the POS Web App
        And it will pass the needed data to the template: the list of products
        by category, pos_config_id, table_id, session info...
        After that the user will be able to navigate to products and cart
        pages to the server, using client side routing."""
        pos_config_sudo = request.env["pos.config"].sudo().browse(
            int(config_id))
        current_session = pos_config_sudo.current_session_id
        pos_floor = pos_config_sudo.mapped('floor_ids')
        table = {}
        for floor in pos_floor:
            table[floor.name] = request.env['restaurant.table'].sudo().search(
                [('floor_id', '=', floor.id)])
        image_path = modules.get_module_resource(
            "pos_restaurant_web_menu", "static/src/img",
            "default_background.jpg")
        bg_image = base64.b64encode(file_open(image_path, "rb").read())
        products = request.env["product.product"].sudo().search(
            [('available_in_pos', '=', 'True')])
        customers = request.env["res.partner"].search([])
        pos_category = products.mapped('pos_categ_id.name')
        pos_category.sort()
        currency = request.env.company.currency_id.symbol
        data = {category: products.filtered(
            lambda pos: pos.pos_categ_id.name == category) for category in
            pos_category}
        return request.render(
            'pos_restaurant_web_menu.pos_restaurant_menu_index',
            {'page_background': bg_image, 'table': table, 'data': data,
             'config_id': config_id, 'session_info': current_session,
             'customers': customers, 'currency': currency})

    @http.route("/product/pos_cart", type='json', auth='public')
    def pos_web_cart(self, product_id):
        """ Get information about the product for pos web cart.
        :param int product_id: The ID of the product.
        :return dict: A dictionary containing product information."""
        product = request.env['product.product'].sudo().browse(
            int(product_id))
        currency = request.env.company.currency_id.symbol
        return {'id': product_id, 'display_name': product.display_name,
                'lst_price': product.lst_price, 'currency': currency}
