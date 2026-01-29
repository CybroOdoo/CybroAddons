# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
"""Website Booking Orders"""
from odoo import api, fields, models


class WebsiteBookings(models.Model):
    """Model for storing the bookings details from the website"""
    _name = 'website.bookings'
    _description = 'Website Bookings'

    booking = fields.Char(string='Booking Id', copy=False,
                          readonly=True, default='New',
                          help="Sequence for the booking orders")
    name = fields.Char(string='Name', help="Name of the reserved person")
    email = fields.Char(string='Email', help="Email of the reserved person")
    phone = fields.Char(string='Phone',
                        help="Contact number of the reserved person")
    date = fields.Date(string='Date', help="Reservation date")
    time = fields.Float(string="Time", help="Reservation time")
    persons = fields.Integer(string='Person',
                             help="Number of persons for the reservation")
    notes = fields.Text(string='Notes', help="Add the extra information")

    @api.model
    def create(self, vals):
        """Function for generating sequence for the records"""
        if vals.get('booking', 'New') == 'New':
            vals['booking'] = self.env['ir.sequence'].next_by_code(
                'website.bookings') or 'New'
        return super().create(vals)
