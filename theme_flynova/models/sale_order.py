# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime
from odoo import fields, models


class SaleOrder(models.Model):
    """Extend sale orders with travel booking information."""

    _inherit = 'sale.order'

    booking_date = fields.Date(
        string='Check-In Date',
        help='Customer\'s check-in or travel start date from the booking form.')
    booking_date_end = fields.Date(
        string='Check-Out Date',
        help='Customer\'s check-out or travel end date; defaults to check-in date if empty.')
    adult_qty = fields.Integer(
        string='Adults', default=1,
        help='Number of adult guests (18+) included in this booking.')
    child_qty = fields.Integer(
        string='Children', default=0,
        help='Number of child guests (under 18) included in this booking.')
    is_booking_order = fields.Boolean(
        string='Is Booking Order', default=False,
        help='When enabled, confirming this order auto-creates a linked travel event.')
    booking_product_id = fields.Many2one(
        'product.template', string='Booking Product',
        help='The tour or hotel product booked through the Flynova website.')

    def _action_confirm(self):
        """Extend order confirmation to auto-create a booking event.

        Calls the parent confirmation logic and then, for each confirmed order
        that is flagged as a booking order with a booking product, triggers
        the creation of a linked event with tickets and registrations.

        Returns:
            bool: The result returned by the parent _action_confirm method.
        """
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            if order.is_booking_order and order.booking_product_id:
                order._create_booking_event()
        return res

    def _create_booking_event(self):
        """Create an event, ticket, and attendee registrations from this booking order.

        Derives the event date range from the booking dates, calculates a
        per-person ticket price from the order total, copies the product image
        to the event, and registers all guests (adults + children) with the
        primary partner's contact details assigned to the first attendee.

        This method is called automatically by _action_confirm for confirmed
        booking orders and should not be called directly.

        Raises:
            ValueError: If called on a recordset with more than one record
                (ensured via ensure_one).
        """
        self.ensure_one()
        Event = self.env['event.event'].sudo()
        Ticket = self.env['event.event.ticket'].sudo()
        Registration = self.env['event.registration'].sudo()

        date_begin = datetime.combine(self.booking_date, datetime.min.time())
        if self.booking_date_end:
            date_end = datetime.combine(self.booking_date_end, datetime.max.time())
        else:
            date_end = datetime.combine(self.booking_date, datetime.max.time())

        # Compute the real total from the sale order's calculated amount.
        total_price = self.amount_total
        guest_count = max(self.adult_qty + self.child_qty, 1)
        ticket_price = total_price / guest_count

        # Create an event with the image copied from the booking product.
        event = Event.create({
            'name': f"{self.booking_product_id.name} ({self.booking_date})",
            'date_begin': date_begin,
            'date_end': date_end,
            'is_published': True,
            'location_name': self.booking_product_id.location_name or self.booking_product_id.name,
            'duration': self.booking_product_id.duration,
            'image_1920': self.booking_product_id.image_1920,
        })

        # Create a ticket with the per-person price.
        product_variant = self.booking_product_id.product_variant_id
        ticket = Ticket.create({
            'name': 'Standard Booking',
            'event_id': event.id,
            'product_id': product_variant.id,
            'price': ticket_price,
            'seats_max': guest_count,
        })

        registrations_data = []
        attendee_name = self.partner_id.name or 'Guest'
        for index in range(guest_count):
            registrations_data.append({
                'event_id': event.id,
                'name': attendee_name if index == 0 else f"{attendee_name} Guest {index + 1}",
                'email': self.partner_id.email if index == 0 else False,
                'phone': self.partner_id.phone if index == 0 else False,
                'event_ticket_id': ticket.id,
                'sale_order_id': self.id,
            })
        Registration.create(registrations_data)
