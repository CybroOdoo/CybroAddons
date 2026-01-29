# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.tools.json import scriptsafe as json_scriptsafe


class WebsiteSaleSubscription(WebsiteSale):
    """Inherited class of website sale."""

    @http.route(['/shop/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def product(self, product, category='', search=''):
        """Add Subscription plan and recurrence period for subscription
        Product in website."""
        product_context = dict(request.env.context, active_id=product.id)
        product_category = request.env['product.public.category']
        if category:
            category = product_category.browse(int(category)).exists()
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, value.split("-")) for value in attrib_list if
                         value]
        attrib_set = {value[1] for value in attrib_values}
        keep = QueryURL('/shop', category=category and category.id,
                        search=search, attrib=attrib_list)
        categories = product_category.search([('parent_id', '=', False)])
        price_list = request.website.get_current_pricelist()
        from_currency = request.env.user.company_id.currency_id
        to_currency = price_list.currency_id
        compute_currency = lambda price: from_currency.compute(price,
                                                               to_currency)
        subscription_plan = []
        recurrence_period = []
        if not product_context.get('pricelist'):
            product_context['pricelist'] = price_list.id
            product = product.with_context(product_context)
        if product.is_subscription:
            subscription_product = request.env[
                'product.template'].sudo().browse(product.id)
            subscription_plan = subscription_product.subscription_plan_id
            recurrence_period = (subscription_product.
                                 subscription_recurrence_period_ids)
        values = {
            'search': search,
            'category': category,
            'pricelist': price_list,
            'attrib_values': attrib_values,
            'compute_currency': compute_currency,
            'attrib_set': attrib_set,
            'keep': keep,
            'categories': categories,
            'main_object': product,
            'product': product,
            'subscription_plan': subscription_plan,
            'recurrence_period': recurrence_period
        }
        return request.render("website_sale.product", values)

    @http.route(['/shop/cart/update_json'], type='json', auth="public",
                methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None,
                         set_qty=None, display=True, **kw):
        """
        This route is called :
            - When changing quantity from the cart.
            - When adding a product from the wishlist.
            - When adding a product to cart on the same page
            (without redirection).
        """
        order = request.website.sale_get_order(force_create=1)
        if order.state != 'draft':
            request.website.sale_reset()
            if kw.get('force_create'):
                order = request.website.sale_get_order(force_create=1)
            else:
                return {}

        pcav = kw.get('product_custom_attribute_values')
        nvav = kw.get('no_variant_attribute_values')
        value = order._cart_update(
            product_id=product_id,
            line_id=line_id,
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=json_scriptsafe.loads(
                pcav) if pcav else None,
            no_variant_attribute_values=json_scriptsafe.loads(
                nvav) if nvav else None,
            period=kw.get('period')
        )

        if not order.cart_quantity:
            request.website.sale_reset()
            return value

        order = request.website.sale_get_order()
        value['cart_quantity'] = order.cart_quantity

        if not display:
            return value

        value['website_sale.cart_lines'] = request.env[
            'ir.ui.view']._render_template("website_sale.cart_lines", {
            'website_sale_order': order,
            'date': fields.Date.today(),
            'suggested_products': order._cart_accessories()
        })
        value['website_sale.short_cart_summary'] = request.env[
            'ir.ui.view']._render_template("website_sale.short_cart_summary", {
            'website_sale_order': order,
        })
        return value
