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
from odoo import fields, models


class MovieSeats(models.Model):
    """
        Movie Seats model for managing seat bookings.
    """
    _name = 'movie.seats'
    _description = 'Movie Seats'

    screen_id = fields.Many2one('movie.screen', 'Screen',
                                required=True, help='Mention the screen id')
    time_slot_id = fields.Many2one('time.slots', 'Time Slot',
                                   required=True, help='Mention the time slot id')
    movie_registration_id = fields.Many2one('movie.registration',
                                            'Booking ID', required=True,
                                            help='Mention the movie registration id')
    date = fields.Date(string='Date', help='Mention the date', required=True)
    seat = fields.Char(string='Seat', required=True, help='Mention the seats')
    is_booked = fields.Boolean('Is booked', help='Check if is booked true')
