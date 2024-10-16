# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Junaidul Ansar M (odoo@cybrosys.com)
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
from odoo import http, _
from odoo.http import request


class SeatBookingController(http.Controller):
    """The controller handle for the event seat booking page"""

    @http.route(['''/event/<model("event.event"):event>/SeatsBooking'''],
                type='http', auth='public', website=True)
    def seat_booking_page(self, event):
        """It displays the seat booking information """
        # Fetch the seat arrangement lines related to the event or
        # user(based on your requirement)
        event_tickets = request.env['event.event.ticket'].search([
            ('event_id', '=', event.id),
        ])
        event_seat_templates = {}
        for ticket in event_tickets:
            seat_arrangement_lines = ticket.seat_arrangement_id.prepare_seat_ids
            event_seat_template = {}

            for line in seat_arrangement_lines:
                row_no = line.row_no
                if row_no not in event_seat_template:
                    event_seat_template[row_no] = []

                for column in line.column_ids:
                    seat_data = {
                        'seat_column_id': column.column_no,
                        'reservation_status': column.reservation_status,
                        'row_no': row_no,
                        'column_no': column.column_no,
                        'unique_column': column.unique_seat_identifier
                    }
                    event_seat_template[row_no].append(seat_data)

            event_seat_templates[
                ticket.seat_arrangement_id.id] = event_seat_template
        return request.render(
            'event_seat_booking.event_seat_booking_board_templates',
            {
                'event_name': event.name,
                'event': event.id,
                'event_tickets': event_tickets,
                'event_seat_templates': event_seat_templates,
            })
