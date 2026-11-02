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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class ShowPortal(CustomerPortal):
    """ Prepare the counter of the portal home and list the bookings of the user."""

    def _own_registrations_domain(self):
        """ Registrations of the user's commercial partner (the same scope as
        the portal ir.access row). """
        partner = request.env.user.partner_id
        return [('partner_id', 'child_of', [partner.commercial_partner_id.id])]

    def _prepare_portal_counter_values(self, counter):
        """ Counter of the "Show Bookings" card: the user's own registrations
        (all of them for a system administrator, as the list below).

        Replaces `_prepare_home_portal_values`, which portal no longer calls.
        The route checks the access level before counting.
        """
        if counter == 'shows_count':
            if request.env.user.has_group('base.group_system'):
                return 'movie.registration', [], 'sudo'
            return 'movie.registration', self._own_registrations_domain(), 'read'
        return super()._prepare_portal_counter_values(counter)

    @http.route('/my/shows', type='http', auth="user", website=True)
    def my_subscription(self, **kw):
        """
            Retrieve shows for the user based on permissions and render them on the portal.
        """
        Registration = request.env['movie.registration']
        if request.env.user.has_group('base.group_system'):
            shows = Registration.sudo().search([])
        elif Registration.has_access('read'):
            # Searched as the user (ACL + own partner), rendered as sudo: the
            # movie, screen and time slot names are not readable by portal users.
            shows = Registration.search(self._own_registrations_domain()).sudo()
        else:
            shows = Registration.browse()
        values = {
            'shows': shows,
        }
        return request.render('show_booking_management.portal_my_shows', values)
