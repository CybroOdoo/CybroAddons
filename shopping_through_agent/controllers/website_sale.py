# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
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
from odoo.addons.payment.controllers import portal as payment_portal
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo import http
from odoo.http import request
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.addons.http_routing.models.ir_http import slug


class WebsiteSale(WebsiteSale):
    """ Class to inherit the functions in the website sale """
    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', min_price=0.0,
             max_price=0.0, ppg=False, **post):
        """ Function to inherit shop and to set the posted value in the
        website session. """
        res = super(WebsiteSale, self).shop(page, category, search, min_price,
                           max_price, ppg, **post)
        order = request.website.sale_get_order()
        if 'post_values' in request.session:
            stored_post_values = request.session['post_values']
            if stored_post_values != post and post:
                order.unlink()
        if post:
            request.session['post_values'] = post
        return res

    @http.route(['/shop/cart'], type='http', auth="public", website=True,
                sitemap=False)
    def cart(self, access_token=None, revive='', **post):
        """ Function to update the address from cart when the sale order is
        created. """
        res = super().cart(access_token, revive, **post)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            order = request.website.sale_get_order()
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    order.update({
                        'partner_id': customer,
                        'partner_invoice_id': customer,
                        'partner_shipping_id': customer,
                        'agent_id': request.env.user.partner_id.id
                        if request.env.user.partner_id.is_agent else ''
                    })
        return res

    def _get_shop_payment_values(self, order, **kwargs):
        """ Function to update the sale order details created from website """
        res = super()._get_shop_payment_values(order, **kwargs)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    website_sale_order = res.get('website_sale_order', {})
                    website_sale_order.update({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                        'agent_id': request.env.user.partner_id.id
                        if request.env.user.partner_id.is_agent else '',
                    })
                    res.update({
                        'partner': customer,
                        'partner_id': customer.id,
                        'website_sale_order': website_sale_order,
                    })
        return res

    def order_2_return_dict(self, order):
        """
        This method is called in the payment process route in order to
        prepare the dict containing the values to be rendered by the
        confirmation template.
        """
        res = super().order_2_return_dict(order)
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    order.update({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                    })
        return res

    def checkout_values(self, **kw):
        """ Updating the billing and shipping address based on customer """
        res = super().checkout_values(**kw)
        if 'post_values' in request.session:
            order = request.website.sale_get_order(force_create=True)
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    res.update({
                        'partner_id': customer,
                        'shippings': customer,
                        'order': order,
                    })
        return res

    @http.route(['/shop/confirmation'], type='http', auth="public",
                website=True, sitemap=False)
    def shop_payment_confirmation(self, **post):
        """ Function to remove the values of post_values from the session """
        res = super().shop_payment_confirmation(**post)
        request.session['post_values'] = {}
        return res


class PaymentPortal(payment_portal.PaymentPortal):
    """ Class to inherit the function to change the details of the
    transactions. """
    @http.route(
        '/shop/payment/transaction/<int:order_id>', type='json',
        auth='public', website=True)
    def shop_payment_transaction(self, order_id, access_token, **kwargs):
        """ Function to change the order details for delivery and invoice """
        res = super().shop_payment_transaction(order_id, access_token, **kwargs)
        order_id = request.env['sale.order'].browse(int(order_id))
        if 'post_values' in request.session:
            post_values = request.session['post_values']
            if post_values:
                customer_id = post_values.get('customer')
                if customer_id:
                    customer = request.env['res.partner'].browse(
                        int(customer_id))
                    order_id.update({
                        'partner_id': customer.id,
                        'partner_invoice_id': customer.id,
                        'partner_shipping_id': customer.id,
                    })
        return res
