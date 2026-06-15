# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (LGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json
from markupsafe import escape
from odoo import http
from odoo.http import request


class ThemeKidsCareController(http.Controller):
    @http.route(
        '/theme_kids_care/cart/add',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False,
    )
    def theme_kids_care_cart_add(
        self, product_id, add_qty=1, set_qty=0,
        product_custom_attribute_values=None, no_variant_attribute_values=None,
        **kwargs
    ):
        """
        Adds a product to the cart and redirects to the shopping cart page.
        :param product_id: ID of the product to add.
        :param add_qty: Quantity to add.
        :param set_qty: Quantity to set (overrides current quantity if non-zero).
        :param product_custom_attribute_values: Custom attribute values in JSON.
        :param no_variant_attribute_values: No-variant attribute values in JSON.
        :return: Redirect to /shop/cart.
        """
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)
        if product_custom_attribute_values:
            product_custom_attribute_values = json.loads(product_custom_attribute_values)
        if no_variant_attribute_values:
            no_variant_attribute_values = json.loads(no_variant_attribute_values)
        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values,
            **kwargs
        )
        request.session['website_sale_cart_quantity'] = sale_order.cart_quantity
        return request.redirect('/shop/cart')

    @http.route(
        '/theme_kids_care/contactus/submit',
        type='http',
        auth='public',
        website=True,
        methods=['POST'],
        csrf=False,
    )
    def theme_kids_care_contact_submit(self, **post):
        """
        Processes the contact form submission and sends an email to the company.
        :param post: Dictionary containing form fields (name, email_from, subject, description).
        :return: Redirect to /contactus-thank-you.
        """
        company = request.website.company_id
        email_to = company.email or request.env.user.email or ''
        name = (post.get('name') or '').strip()
        email_from = (post.get('email_from') or '').strip()
        subject = (post.get('subject') or '').strip() or 'Website Contact'
        description = (post.get('description') or '').strip()
        body_html = """
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
        """.format(
            name=escape(name),
            email=escape(email_from),
            message=escape(description).replace('\n', '<br/>'),
        )
        request.env['mail.mail'].sudo().create({
            'subject': subject,
            'email_to': email_to,
            'email_from': email_from or email_to,
            'reply_to': email_from or email_to,
            'body_html': body_html,
        }).send()
        return request.redirect('/contactus-thank-you')
