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


class CrmLead(models.Model):
    """Request sent from the AeroCourt website: court, session, membership
    or contact. Court requests also hold the slot, so that the calendar of
    the website knows which courts are taken."""
    _inherit = 'crm.lead'

    aerocourt_kind = fields.Selection(
        [('court', 'Court Booking'),
         ('session', 'Session Booking'),
         ('membership', 'Membership'),
         ('contact', 'Contact Message')],
        string='AeroCourt Request', index=True,
        help='Type of request made on the AeroCourt website.')
    aerocourt_reference = fields.Char(
        string='Booking Reference', index=True, copy=False,
        help='Reference shown to the visitor after the request.')
    aerocourt_date = fields.Date(
        string='Booking Date', index=True,
        help='Day of the court booking or of the session.')
    aerocourt_slot = fields.Char(
        string='Time Slot', index=True,
        help='Start time of the booked slot, for example 18:00.')
    aerocourt_court = fields.Char(
        string='Court', help='Number of the court assigned to the booking.')
    aerocourt_rental_count = fields.Integer(
        string='Rackets to Rent',
        help='Number of rental rackets requested with the booking.')
    aerocourt_total = fields.Float(
        string='Booking Total',
        help='Total price shown to the visitor when the request was made.')
