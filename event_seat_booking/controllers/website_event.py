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
from odoo import _
from odoo.http import request
from odoo.addons.website_event.controllers.main import WebsiteEventController


class WebsiteEventController(WebsiteEventController):
    def _process_tickets_form(self, event, form_details):
        """ Process posted data about ticket order. Generic ticket are supported
        for event without tickets (generic registration).

        :return: list of order per ticket: [{
            'id': if of ticket if any (0 if no ticket),
            'ticket': browse record of ticket if any (None if no ticket),
            'name': ticket name (or generic 'Registration' name if no ticket),
            'quantity': number of registrations for that ticket,
        }, {...}]
        """
        ticket_order = {}

        for key, value in form_details.items():
            registration_items = key.split('nb_register-')
            if len(registration_items) != 2:
                continue
            ticket_order[int(registration_items[1])] = int(value)

        ticket_dict = dict((ticket.id, ticket) for ticket in
                           request.env['event.event.ticket'].sudo().search([
                               ('id', 'in',
                                [tid for tid in ticket_order.keys() if tid]),
                               ('event_id', '=', event.id)
                           ]))
        # Process seat details
        unique_ids = form_details.get('unique_id', '').split(',')
        if not unique_ids or unique_ids == ['']:
            order = [{
                'id': tid if ticket_dict.get(tid) else 0,
                'ticket': ticket_dict.get(tid),
                'name': ticket_dict[tid]['name'] if ticket_dict.get(
                    tid) else _('Registration'),
                'quantity': count,
            } for tid, count in ticket_order.items() if count]
            return order

        column_numbers = form_details.get('column_no', [])
        row_numbers = form_details.get('row_no', [])

        order = []
        for tid, count in ticket_order.items():
            seat_details = []
            for i in range(count):
                index = sum(ticket_order[key] for key in ticket_order.keys() if
                            key < tid) + i
                if index < len(unique_ids):
                    seat_details.append({
                        'unique_id': unique_ids[index],
                        'row_no': row_numbers[index],
                        'column_no': column_numbers[index],
                    })

            order.append({
                'id': tid if ticket_dict.get(tid) else 0,
                'ticket': ticket_dict.get(tid),
                'name': ticket_dict[tid]['name'] if ticket_dict.get(
                    tid) else _('Registration'),
                'quantity': count,
                'seat_details': seat_details,
            })
        return order
