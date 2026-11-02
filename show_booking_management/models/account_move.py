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
from odoo import Command, api, fields, models


class AccountMove(models.Model):
    """
        Add a Many2one field to link movie tickets with account moves and
        keep the pending booking of a ticket invoice until it is paid.
    """
    _inherit = 'account.move'

    movie_ticket_id = fields.Many2one('movie.registration',
                                      string='Movie Ticket ID',
                                      help='Movie ticket ID')
    movie_booking_data = fields.Json(
        copy=False,
        help='Pending booking (movie, screen, time slot, date, seats) of this '
             'invoice. It is turned into a ticket once the invoice is paid, '
             'then cleared. It is never taken from the client after the '
             'invoice has been created.')
    movie_booking_issue = fields.Boolean(
        string='Movie Booking Needs Attention', copy=False,
        help='The invoice was paid but the booking could not be confirmed '
             '(for example a seat was taken meanwhile). Staff must follow up.')

    @api.model
    def _create_movie_booking_invoice(self, partner, movie, booking_data):
        """ Create and post the invoice of a booking. The booking data is
        stored on the invoice so the payment post-processing can issue the
        ticket without any HTTP session.

        :param res.partner partner: The customer to invoice.
        :param movie.movie movie: The booked show; its price is used.
        :param dict booking_data: movie_id, screen_id, time_slot_id,
            booking_date, selected_seats and optional registration_id.
        :rtype: account.move
        """
        invoice = self.sudo().create({
            'move_type': 'out_invoice',
            'invoice_origin': 'Movie',
            'partner_id': partner.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': [Command.create({
                'name': self.env._("Ticket for %(movie)s on %(date)s",
                           movie=movie.name, date=booking_data['booking_date']),
                'product_id': self.env.ref('show_booking_management.product_1').id,
                'quantity': len(booking_data['selected_seats']),
                'price_unit': movie.price,
            })],
            'movie_booking_data': booking_data,
        })
        invoice.action_post()
        return invoice
