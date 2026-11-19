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
from odoo import http
from odoo.http import request


class OraAiWebsite(http.Controller):
    """Data for the voice assistant of the shop page"""

    @http.route('/ora_ai_website/assistant', type='jsonrpc', auth='public',
                website=True)
    def assistant_data(self):
        """Public key and assistant to start the call in the browser, and the
        published products to highlight the ones the assistant talks about"""
        assistant = request.env['ora.ai']._get_website_assistant()
        if not assistant:
            return {}
        products = request.env['product.template'].sudo().search(
            request.env.website.sale_product_domain())
        return {
            'public_api_key': request.env['ir.config_parameter'].sudo().get_str(
                'ora_ai_base.vapi_public_api_key'),
            'assistant': assistant.id_assistant,
            'product_names': products.mapped('name'),
        }

    @http.route('/ora_ai_website/language', type='jsonrpc', auth='public',
                website=True)
    def language_overrides(self, code):
        """Settings of the call in the language the visitor chose"""
        assistant = request.env['ora.ai']._get_website_assistant()
        return assistant._get_language_overrides(code) if assistant else {}

    @http.route('/ora_ai_website/products', type='jsonrpc', auth='public',
                website=True)
    def product_templates(self, product_ids):
        """Templates of the products ordered through the assistant that can
        be added to the cart, by product id"""
        ids = [int(pid) for pid in product_ids if str(pid).isdigit()]
        products = request.env['product.product'].sudo().browse(ids).exists()
        return {product.id: product.product_tmpl_id.id for product in products
                if product._is_add_to_cart_allowed()}
