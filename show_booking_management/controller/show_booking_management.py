# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import json
from werkzeug.urls import url_encode
from odoo import http, fields
from odoo.http import request


class MovieShow(http.Controller):
    """ This class defines the HTTP routes and movie shows.
        It provides functionality to render the movie template for user
        interaction."""
    @http.route(['/show'], type='http', auth="public", csrf=False, website=True)
    def show_movies(self):
        """ Function for rendering show page."""
        movies = request.env['movie.movie'].search([('state', '=', 'ongoing')])
        return http.request.render('show_booking_management.show_movie',
                                   {'movies': movies})

    @http.route(['/book_now/<int:movie_id>'], type='http', auth="public",
                csrf=False, website=True)
    def book_now(self, movie_id):
        """ Function for rendering booking page while clicking the button book now."""
        movie = request.env['movie.movie'].browse(movie_id)
        return http.request.render('show_booking_management.book_movie',
                                   {'movie': movie})

    @http.route('/movie/book_ticket', type='http', auth='public', website=True,
                methods=['POST'], csrf=False)
    def book_ticket(self, **kwargs):
        """ Function for submitting the form and rendering the seat selection chart."""
        movie_id = request.env['movie.movie'].browse(
            int(kwargs.get('movie_id')))
        screen_id = request.env['movie.screen'].browse(
            int(kwargs.get('screen')))
        time_slot_id = request.env['time.slots'].browse(
            int(kwargs.get('time_slots')))
        booked_seats = request.env['movie.seats'].search([
            ('screen_id', '=', screen_id.id),
            ('time_slot_id', '=', int(kwargs.get('time_slots'))),
            ('date', '=', kwargs.get('show_date')),
            ('is_booked', '=', True)
        ]).mapped('seat')

        return http.request.render(
            'show_booking_management.seat_selection_template',
            {'screen': screen_id, 'movie': movie_id,
             'time_slot_id': time_slot_id, 'booked_seats': booked_seats,
             'booked_seats_count': len(booked_seats),
             'available_seats_count': screen_id.total_seat_count - len(booked_seats),
             'booking_date': kwargs.get('show_date')})

    @http.route('/movie/confirm_booking', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def confirm_booking(self, **post):
        """ Function for confirming the seats selection and creating invoice."""
        selected_seats = request.httprequest.form.getlist('selected_seats')
        movie = request.env['movie.movie'].browse(int(post.get('movie_id')))
        product = request.env.ref('show_booking_management.product_1')
        invoice = request.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'invoice_origin': 'Movie',
            'partner_id': request.env.user.partner_id.id,
            'invoice_date': fields.Date.today(),
            'state': 'draft',
            'invoice_line_ids': [(0, 0, {
                'name': f"Ticket for {movie.name} on {post.get('booking_date')}",
                'product_id': product.id,
                'quantity': len(selected_seats),
                'price_unit': movie.price,
            })],
        })
        if invoice:
            invoice.sudo().action_post()
        access_token = invoice._portal_ensure_token()
        booking_data = {
            'invoice_id': invoice.id,
            'movie_id': int(post.get('movie_id')),
            'screen_id': int(post.get('screen_id')),
            'time_slot_id': int(post.get('time_slot_id')),
            'booking_date': post.get('booking_date'),
            'selected_seats': selected_seats,
        }
        request.session['movie_booking_data'] = json.dumps(booking_data)
        params = {
            'access_token': access_token,
            'payment_method_id': post.get('payment_method_id'),
        }
        return request.redirect(f'/my/invoices/{invoice.id}?{url_encode(params)}')
