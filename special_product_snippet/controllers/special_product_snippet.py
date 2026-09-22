# -*- coding: utf-8 -*-
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
from odoo import http
from odoo.http import request


class SpecialProduct(http.Controller):
    """Render one product into one of the snippet's four layouts."""

    @http.route('/website/snippet/special/render', type='json', auth='public',
                website=True)
    def render_template(self, params=None, id=None, template=None, **kw):
        # Accept either a JSON-encoded `params` blob (legacy) or plain arguments.
        if isinstance(params, str):
            import json
            params = json.loads(params)
        if isinstance(params, dict):
            id = params.get('id', id)
            template = params.get('template', template)

        product = request.env['product.template'].sudo().browse(
            int(id or 0)).exists()
        website = request.website
        currency = website.currency_id or request.env.company.currency_id

        # A missing or unpublished product must fail loudly rather than render
        # `undefined` into the image and link URLs, which is what produced the
        # 404 on /undefined.
        if not product or not product.is_published:
            return {
                'error': 'unavailable',
                'html': request.env['ir.qweb']._render(
                    'special_product_snippet.unavailable', {}),
            }

        qcontext = {
            'display_name': product.display_name,
            'list_price': product.list_price,
            'website_url': product.website_url,
            'image_url': '/web/image/product.template/%s/image_1920' % product.id,
            'currency': currency,
        }

        html = request.env['ir.qweb']._render(template, qcontext)
        # Only JSON-serialisable values cross the RPC boundary. The previous
        # version put a res.company recordset in here.
        return {
            'html': str(html),
            'qcontext': {k: v for k, v in qcontext.items() if k != 'currency'},
        }
