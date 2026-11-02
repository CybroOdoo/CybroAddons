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
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.urls import url_encode
from odoo import http, fields
from odoo.exceptions import AccessError, ValidationError
from odoo.http import request


def _int_param(value):
    """ An integer request parameter; 400 when it is not one. """
    try:
        return int(value)
    except (TypeError, ValueError) as error:
        raise BadRequest() from error


class MovieShow(http.Controller):
    """ This class defines the HTTP routes and movie shows.
        It provides functionality to render the movie template for user
        interaction. Booking is reserved to logged-in users allowed to read
        the shows (the show groups): the other users get a 403 from the ACL and
        visitors are redirected to the login page."""
    @http.route(['/show'], type='http', auth="user", csrf=False, website=True)
    def show_movies(self):
        """ Function for rendering show page."""
        Movie = request.env['movie.movie']
        today = fields.Date.context_today(Movie)
        movies = Movie.search(['|', ('state', '=', 'ongoing'),
                               '&', ('state', '=', 'prebooking'),
                               '&', ('booking_start_date', '<=', today),
                               '|', ('booking_end_date', '>=', today),
                                    ('booking_end_date', '=', False)])
        return http.request.render('show_booking_management.show_movie',
                                   {'movies': movies})

    @http.route(['/book_now/<int:movie_id>'], type='http', auth="user",
                csrf=False, website=True)
    def book_now(self, movie_id):
        """ Function for rendering booking page while clicking the button book now."""
        movie = request.env['movie.movie'].browse(movie_id).exists()
        if not movie:
            raise NotFound()
        return http.request.render('show_booking_management.book_movie',
                                   {'movie': movie})

    @http.route('/movie/book_ticket', type='http', auth='user', website=True,
                methods=['POST', 'GET'], csrf=False)
    def book_ticket(self, **kwargs):
        """ Function for submitting the form and rendering the seat selection chart."""
        movie_id = request.env['movie.movie'].browse(
            _int_param(kwargs.get('movie_id'))).exists()
        screen_id = request.env['movie.screen'].browse(
            _int_param(kwargs.get('screen'))).exists()
        time_slot_id = request.env['time.slots'].browse(
            _int_param(kwargs.get('time_slots'))).exists()
        if not (movie_id and screen_id and time_slot_id):
            raise NotFound()
        # Only a numeric id is echoed back into the page (it is validated on confirmation)
        registration_id = _int_param(kwargs.get('registration_id') or 0) or False
        booked_seats = request.env['movie.seats'].search([
            ('screen_id', '=', screen_id.id),
            ('time_slot_id', '=', time_slot_id.id),
            ('date', '=', kwargs.get('show_date')),
            ('is_booked', '=', True)
        ]).mapped('seat')

        return http.request.render(
            'show_booking_management.seat_selection_template',
            {'screen': screen_id, 'movie': movie_id,
             'time_slot_id': time_slot_id, 'booked_seats': booked_seats,
             'booked_seats_count': len(booked_seats),
             'available_seats_count': screen_id.total_seat_count - len(booked_seats),
             'booking_date': kwargs.get('show_date'),
             'registration_id': registration_id})

    @http.route('/movie/confirm_booking', type='http', auth='user',
                website=True, methods=['POST'], csrf=True)
    def confirm_booking(self, **post):
        """ Function for confirming the seats selection and creating invoice.

        Nothing posted is trusted: the whole booking is validated first (show
        open, screen and time slot of the show, date, seats on the chart and
        free, capacity), and a registration to complete must be a draft the user
        may write. The price always comes from the show."""
        # The validation and the invoice below run as sudo, so the ACL is
        # checked here: only users who may create registrations (the show
        # groups) can book, like they are the only ones who can open the pages.
        request.env['movie.registration'].check_access('create')
        booking_data = {
            'movie_id': post.get('movie_id'),
            'screen_id': post.get('screen_id'),
            'time_slot_id': post.get('time_slot_id'),
            'booking_date': post.get('booking_date'),
            'selected_seats': request.httprequest.form.getlist('selected_seats'),
            'registration_id': post.get('registration_id'),
        }
        try:
            show = request.env['movie.registration'].sudo()._validate_booking_values(booking_data)
        except ValidationError as error:
            raise BadRequest(error.args[0]) from error
        draft_ticket = show['draft_ticket']
        if draft_ticket:
            try:
                # As the user, not sudo: taking over a draft needs write access on it
                request.env['movie.registration'].browse(draft_ticket.id).check_access('write')
            except AccessError as error:
                raise Forbidden() from error
        invoice = request.env['account.move']._create_movie_booking_invoice(
            request.env.user.partner_id, show['movie'], {
                'movie_id': show['movie'].id,
                'screen_id': show['screen'].id,
                'time_slot_id': show['time_slot'].id,
                'booking_date': str(show['date']),
                'selected_seats': show['seats'],
                'registration_id': draft_ticket.id or False,  # Draft ticket to complete, if any
            })
        access_token = invoice._portal_ensure_token()
        params = {
            'access_token': access_token,
            'payment_method_id': post.get('payment_method_id'),
        }
        return request.redirect(f'/my/invoices/{invoice.id}?{url_encode(params)}')
