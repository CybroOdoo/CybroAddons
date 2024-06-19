# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anagha S (odoo@cybrosys.com)
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
###############################################################################
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
