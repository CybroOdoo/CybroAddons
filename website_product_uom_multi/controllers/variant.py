# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
    @http.route('/website_sale/get_combination_info', type='json',
                auth='public',
                methods=['POST'], website=True)
    def get_combination_info_website(
            self, product_template_id, product_id, combination, add_qty,
            uom=False,
            parent_combination=None,
            **kwargs
    ):
        res = super(
            Vairant, self).get_combination_info_website(
            product_template_id=product_template_id, product_id=product_id,
            combination=combination, add_qty=add_qty,
            uom=uom, parent_combination=parent_combination, **kwargs)
        request.session['uom_id'] = uom
        if uom:
            uom_id = request.env['uom.uom'].browse(int(uom))
            product = request.env['product.product'].sudo().browse(product_id)
            default_uom_qty = uom_id._compute_quantity(add_qty, product.uom_id)
            updated_price = res['list_price'] * default_uom_qty
            res.update({'price': updated_price})
        return res
