# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.http import request


class ProductModel(http.Controller):
    """This controller provides an endpoint for retrieving AR-related data for
    a given product."""

    @http.route('/product/ar_image', type='json', auth='none')
    def get_product_ar_model(self, product_id):
        """This method returns AR related data in the product."""
        product = request.env['product.template'].sudo().browse(
            int(product_id))
        local_url = request.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'product.template'),
             ('res_id', '=', product_id), ('name', '=', product.filename)],
            limit=1).local_url
        return {'type': product.ar_image_type,
                'ar_url': product.ar_url if product.ar_url else False,
                'ar_scale': product.ar_scale,
                'auto_rotate': product.auto_rotate,
                'ar_placement': product.ar_placement,
                'local_url': local_url}
