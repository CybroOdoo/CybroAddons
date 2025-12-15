# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request, route


class WebSiteVapiController(http.Controller):
    """This controller handles various HTTP routes related to VAPI assistant
     integration and product-related operations on the website."""

    @route('/website_assistant', auth='public', type='jsonrpc',
           website=True)
    def website_assistant_data(self):
        """Get the values from the settings and return as data dictionary. """
        private_api_key = request.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_private_api_key')
        public_api_key = request.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_base.vapi_public_api_key')
        assistant = request.env['ir.config_parameter'].sudo().get_param(
            'ora_ai_website.website_assistant_id')
        assistant_id = request.env['ora.ai'].sudo().browse(
            int(assistant)).id_assistant
        return {'public_api_key': public_api_key,
                'assistant': assistant_id,
                'private_api_key': private_api_key}

    @route('/get_product_template_id', auth='public', type='jsonrpc', website=True)
    def get_product_id(self, product):
        """Fetch the corresponding product template."""
        product_id = request.env['product.product'].sudo().browse(product)
        return product_id.product_tmpl_id.id

    @route('/get_variant_product_id', auth='public', type='jsonrpc',
           website=True)
    def get_variant_product_id(self, **args):
        """Fetch the product variant ID that matches the given product
         name and variant attribute values."""
        variant = args.get('variant_name')
        att_value_list = [var.strip() for var in variant.split(",")]
        att_id_list = []
        for val in att_value_list:
            att_id_list.append(request.env['product.attribute.value'].search(
                [('name', '=', val)]).id)
        product_variants = request.env['product.product'].search(
            [('name', '=', args.get('product_name'))])
        variant_product_id = []
        for rec in product_variants:
            variant_product_ids = rec.product_template_variant_value_ids.ids
            variants = rec.product_template_variant_value_ids.mapped('name')
            if (variant_product_ids == att_id_list or
                    variants == att_value_list):
                variant_product_id.append(rec.id)
        return {
            'variant_product_id': variant_product_id[0]
        }

    @route('/get_product_name', auth='public', type='jsonrpc', website=True)
    def get_product_name(self):
        """Getting all the published product names."""
        product_name = request.env['product.template'].sudo().search(
            [('is_published', '=', True)]).mapped('name')
        return {'product_name': product_name}

    @route('/shop/add_cart_order', auth='public', type='jsonrpc', website=True)
    def add_to_cart(self):
        """ Add multiple products to the website cart."""
        is_order = False
        order = request.cart or request.website._create_cart()
        if order:
            is_order = True
        return {
            'is_order': is_order,
        }
