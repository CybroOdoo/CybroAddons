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
#############################################################################
import logging
from markupsafe import escape
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class SpecialProduct(http.Controller):
    """Render one product into one of the snippet's four layouts."""

    VALID_TEMPLATES = {
        'special_product_snippet.first_dynamic_template',
        'special_product_snippet.second_dynamic_template',
        'special_product_snippet.third_dynamic_template',
        'special_product_snippet.fourth_dynamic_template',
    }

    @http.route('/website/snippet/special/render', type='jsonrpc', auth='public',
                website=True)
    def render_template(self, params=None, id=None, template=None, **kw):
        try:
            # Accept either a JSON-encoded `params` blob (legacy) or plain arguments.
            if isinstance(params, str):
                import json
                params = json.loads(params)
            if isinstance(params, dict):
                id = params.get('id', id)
                template = params.get('template', template)

            if not template or template not in self.VALID_TEMPLATES:
                template = 'special_product_snippet.first_dynamic_template'

            product = request.env['product.template'].sudo().browse(
                int(id or 0)).exists()

            company = request.env.company
            currency = company.currency_id.sudo()
            if 'website' in request.env:
                try:
                    website = getattr(request, 'website', None)
                    if not website or getattr(website, '_name', None) != 'website':
                        website = request.env['website'].sudo().search([('company_id', '=', company.id)], limit=1)
                    if not website or getattr(website, '_name', None) != 'website':
                        website = request.env['website'].sudo().search([], limit=1)
                    if website and getattr(website.currency_id, '_name', None) == 'res.currency':
                        currency = website.currency_id.sudo()
                except Exception as err:
                    _logger.debug("Failed to resolve fallback website currency: %s", err)

            # A missing product must fail cleanly.
            if not product:
                return {
                    'error': 'unavailable',
                    'html': request.env['ir.qweb'].sudo()._render(
                        'special_product_snippet.unavailable', {}),
                }

            website_url = getattr(product, 'website_url', None) or f'/shop/{product.id}'

            qcontext = {
                'display_name': product.display_name,
                'list_price': product.list_price,
                'website_url': website_url,
                'image_url': f'/web/image/product.template/{product.id}/image_1920',
                'currency': currency,
            }

            html = request.env['ir.qweb'].sudo()._render(template, qcontext)
            # Only JSON-serialisable values cross the RPC boundary.
            return {
                'html': str(html),
                'qcontext': {k: v for k, v in qcontext.items() if k != 'currency'},
            }
        except Exception as e:
            _logger.exception("Failed to render special product snippet for id=%s, template=%s", id, template)
            return {
                'error': str(e),
                'html': f'<div class="alert alert-danger p-3">Failed to load product: {escape(str(e))}</div>',
            }
