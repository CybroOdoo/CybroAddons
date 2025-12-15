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
from odoo import fields, http
from odoo.http import request, route


class WebSiteVapiController(http.Controller):
    """This controller handles various HTTP routes related to VAPI assistant
     integration and product-related operations on the website."""

    @route('/website_assistant', auth='public', type='json',
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

    @route('/get_product_id', auth='public', type='json', website=True)
    def get_product_id(self, **args):
        """Fetch the corresponding product."""
        product = args.get('product_name')
        product_id = request.env['product.product'].sudo().search(
            [('name', '=', product)])
        return {'product_id': product_id.id}

    @route('/get_variant_product_id', auth='public', type='json',
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

    @route('/get_product_name', auth='public', type='json', website=True)
    def get_product_name(self):
        """Getting all the published product names."""
        product_name = request.env['product.template'].sudo().search(
            [('is_published', '=', True)]).mapped('name')
        return {'product_name': product_name}

    @route('/shop/add_to_cart', auth='public', type='json', website=True)
    def add_to_cart(self, products):
        """ Add multiple products to the website cart."""
        order = request.website.sale_get_order(
            force_create=1)
        val = []
        for product_id_str, quantity in products.items():
            product_id = int(product_id_str)
            view = request.env['ir.ui.view']
            values = order._cart_update(product_id=product_id,
                                        add_qty=quantity)
            values['website_sale.cart_lines'] = view._render_template(
                "website_sale.cart_lines", {
                    'website_sale_order': order,
                    'date': fields.Date.today(),
                    'suggested_products': order._cart_accessories()})
            values['website_sale.total'] = view._render_template(
                "website_sale.total", {
                    'website_sale_order': order})
            request.session['website_sale_cart_quantity'] = order.cart_quantity
            values['cart_quantity'] = order.cart_quantity
            val.append(values)
            line_ids = [values['line_id']]
            lines = order.order_line.filtered(lambda line: line.id in line_ids)
            show_tax = order.website_id.show_line_subtotals_tax_selection == 'tax_included'
            notification = {
                'currency_id': order.currency_id.id,
                'lines': [{'id': line.id,
                           'image_url': order.website_id.image_url(
                               line.product_id, 'image_128'),
                           'quantity': line.product_uom_qty,
                           'name': line.name_short,
                           'description': line._get_sale_order_line_multiline_description_variants(),
                           'line_price_total': (
                               line.price_total
                               if show_tax
                               else line.price_subtotal
                           ),
                           } for line in lines
                          ],
            }
            values['notification_info'] = notification
        return {
            'success': True,
            'order_id': order.id,
            'order_total': order.amount_total,
            'values': val,
        }
