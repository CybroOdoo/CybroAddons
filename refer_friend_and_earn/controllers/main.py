# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
from odoo.http import request
from odoo.addons.website_sale_product_configurator.controllers.main import \
    WebsiteSale


class Cart(WebsiteSale):
    """This class is used to recalculate the discount when we add a product with
     variants to the cart"""
    def cart_options_update_json(self, *args, **kwargs):
        """This class is used to recalculate the discount when we add a product
         with variants to the cart"""
        res = super().cart_options_update_json(*args, **kwargs)
        discount_product_id = request.env['product.product'].sudo().search(
            [('default_code', '=', 'DISCOUNT001')])
        for line in request.website.sale_get_order().order_line:
            if line.product_id.id == discount_product_id.id:
                order_line_discount = line.price_unit
                total_price = sum(request.website.sale_get_order().order_line.mapped('price_subtotal'))
                original_total_price = total_price - order_line_discount
                discount_percentage = request.website.sale_get_order().discount_applied
                discount_amount = original_total_price * (
                        discount_percentage / 100)
                order_line_discount_price = -discount_amount
                order_line = request.website.sale_get_order().order_line.browse(line.id)
                order_line.write({
                    'price_unit': order_line_discount_price,
                })
        return res
