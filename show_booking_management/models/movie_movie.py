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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class MovieMovie(models.Model):
    """
        Model for managing movie details including name, duration,
        release date, show type, language, poster, time slots, cast,
        screens, price, overview, currency, and status.
    """
    _name = 'movie.movie'
    _description = 'Movie Movie'

    name = fields.Char(string='Name', help='Name of the Movie')
    duration = fields.Float(string='Duration of the movie',
                            help='Duration of the Movie')
    release_date = fields.Date(string='Release Date',
                               help='Release date of the Movie')
    show_type_ids = fields.Many2many('show.type',
                                     string='Show Type',
                                     help='Show type of the movie')
    movie_language_id = fields.Many2one('res.lang',
                                        string='Movie Language',
                                        help='Language of the movie')
    movie_poster = fields.Binary(string='Movie Poster', help='Poster of the Movie')
    available_time_slots_ids = fields.Many2many('time.slots',
                                                string='Time Slots',
                                                help='Time slots of the movie')
    movie_cast_ids = fields.Many2many('movie.cast',
                                      string='Movie Cast',
                                      help='Mention the movie casts')
    available_screens_ids = fields.Many2many('movie.screen',
                                             string='Screens',
                                             help='Mention the screens')
    show_start_date = fields.Date(string='Show Start Date',
                                  help='Mention the show start date')
    show_end_date = fields.Date(string='Show End Date',
                                help='Mention the show end date')
    price = fields.Monetary(currency_field='currency_id', string='Price',
                            help='Mention the ticket price')
    about_movie = fields.Text(string='About Movie', help='Overview of the movie.')
    currency_id = fields.Many2one('res.currency',
                                  string='Currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    state = fields.Selection([('draft', 'Draft'),
                              ('ongoing', 'Ongoing'),
                              ('cancel', 'Cancelled')],
                             string='Status', default='draft',
                             help='')

    @api.constrains('show_start_date', 'show_end_date', 'release_date')
    def _check_show_start_date(self):
        """ Function for validating show start date and end date """
        for record in self:
            if (record.show_start_date and record.release_date and
                    record.show_start_date < record.release_date):
                raise ValidationError(
                    'Show Start date must be on or after the Release Date')
            if (record.show_end_date and record.show_end_date and
                    record.show_start_date > record.show_end_date):
                raise ValidationError(
                    'Show End date must be on or after the Show Start date')

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
                    raise ValidationError(
                        'One or more of the selected screens are already booked '
                        'for another movie during this period.')

    @api.model
    def create(self, vals):
        """Supering create function to check screen availability"""
        res = super(MovieMovie, self).create(vals)
        res._check_screen_availability()
        return res

    @api.model
    def write(self, vals):
        """Supering create function to check screen availability"""
        res = super(MovieMovie, self).write(vals)
        self._check_screen_availability()
        return res

    @api.model
    def check_shows_on_date(self, date, selected_movie):
        """ Function for searching the movies based on the date from js."""
        movie = self.search([('id', '=', selected_movie),
                             ('show_start_date', '<=', date),
                             ('show_end_date', '>=', date)])
        return bool(movie)

    def action_start_show(self):
        """ Function for changing the state into ongoing."""
        for rec in self:
            if fields.Date.today() >= rec.show_start_date:
                self.write({'state': 'ongoing'})
            else:
                raise ValidationError(
                    'Show Starts only based on the Show Start Date')

    def action_cancel_show(self):
        """ Function for changing the state into cancel."""
        self.write({'state': 'cancel'})

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
