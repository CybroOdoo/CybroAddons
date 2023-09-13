# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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
##############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteVariantSale(WebsiteSale):
    """WebsiteSale class is inherited to add the
    functionality to add the variants if selected"""

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Since the buy button is optional this function is supered
        to give buy_now value from the settings to the template"""
        values = super()._prepare_product_values(product, category, search,
                                                 **kwargs)
        res = request.env['res.config.settings'].sudo().search([], limit=1,
                                                               order='id desc')
        values['buy_now'] = res.enabled_buy_now_button
        return values

    @http.route('/shop/cart/multi', type='http', auth="user", website=True)
    def cart_update_multi(self, **post):
        """This controller is triggered when
        the form is submitted and will update
        the cart and redirect to payment if
        selected to will redirect to cart"""
        if post.get('product_tmpl_id'):
            request.website.get_current_pricelist()
            sale_order = request.website.sale_get_order(force_create=1)
            product_template = request.env['product.template'].sudo().browse(
                int(post.get('product_tmpl_id')))
            if product_template:
                for variant in product_template.product_variant_ids:
                    if post.get(f'quantity-{variant.id}'):
                        quantity = float(post.get(f'quantity-{variant.id}'))
                        if quantity >= 1:
                            if sale_order.order_line:
                                for rec in sale_order.order_line:
                                    variant_ids_in_sale = \
                                        [record.product_id.id for record in
                                         sale_order.order_line]
                                    if variant.id not in variant_ids_in_sale:
                                        sale_order._cart_update(
                                            product_id=int(variant.id),
                                            add_qty=float(quantity))
                                    elif rec.product_id.id == variant.id:
                                        rec.product_uom_qty += float(quantity)
                            else:
                                sale_order._cart_update(
                                    product_id=int(variant.id),
                                    add_qty=float(quantity))

        res = request.redirect('/shop/payment') if post.get(
            'buy_now') else request.redirect(
            '/shop/cart')
        return res
