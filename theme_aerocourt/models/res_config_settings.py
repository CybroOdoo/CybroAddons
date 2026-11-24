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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Settings of the AeroCourt booking pages."""
    _inherit = 'res.config.settings'

    aerocourt_open_hour = fields.Integer(
        string='Opening Hour', related='website_id.aerocourt_open_hour',
        readonly=False, help='First bookable hour of the day, from 0 to 23.')
    aerocourt_close_hour = fields.Integer(
        string='Closing Hour', related='website_id.aerocourt_close_hour',
        readonly=False, help='Hour at which the club closes, from 1 to 24.')
    aerocourt_court_count = fields.Integer(
        string='Courts', related='website_id.aerocourt_court_count',
        readonly=False, help='Number of identical courts that can be booked.')
    aerocourt_court_rate = fields.Float(
        string='Court Price per Hour',
        related='website_id.aerocourt_court_rate', readonly=False,
        help='Price of one hour on a court.')
    aerocourt_rental_fee = fields.Float(
        string='Racket Rental Fee', related='website_id.aerocourt_rental_fee',
        readonly=False, help='Price to rent one racket for a booking.')
    aerocourt_booking_days = fields.Integer(
        string='Booking Window', related='website_id.aerocourt_booking_days',
        readonly=False,
        help='Number of days ahead that a court can be booked.')
