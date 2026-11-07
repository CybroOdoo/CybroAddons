# pylint: disable=unknown-option-value
# pylint: disable=missing-module-docstring
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import base64
import binascii

from odoo import http
from odoo.http import request


class ProductModel(http.Controller):
    """This class represents a 3D product model."""

    @http.route('/product/3d', type='jsonrpc', auth='public', website=True)
    def get_product_3d_model(self, product_id):
        """This method returns a 3D model uploaded in the product."""
        if not product_id:
            return {'3D_model': False}
        try:
            prod_tmpl = request.env['product.template'].sudo()
            product = prod_tmpl.browse(int(product_id))
        except (ValueError, TypeError):
            return {'3D_model': False}

        model_3d = False
        if product.exists() and product.model_3d:
            if hasattr(product.model_3d, 'to_base64'):
                model_3d = product.model_3d.to_base64()
            else:
                model_3d = product.model_3d
        return {
            '3D_model': model_3d,
        }

    @http.route(
        '/product/3d_model/<int:product_id>/model.glb',
        type='http', auth='public', website=True,
    )
    def get_product_3d_model_file(self, product_id):
        """This method returns raw 3D model file uploaded in the product."""
        product = request.env['product.template'].sudo().browse(product_id)
        if product.exists() and product.model_3d:
            raw = product.model_3d
            if hasattr(raw, 'to_base64'):
                raw = base64.b64decode(raw.to_base64())
            elif isinstance(raw, str):
                raw = base64.b64decode(raw)
            elif isinstance(raw, bytes):
                if not raw.startswith(b'glTF'):
                    try:
                        raw = base64.b64decode(raw)
                    except (ValueError, binascii.Error):
                        raw = b''
            return request.make_response(
                raw,
                headers=[
                    ('Content-Type', 'model/gltf-binary'),
                    ('Content-Disposition', 'inline; filename="model.glb"'),
                    ('Cache-Control', 'public, max-age=86400'),
                ],
            )
        return request.not_found()
