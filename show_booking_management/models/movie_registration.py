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
                              ('done', 'Done'),
                              ('invoiced', 'Invoiced')], string='Status',
                             default='draft', help='Status of the movie registration')

    def action_submit(self):
        """ Function for writing the state into done."""
        self.write({'state': 'done'})

    def action_invoice(self):
        """ Function for creating invoice."""
        product_id = self.env.ref('show_booking_management.product_1')
        try:
            move = self.env['account.move'].create([
                {
                    'move_type': 'out_invoice',
                    'partner_id': self.partner_id.id,
                    'movie_ticket_id': self.id,
                    'date': self.date,
                    'invoice_date': fields.Date.today(),
                    'invoice_line_ids': [
                        (0, 0,
                         {
                             'product_id': product_id.id,
                             'name': product_id.name,
                             'quantity': self.no_of_tickets,
                             'price_unit': self.movie_id.price,
                         })],
                }, ])
            self.write({'state': 'invoiced'})
            move.action_post()
            return {
                'name': 'Invoice',
                'res_id': move.id,
                'res_model': 'account.move',
                'view_id': False,
                'view_mode': 'form',
                'type': 'ir.actions.act_window',
            }
        except:
            raise ValidationError('Invoice Creation Failed!')

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
            ]).ids
            record.available_movie_ids = movies_list

    def check_seat_availability(self):
        """ Function for checking seat availability"""
        reserved_seats = sum(self.search([
            ('date', '=', self.date),
            ('time_slot_id', '=', self.time_slot_id.id),
            ('screen_id', '=', self.screen_id.id),
            ('state', '=', 'invoiced')
        ]).mapped('no_of_tickets')) + self.no_of_tickets
        if reserved_seats > self.screen_id.total_seat_count:
            raise ValidationError('Selected screen is already full')

    @api.model
    def create(self, vals):
        """Supering create function to check screen availability"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'movie.registration')
        res = super(MovieRegistration, self).create(vals)
        res.check_seat_availability()
        return res

    @api.constrains('no_of_tickets')
    def check_seat(self):
        """ Function for checking seat availability based on the number of tickets"""
        self.check_seat_availability()

    @api.onchange('movie_id')
    def set_values(self):
        """ Function for resetting time slot and screen while changing movie."""
        for record in self:
            record.update({'time_slot_id': None, 'screen_id': None})

    def action_generate_ticket_pdf(self):
        """ Function for downloading ticket pdf."""
        return self.env.ref(
            'show_booking_management.action_report_movie_ticket').report_action(self)

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
        return {'Status': 'Success'}

    def action_open_invoices(self):
        """ Function for viewing created invoices"""
        return {
            'name': 'Invoice',
            'domain': [('movie_ticket_id', '=', self.id)],
            'res_model': 'account.move',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }
