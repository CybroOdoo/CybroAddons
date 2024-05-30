# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
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
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale


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
        price_list = request.website._get_current_pricelist()
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

    @http.route()
    def cart_update_json(self, *args, period=None, **kw):
        """Override to parse to recurrence period."""
        recurrence_period = None
        if period:
            recurrence_period = request.env['recurrence.period'].browse(
                int(period))
        return super(WebsiteSaleSubscription, self).cart_update_json(
            *args, period=recurrence_period, **kw)

    @http.route()
    def shop_payment_confirmation(self, **post):
        """Super controller in website sale and call send mail function."""
        res = super(WebsiteSaleSubscription, self).shop_payment_confirmation(
            **post)
        order = res.qcontext['order']
        subscription_order = request.env[
            'subscription.package'].search(
            [('sale_order_id', '=', order.id)])
        recurrence = [
            {order_line.product_id: order_line.subscription_interval_id}
            for order_line in order.order_line]
        for dictionary in recurrence:
            if (subscription_order.product_line_ids.product_id in
                    dictionary.keys()):
                subscription_order.update({'recurrence_period_id': dictionary[
                    subscription_order.product_line_ids.product_id]})
        subscription_order.send_subscription_order_to_customer()
        return res
