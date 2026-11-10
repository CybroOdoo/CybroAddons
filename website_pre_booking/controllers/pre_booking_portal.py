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
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    """Used to manage a customer portal"""

    def _prepare_home_portal_values(self, counters):
        """Add pre_bookings_count to home portal values"""
        values = super()._prepare_home_portal_values(counters)
        if 'pre_bookings_count' in counters:
            current_user = request.env.user.partner_id
            pre_bookings_count = request.env['website.prebook'].search_count(
                [('partner_id', '=', current_user.id)]
            )
            values['pre_bookings_count'] = pre_bookings_count
        return values

    def _prepare_portal_layout_values(self):
        """Add pre_bookings_count to portal layout values"""
        values = super()._prepare_portal_layout_values()
        current_user = request.env.user.partner_id
        values['pre_bookings_count'] = (
            request.env['website.prebook'].sudo().search_count([
                ('partner_id', '=', current_user.id),
            ])
        )
        return values

    def _prepare_portal_counter_values(self, counter):
        """Return search values for Odoo portal counter"""
        if counter == 'pre_bookings_count':
            partner = request.env.user.partner_id
            return 'website.prebook', [('partner_id', '=', partner.id)], 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route(['/my/pre_bookings'], type='http', auth="user", website=True)
    def portal_my_pre_bookings(self):
        """Function to view the logged-in user pre bookings in the account."""
        current_user = request.env.user.partner_id
        pre_booking = request.env['website.prebook'].sudo().search(
            [('partner_id', '=', current_user.id)])
        return request.render("website_pre_booking.portal_my_pre_bookings",
                              {'pre_bookings': pre_booking,
                               'page_name': 'pre_booking'})

