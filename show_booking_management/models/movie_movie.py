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
from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MovieMovie(models.Model):
    """
        Model for managing movie details including name, duration,
        release date, show type, language, poster, time slots, cast,
        screens, price, overview, currency, and status.
    """
    _name = 'movie.movie'
    _description = 'Movie'

    name = fields.Char(help='Name of the Movie')
    duration = fields.Float(string='Duration of the movie',
                            help='Duration of the Movie')
    release_date = fields.Date(help='Release date of the Movie')
    show_type_ids = fields.Many2many('show.type',
                                     help='Show type of the movie')
    movie_language_id = fields.Many2one('res.lang',
                                        help='Language of the movie')
    movie_poster = fields.Binary(help='Poster of the Movie')
    available_time_slots_ids = fields.Many2many('time.slots',
                                                string='Time Slots',
                                                help='Time slots of the movie')
    movie_cast_ids = fields.Many2many('movie.cast',
                                      help='Mention the movie casts')
    available_screens_ids = fields.Many2many('movie.screen',
                                             string='Screens',
                                             help='Mention the screens')
    show_start_date = fields.Date(help='Mention the show start date')
    show_end_date = fields.Date(help='Mention the show end date')
    booking_start_date = fields.Date(string='Pre-booking Start Date',
                                     help='Mention the booking start date')
    booking_end_date = fields.Date(string='Pre-booking End Date',
                                   help='Mention the booking end date')
    prebooking_slot = fields.Integer(string='Pre-booking Slot',
                                     help='Maximum seats that can be pre-booked per show.')
    price = fields.Monetary(currency_field='currency_id', help='Mention the ticket price')
    about_movie = fields.Text(help='Overview of the movie.')
    currency_id = fields.Many2one('res.currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    state = fields.Selection([('draft', 'Draft'),
                              ('prebooking', 'Pre-booking'),
                              ('ongoing', 'Ongoing'),
                              ('cancel', 'Cancelled')],
                             string='Status', default='draft',
                             help='Status of the show')
    is_prebooking_closed = fields.Boolean(string='Is Pre-booking Closed',
                                          compute='_compute_is_prebooking_closed',
                                          help='Technical field to check if pre-booking is full')

    @api.depends('state', 'prebooking_slot', 'show_start_date', 'show_end_date',
                 'available_time_slots_ids', 'available_screens_ids')
    def _compute_is_prebooking_closed(self):
        """ Compute if pre-booking is closed: every show (date, time slot,
        screen) from today to the show end date has reached the pre-booking
        slot limit. """
        today = fields.Date.context_today(self)
        movies = self.filtered(lambda m: m.state == 'prebooking' and m.prebooking_slot > 0)
        (self - movies).is_prebooking_closed = False
        if not movies:
            return
        # Booked tickets per show, for all the movies in a single query
        show_bookings = {}
        for movie, show_date, time_slot, screen, tickets in self.env['movie.registration']._read_group(
                [('movie_id', 'in', movies.ids), ('state', '=', 'invoiced'), ('date', '>=', today)],
                ['movie_id', 'date:day', 'time_slot_id', 'screen_id'], ['no_of_tickets:sum']):
            show_bookings[movie.id, show_date, time_slot.id, screen.id] = tickets
        for record in movies:
            start_date = max(today, record.show_start_date or today)
            end_date = record.show_end_date
            if not end_date or start_date > end_date:
                record.is_prebooking_closed = True
                continue
            record.is_prebooking_closed = not any(
                show_bookings.get((record.id, start_date + timedelta(days=day), slot.id, screen.id), 0)
                < record.prebooking_slot
                for day in range((end_date - start_date).days + 1)
                for slot in record.available_time_slots_ids
                for screen in record.available_screens_ids
            )

    @api.constrains('show_start_date', 'show_end_date', 'release_date')
    def _check_show_start_date(self):
        """ Function for validating show start date and end date """
        for record in self:
            if (record.show_start_date and record.release_date and
                    record.show_start_date < record.release_date):
                raise ValidationError(
                    self.env._('The show start date must be on or after the release date.'))
            if (record.show_start_date and record.show_end_date and
                    record.show_start_date > record.show_end_date):
                raise ValidationError(
                    self.env._('The show end date must be on or after the show start date.'))

    @api.constrains('booking_start_date', 'booking_end_date', 'show_start_date')
    def _check_booking_dates(self):
        """ Function for validating booking start and end dates """
        for record in self:
            if (record.booking_start_date and record.show_start_date and
                    record.booking_start_date > record.show_start_date):
                raise ValidationError(
                    self.env._('The pre-booking start date must be on or before the show start date.'))
            if (record.booking_start_date and record.booking_end_date and
                    record.booking_start_date > record.booking_end_date):
                raise ValidationError(
                    self.env._('The pre-booking end date must be on or after the pre-booking start date.'))

    @api.constrains('available_screens_ids', 'show_start_date', 'show_end_date')
    def _check_screen_availability(self):
        """ Function for checking the screen availability if the
        screen is already booked for another movie it raises error"""
        for record in self:
            if record.show_start_date and record.show_end_date:
                overlapping_movies = self.env['movie.movie'].search([
                    ('id', '!=', record.id),
                    ('available_screens_ids', 'in',
                     record.available_screens_ids.ids),
                    ('show_start_date', '<=', record.show_end_date),
                    ('show_end_date', '>=', record.show_start_date),
                ])
                if overlapping_movies:
                    raise ValidationError(self.env._(
                        'One or more of the selected screens are already booked '
                        'for another movie during this period.'))

    @api.model_create_multi
    def create(self, vals_list):
        """Supering create function to check screen availability"""
        res = super().create(vals_list)
        res._check_screen_availability()
        return res

    def write(self, vals):
        """Supering write function to check screen availability"""
        res = super().write(vals)
        self._check_screen_availability()
        return res

    @api.model
    def check_shows_on_date(self, date, selected_movie):
        """ Function for searching the movies based on the date from js."""
        movie = self.search([('id', '=', selected_movie),
                             ('show_start_date', '<=', date),
                             ('show_end_date', '>=', date)])
        return bool(movie)

    def action_prebooking(self):
        """ Function for changing the state into prebooking."""
        self.state = 'prebooking'

    def action_start_show(self):
        """ Function for changing the state into ongoing."""
        today = fields.Date.context_today(self)
        if any(not rec.show_start_date or today < rec.show_start_date for rec in self):
            raise ValidationError(self.env._('A show can only be started from its show start date.'))
        self.state = 'ongoing'

    def action_cancel_show(self):
        """ Function for changing the state into cancel."""
        self.write({'state': 'cancel'})

    @api.model
    def _cron_auto_start_shows(self):
        """ Scheduled action to automatically transition movies to ongoing or cancelled state """
        today = fields.Date.context_today(self)
        # 1. Start shows that reached their start date
        self.search([
            ('state', '=', 'prebooking'),
            ('show_start_date', '<=', today),
        ]).action_start_show()
        # 2. Cancel shows that passed their end date
        self.search([
            ('state', 'in', ['prebooking', 'ongoing']),
            ('show_end_date', '<', today),
        ]).action_cancel_show()

    @api.model
    def update_seats(self, screen_id, time_slot_id, booking_date):
        """
            Update the seats availability based on the screen, time slot, and booking date.
        """
        booked_seats = self.env['movie.seats'].search([
            ('screen_id', '=', int(screen_id)),
            ('time_slot_id', '=', int(time_slot_id)),
            ('date', '=', booking_date),
            ('is_booked', '=', True)
        ]).mapped('seat')
        time_slot = self.env['time.slots'].browse(int(time_slot_id)).name
        screen = self.env['movie.screen'].browse(int(screen_id))
        return {'booked_seats': booked_seats,
                'time_slot': time_slot,
                'booked_seats_count': len(booked_seats),
                'available_seats_count': screen.total_seat_count - len(booked_seats)}
