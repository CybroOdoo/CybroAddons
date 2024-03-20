# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import http, _
from odoo.http import request
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        """super the function to add new button in the home portal"""
        values = super()._prepare_home_portal_values(counters)
        if 'pre_bookings_count' in counters:
            current_user = request.env['res.users'].sudo().browse(
                request.env.uid)
            pre_bookings_count = request.env['website.prebook'].search_count([('partner_id', '=', current_user.partner_id.id)])
            values['pre_bookings_count'] = pre_bookings_count
        return values

    @http.route(['/my/pre_bookings'], type='http', auth="user", website=True)
    def portal_my_pre_bookings(self, **kwargs):
        """Function to view the logined user pre bookings in the account."""
        current_user = request.env['res.users'].sudo().browse(request.env.uid)
        pre_booking = request.env['website.prebook'].sudo().search(
            [('partner_id', '=', current_user.partner_id.id)])
        return request.render("website_pre_booking.portal_my_pre_bookings",
                              {'pre_bookings': pre_booking,
                               'page_name': 'pre_booking'})