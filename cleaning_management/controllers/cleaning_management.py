# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad TK (odoo@cybrosys.com)
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
from datetime import datetime

from odoo import http
from odoo.http import request


class CleaningRequest(http.Controller):
    """Create a controller function that retrieves all data from the backend,
     sends it to the frontend, and handles the storage of data sent from
     the frontend back to the backend."""

    @http.route(['/cleaning/request/form'], type='http',
                auth="user", website=True)
    def request_form(self):
        """Retrieving data from the backend."""
        customer_name_rec = http.request.env['res.partner'].sudo().search([])
        building_type_rec = http.request.env['building.type'].sudo().search([])
        cleaning_team_id = http.request.env['cleaning.team'].sudo().search([])
        location_state_id = http.request.env['res.country.state'].sudo().search(
            [])
        return http.request.render(
            "cleaning_management.cleaning_online_request", {
                'customer_name_rec': customer_name_rec,
                'building_type_rec': building_type_rec,
                'location_state_id': location_state_id,
                'cleaning_team_id': cleaning_team_id,
            })

    @http.route(['/cleaning/request/form/submit'], type='http',
                auth="public", website=True)
    def online_request_cleaning_form(self, **kw):
        """Storing data into the backend."""
        bookings = request.env['cleaning.booking'].sudo().create({
            'customer_name_id': kw.get('customer_name_id'),
            'address': kw.get('address'),
            'building_type_id': kw.get('building_type_id'),
            'booking_date': kw.get('booking_date'),
            'cleaning_date': str(
                datetime.fromisoformat(kw.get('cleaning_date'))),
            'cleaning_time': (kw.get('cleaning_time')),
            'cleaning_team_id': (kw.get('cleaning_team_id')),
            'location_state_id': (kw.get('location_state_id')),
            'description': kw.get('description')
        })
        value = {
            'vals': bookings,
        }
        return http.request.render("cleaning_management.cleaning_online_thanks",
                                   value)
