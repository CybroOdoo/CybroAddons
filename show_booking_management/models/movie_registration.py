# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import base64
import qrcode
from io import BytesIO


class MovieRegistration(models.Model):
    """
        Model for managing movie registrations including details like partner,
        movie, date, time slot, screen, tickets, etc.
    """
    _name = 'movie.registration'
    _description = 'Movie Registration'

    name = fields.Char(required=True, copy=False,
                       default='New', readonly=True,
                       help='Name of the Movie Ticket')
    partner_id = fields.Many2one('res.partner', string='Select Partner',
                                 help='Mention the partner')
    movie_id = fields.Many2one('movie.movie', string='Select Movie',
                               domain="[('id', 'in', available_movie_ids)]",
                               required=True, help='Mention the movie id')
    movie_type = fields.Many2many('show.type', related='movie_id.show_type_ids',
                                  help='Show type of the movie')
    movie_lang = fields.Many2one('res.lang', string='Movie Langauge',
                                 related='movie_id.movie_language_id',
                                 help='Language of the movie')
    date = fields.Date(string='Date', default=fields.Date.today(),
                       required=True, help='Mention the date for booking.')
    time_slot_id = fields.Many2one('time.slots',
                                   string='Select time slot',
                                   domain="[('id', 'in', available_time_slot_ids)]",
                                   required=True, help='Mention the time slots of the movie')
    screen_id = fields.Many2one('movie.screen', string='Select Screen',
                                domain="[('id', 'in', available_screens_ids)]",
                                required=True, help='Mention the screen of the movie')
    available_movie_ids = fields.Many2many('movie.movie',
                                           string='Available movies',
                                           help='Mention the available movies')
    available_time_slot_ids = fields.Many2many('time.slots',
                                               string='Available time slots',
                                               compute='_compute_available_time_slot_ids',
                                               help='Mention the available time slots')
    available_screens_ids = fields.Many2many('movie.screen',
                                             string='Available screens',
                                             compute='_compute_available_time_slot_ids',
                                             help='Mention the available screen')
    movie_price = fields.Monetary(string='Movie Price',
                                  related='movie_id.price',
                                  help='Price of the movie ticket')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  help="Currency",
                                  required=True,
                                  default=lambda
                                      self: self.env.user.company_id.currency_id)
    no_of_tickets = fields.Integer(string='Number of tickets', default=1,
                                   help='Mention the number of tickets')
    movie_poster = fields.Binary(related='movie_id.movie_poster',
                                 string='Movie poster',
                                 help='Poster of the movie.')
    movie_cast_ids = fields.Many2many(related='movie_id.movie_cast_ids',
                                      string='Movie Cast', readonly=True,
                                      help='Movie casts')
    seat_ids = fields.One2many('movie.seats', 'movie_registration_id',
                               string="Seats", help='Mention the seat ids')
    qr_code = fields.Binary(string='Qr Code', help='Qr code containing ticket details')
    state = fields.Selection([('draft', 'Draft'),
                              ('invoiced', 'Invoiced')], string='Status',
                             default='draft', help='Status of the movie registration')

    def action_select_seats(self):
        """ Function for redirecting to seat selection page on website."""
        self.ensure_one()
        if not self.movie_id or not self.date or not self.time_slot_id or not self.screen_id:
            raise ValidationError('Please select Movie, Date, Time Slot, and Screen first.')

        url = '/movie/book_ticket?movie_id=%s&screen=%s&time_slots=%s&show_date=%s&registration_id=%s' % (
            self.movie_id.id, self.screen_id.id, self.time_slot_id.id, self.date, self.id
        )
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    @api.depends('movie_id')
    def _compute_available_time_slot_ids(self):
        """ Function for computing time slots and screens."""
        for record in self:
            record.available_time_slot_ids = record.movie_id.available_time_slots_ids.ids
            record.available_screens_ids = record.movie_id.available_screens_ids.ids

    @api.onchange('date')
    def fetch_movies(self):
        """ Function for validating date and fetching movies based on the date."""
        for record in self:
            if record.date < fields.Date.today():
                raise ValidationError('The date must be greater than or equal to today\'s date.')
            record.movie_id = None
            record.available_movie_ids = None
            movies_list = self.env['movie.movie'].search([
                ('show_start_date', '<=', record.date),
                ('show_end_date', '>=', record.date),
                ('state', 'in', ['prebooking', 'ongoing'])
            ]).ids
            record.available_movie_ids = movies_list

    def check_seat_availability(self):
        """ Function for checking seat availability"""
        reserved_seats = sum(self.search([
            ('id', '!=', self.id),
            ('date', '=', self.date),
            ('time_slot_id', '=', self.time_slot_id.id),
            ('screen_id', '=', self.screen_id.id),
            ('state', '=', 'invoiced')
        ]).mapped('no_of_tickets')) + self.no_of_tickets
        if reserved_seats > self.screen_id.total_seat_count:
            raise ValidationError('Selected screen is already full')

        if self.movie_id.state == 'prebooking' and self.movie_id.prebooking_slot > 0:
            if reserved_seats > self.movie_id.prebooking_slot:
                raise ValidationError(
                    f'Pre-booking limit reached! Only {self.movie_id.prebooking_slot} seats are allowed for pre-booking.')

    @api.model_create_multi
    def create(self, vals_list):
        """Supering create function to check screen availability"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'movie.registration')
        res = super().create(vals_list)
        for record in res:
            record.check_seat_availability()
        return res

    @api.constrains('no_of_tickets', 'seat_ids')
    def check_seat(self):
        """ Function for checking seat availability based on the number of tickets"""
        for record in self:
            if record.no_of_tickets <= 0:
                raise ValidationError('Number of tickets must be at least 1.')
            if record.seat_ids and len(record.seat_ids) != record.no_of_tickets:
                raise ValidationError(f'The number of selected seats ({len(record.seat_ids)}) '
                                      f'does not match the number of tickets ({record.no_of_tickets}).')
            record.check_seat_availability()

    @api.onchange('movie_id')
    def set_values(self):
        """ Function for resetting time slot and screen while changing movie."""
        for record in self:
            record.update({'time_slot_id': None, 'screen_id': None})

    def action_generate_ticket_pdf(self):
        """ Function for downloading ticket pdf."""
        return self.env.ref(
            'show_booking_management.action_report_movie_ticket').report_action(self)

    def get_qr_code_image(self):
        """ Function for generating QR code image for the report """
        qr_data = f"Ticket : {self.name}\n" \
                  f"Movie: {self.movie_id.name}\n" \
                  f"Date: {self.date}\n" \
                  f"Time: {self.time_slot_id.name}\n" \
                  f"Screen: {self.screen_id.name}\n" \
                  f"Seats: {', '.join(self.seat_ids.mapped('seat'))}"
        qr = qrcode.QRCode(version=None,
                           error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image()
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue())

    @api.model
    def check_seat_available(self, date, time_slot_id, screen_id, ticket_count):
        """ Function for updating the status of the seats availability based
         on the movie time slot and screen selected"""
        screen = self.env['movie.screen'].browse(int(screen_id))
        reserved_seats = sum(self.search([
            ('date', '=', date),
            ('time_slot_id', '=', int(time_slot_id)),
            ('screen_id', '=', int(screen_id)),
            ('state', '=', 'invoiced')
        ]).mapped('no_of_tickets'))
        if reserved_seats + int(ticket_count) > screen.total_seat_count:
            return {
                'Status': 'Failed',
                'Error': f"The selected screen has only "
                         f"{screen.total_seat_count - reserved_seats} seats left!"
            }

        movie = self.env['movie.movie'].search([
            ('available_screens_ids', 'in', screen.id),
            ('available_time_slots_ids', 'in', int(time_slot_id)),
            ('show_start_date', '<=', date),
            ('show_end_date', '>=', date)
        ], limit=1)


        if movie and movie.state == 'prebooking' and movie.prebooking_slot > 0:
            if reserved_seats + int(ticket_count) > movie.prebooking_slot:
                return {
                    'Status': 'Failed',
                    'Error': f"Only {movie.prebooking_slot} seats are allowed for pre-booking. "
                             f"{reserved_seats} are already booked."
                }

        return {'Status': 'Success'}

    def action_open_invoices(self):
        """ Function for viewing created invoices"""
        return {
            'name': 'Invoice',
            'domain': [('movie_ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }
