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
from odoo import fields, http
from odoo.http import request
from odoo.tools import email_normalize


class WebsitePreBookingController(http.Controller):
    """Website routes for placing and tracking pre-bookings."""

    @staticmethod
    def _parse_quantity(value):
        try:
            quantity = int(value)
        except (TypeError, ValueError):
            return 0
        return quantity if quantity > 0 else 0

    def _create_booking(
        self, product, quantity, partner=None, partner_values=None
    ):
        if not product.sudo()._reserve_pre_booking_quantity(quantity):
            return request.render(
                'website_pre_booking.pre_booking_failed',
                {'main_object': product},
            )
        if partner_values:
            partner = request.env['res.partner'].sudo().create(partner_values)
        booking = request.env['website.prebook'].sudo().create({
            'partner_id': partner.id,
            'booking_date': fields.Date.context_today(request.env.user),
            'product_id': product.id,
            'quantity': quantity,
            'website_id': request.env.website.id if request.env.website else False,
        })
        return request.render(
            'website_pre_booking.pre_booking_done',
            {'ref': booking.reference, 'main_object': product},
        )

    @http.route(
        '/my/prebook_request/<model("product.template"):product>',
        type='http', auth='public', website=True, methods=['POST'],
    )
    def create_pre_booking(self, product, **post):
        """Create a reservation or collect guest contact details."""
        if not product.pre_book:
            return request.redirect('/shop')

        quantity = self._parse_quantity(post.get('prod_qty'))
        if (
            not quantity
            or not product._is_pre_booking_available()
            or quantity > product.pre_max_quantity
        ):
            return request.render(
                'website_pre_booking.pre_booking_failed',
                {'main_object': product},
            )

        partner = False
        if not request.env.website.is_public_user():
            partner = request.env.user.partner_id
            existing_booking = request.env['website.prebook'].search([
                ('partner_id', '=', partner.id),
                ('product_id', '=', product.id),
            ], limit=1)
            if existing_booking:
                return request.render(
                    'website_pre_booking.pre_booking_done',
                    {
                        'ref': existing_booking.reference,
                        'main_object': product,
                    },
                )

        if not partner:
            return request.render(
                'website_pre_booking.prebook_address',
                {
                    'product_id': product.id,
                    'quantity': quantity,
                    'main_object': product,
                },
            )
        return self._create_booking(product, quantity, partner=partner)

    @http.route(
        '/prebook/address', type='http', methods=['POST'], auth='public',
        website=True, sitemap=False,
    )
    def pre_address(self, **post):
        """Create a guest booking after validating its product and quantity."""
        try:
            product_id = int(post.get('product_id', ''))
        except (TypeError, ValueError):
            product_id = 0
        product = request.env['product.template'].search([
            ('id', '=', product_id),
            ('website_published', '=', True),
            ('pre_book', '=', True),
        ], limit=1)
        quantity = self._parse_quantity(post.get('quantity'))
        name = (post.get('name') or '').strip()
        email = email_normalize(post.get('email') or '')
        phone = (post.get('phone') or '').strip()

        if (
            not product
            or not quantity
            or not product._is_pre_booking_available()
            or quantity > product.pre_max_quantity
            or not name
            or not email
        ):
            return request.render('website_pre_booking.pre_booking_failed')

        partner_values = {
            'name': name,
            'email': email,
            'phone': phone,
        }
        return self._create_booking(
            product, quantity, partner_values=partner_values,
        )

    @http.route(
        '/track/prebooking', type='http', auth='public', website=True,
        methods=['POST'],
    )
    def submit_booking(self, **post):
        """Show a booking owned by the signed-in customer or email holder."""
        reference = (post.get('reference') or '').strip()
        if request.env.website.is_public_user():
            email = email_normalize(post.get('email') or '')
            booking = request.env['website.prebook'].sudo().search([
                ('reference', '=', reference),
                ('partner_id.email_normalized', '=', email),
                ('partner_id.user_ids', '=', False),
            ], limit=1) if email else request.env['website.prebook']
        else:
            booking = request.env['website.prebook'].search([
                ('reference', '=', reference),
                ('partner_id', '=', request.env.user.partner_id.id),
            ], limit=1)
        if not booking:
            return request.render(
                'website_pre_booking.my_booking_template',
                {'booking': False, 'not_found': True},
            )

        status = dict(booking._fields['state'].selection).get(booking.state)
        if booking.sale_id:
            status = {
                'draft': 'Quotation',
                'sent': 'Quotation Sent',
                'sale': 'Sales Order',
                'done': 'Locked',
                'cancel': 'Cancelled',
            }.get(booking.sale_id.state, status)
        return request.render(
            'website_pre_booking.my_booking_template',
            {'booking': booking, 'booking_status': status, 'not_found': False},
        )

    @http.route('/my/prebookings', type='http', auth='public', website=True)
    def my_prebookings(self):
        """Render the booking reference search form."""
        return request.render(
            'website_pre_booking.my_booking_template',
            {'booking': False, 'not_found': False},
        )

    @http.route('/sale/fail', type='http', auth='public', website=True)
    def my_prebookings_fail(self):
        """Show the unavailable-quantity message."""
        return request.render('website_pre_booking.pre_booking_failed')
