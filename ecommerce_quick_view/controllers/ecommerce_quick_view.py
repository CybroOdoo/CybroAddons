# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import http
from odoo.fields import Domain
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class QuickViewWebsiteSale(WebsiteSale):
    """Controller for quick view functionality."""

    @http.route(
        '/c_quick_view/get_quick_view_html',
        type='jsonrpc',
        auth='public',
        website=True,
        sitemap=False,
    )
    def get_quick_view_html(self, product_id=None, **kwargs):
        """Generate quick view HTML for the given product."""
        try:
            product_id = int(product_id or 0)
        except (TypeError, ValueError):
            return ""
        if not product_id:
            return ""

        # `request.website` no longer exists: the current website lives on env.
        website = request.env.website
        if not website.has_ecommerce_access():
            return ""

        # Only products the current visitor may see on this website
        # (published, right website, saleable). No blanket sudo().
        product = request.env['product.template'].search(
            Domain('id', '=', product_id)
            & Domain(website.sale_product_domain()),
            limit=1,
        )
        if not product:
            return ""

        # Signature is _prepare_product_values(self, product, **kwargs); it
        # already computes combination_info (with the visitor's pricelist)
        # for the first possible combination, so nothing else is needed.
        values = self._prepare_product_values(product)
        combination_info = values['combination_info']

        values.update({
            'combination': product._get_first_possible_combination(),
            'product_variant_id': combination_info.get('product_id'),
            'add_qty': 1,
        })

        # Render through the website so the frontend QWeb context is added
        # (is_view_active, website, editable, ...). Rendering with
        # request.env['ir.qweb']._render() directly skips all of that and
        # breaks website_sale templates such as website_sale.product_price.
        return website._render_template(
            'ecommerce_quick_view.c_product_quick_view',
            values,
        )