# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import api, fields, models


class Venue(models.Model):
    """Model for managing the Venue that used to add new fields and
    functions to create the Venue"""
    _name = 'venue'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Venue'

    name = fields.Char(string="Name", help="Name of the venue type",
                       required=True)
    image = fields.Binary(string="Image", attachment=True,
                          related="venue_type_id.image",
                          help="This field holds the image used as "
                               "image for the event, limited to 1080x720px.")
    venue_type_id = fields.Many2one('venue.type',
                                    string='Venue Type', required=True,
                                    help='Used to choose the type of the '
                                         'particular venue')
    venue_location = fields.Char(string='Location', required=True,
                                 help='The venue location for Booking')
    capacity = fields.Integer(string='Capacity',
                              help='The capacity of the venue')
    seating = fields.Integer(string='Seating', help='The Seating of the venue')
    venue_charge_hour = fields.Float(string='Charge Per Hour',
                                     help='The charge per hour of the venue')
    venue_charge_day = fields.Float(string='Charge Per Day',
                                    help='The charge per day of the venue')
    additional_charge_hour = fields.Float(string=' Additional Charge Per Hour',
                                          help='The charge per hour of the '
                                               'venue')
    additional_charge_day = fields.Float(string='Additional Charge Per Day',
                                         help='The charge per day of the venue')
    venue_count = fields.Integer(string="# of Events",
                                 compute='_compute_venue_count',
                                 help='Compute field for calculate the '
                                      'venue count')
    open_time = fields.Float(string=' Open Time', help='Open time of the venue')
    closed_time = fields.Float(string=' Close Time',
                               help='Close time of the venue')
    venue_line_ids = fields.One2many('venue.lines',
                                     'venue_id', string='Amenities',
                                     help='Amenities for the venue')
    price_subtotal = fields.Float(string='Total',
                                  help='Total price of the venue',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True)

    @api.depends('venue_line_ids', 'venue_line_ids.sub_total')
    def _compute_price_subtotal(self):
        """Compute function for calculating the Amenities Price Subtotal"""
        self.price_subtotal = sum(
            item.sub_total for item in self.venue_line_ids)

    def _compute_venue_count(self):
        """Compute function for calculating the venue count"""
        for records in self:
            venues = self.env['venue.booking'].search([
                ('venue_id', '=', records.id)])
            records.venue_count = len(venues)

    def get_venue_type_action(self):
        """Get the venue type action for the venue bookings"""
        return self._get_action(
            'venue_booking_management.venue_booking_action_view_kanban')
