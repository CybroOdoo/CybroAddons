# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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

from odoo.addons.website_sale.controllers.variant import \
    WebsiteSaleVariantController


class Vairant(WebsiteSaleVariantController):
    @http.route('/website_sale/get_combination_info', type='jsonrpc',
                auth='public',
                methods=['POST'], website=True)
    def get_combination_info_website(
            self, product_template_id, product_id, combination, add_qty,
            uom=False,
            parent_combination=None,
            **kwargs
    ):
        # Set UOM in session before calling super so Odoo's internal price calculation uses it
        if uom:
            request.session['uom_id'] = int(uom)

        res = super(Vairant, self).get_combination_info_website(
            product_template_id=product_template_id, product_id=product_id,
            combination=combination, add_qty=add_qty,
            uom=uom, parent_combination=parent_combination, **kwargs)

        if uom:
            uom_record = request.env['uom.uom'].sudo().browse(int(uom))
            product = request.env['product.product'].sudo().browse(product_id)
            
            # Compute how many base units are in 1 unit of the selected UOM
            uom_factor = uom_record._compute_quantity(1.0, product.uom_id)
            
            # Scale both the price (includes discounts) and list_price
            res['price'] = res['price'] * uom_factor
            res['list_price'] = res['list_price'] * uom_factor
            
        return res
