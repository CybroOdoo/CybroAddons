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


class SalonReviewController(http.Controller):

    def _get_booking(self, token):
        return request.env['salon.booking'].sudo().search(
            [('review_token', '=', token), ('state', '=', 'done')], limit=1)

    def _render_page(self, booking, token, rating=0, error=False):
        return request.render('pos_salon.review_page', {
            'booking': booking, 'token': token, 'rating': rating, 'error': error})

    @http.route('/salon/review/<string:token>', type='http', auth='public', methods=['GET'])
    def review_page(self, token, rating=None, **kw):
        booking = self._get_booking(token)
        if not booking:
            return request.render('pos_salon.review_invalid')
        try:
            pre = int(rating)
        except (TypeError, ValueError):
            pre = 0
        return self._render_page(booking, token, rating=pre if 1 <= pre <= 5 else 0)

    @http.route('/salon/review/<string:token>/submit', type='http', auth='public',
                methods=['POST'])
    def review_submit(self, token, rating=None, note='', **kw):
        booking = self._get_booking(token)
        if not booking:
            return request.render('pos_salon.review_invalid')
        if booking.review_date:
            return request.redirect('/salon/review/%s' % token)
        try:
            value = int(rating)
        except (TypeError, ValueError):
            value = 0
        if not 1 <= value <= 5:
            return self._render_page(booking, token, error=True)
        booking.write({
            'rating': value,
            'review_note': (note or '').strip()[:2000],
            'review_date': fields.Datetime.now(),
        })
        return request.redirect('/salon/review/%s' % token)