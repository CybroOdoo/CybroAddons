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
from odoo import fields, models
from datetime import datetime

class SaleOrder(models.Model):
    """Sale Order"""
    _inherit = 'sale.order'

    booking_date = fields.Date(string="Booking Date",
                               help="The check-in or start date of the booking, set from the customer's selection on the website.")
    booking_date_end = fields.Date(string="Booking Date End",
                                   help="The check-out or end date of the booking. If not set, the booking is treated as a single-day event.")
    adult_qty = fields.Integer(string="Adults", default=1,
                               help="Number of adult guests (18+) included in this booking.")
    child_qty = fields.Integer(string="Children", default=0,
                               help="Number of child guests (under 18) included in this booking. Priced at 50% of the adult rate.")
    is_booking_order = fields.Boolean(string="Is Booking Order", default=False,
                                      help="When enabled, this sale order represents a Flynova tour/hotel booking and will generate an event upon confirmation.")
    booking_product_id = fields.Many2one(comodel_name='product.template', string="Booking Product",
                                         help="The tour or hotel product associated with this booking order.")

    def _action_confirm(self):
        """
        Extend the sale order confirmation to trigger booking event creation.

        Calls the standard ``_action_confirm`` logic, then iterates over all
        confirmed orders in the recordset. For each order flagged as a booking
        order (``is_booking_order=True``) with a linked product, a corresponding
        ``event.event`` record is created via :meth:`_create_booking_event`.

        Returns:
            Any: The return value of the parent ``_action_confirm`` call
            (typically ``True`` for standard Odoo sale orders).
        """
        res = super(SaleOrder, self)._action_confirm()
        for order in self:
            if order.is_booking_order and order.booking_product_id:
                order._create_booking_event()
        return res

    def _create_booking_event(self):
        """
        Create an event, ticket, and registrations from this booking sale order.

        Derives the event date range from ``booking_date`` and
        ``booking_date_end``, computes a per-person ticket price by dividing
        the order's ``amount_total`` by the total guest count, and then:

        1. Creates an ``event.event`` record with the product's image, name,
           location, and duration.
        2. Creates a single ``event.event.ticket`` ("Standard Booking") linked
           to the product variant with the computed per-person price.
        3. Creates one ``event.registration`` per guest, using the order
           partner's name and contact details for the first attendee and
           auto-generated names ("Guest N") for the remaining ones.

        This method must be called on a singleton record (``ensure_one()`` is
        enforced). It is intended to be invoked from :meth:`_action_confirm`
        and should not be called directly on unconfirmed orders.

        Raises:
            odoo.exceptions.ValueError: If called on a multi-record recordset.
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

        # ── Compute real total using the Sale Order's calculated amount_total ──
        total_price = self.amount_total
        guest_count = max(self.adult_qty + self.child_qty, 1)
        ticket_price = total_price / guest_count

        # ── Create Event with image copied from the booking product ──
        event = Event.create({
            'name': f"{self.booking_product_id.name} ({self.booking_date})",
            'date_begin': date_begin,
            'date_end': date_end,
            'is_published': True,
            'location_name': self.booking_product_id.location_name or self.booking_product_id.name,
            'duration': self.booking_product_id.duration,
            'image_1920': self.booking_product_id.image_1920,
        })

        # ── Create Ticket with the 'per person' price ──
        product_variant = self.booking_product_id.product_variant_id
        ticket = Ticket.create({
            'name': 'Standard Booking',
            'event_id': event.id,
            'product_id': product_variant.id,
            'price': ticket_price,
            'seats_max': guest_count,
        })

        # ── Create Registrations ──
        registrations_data = []
        attendee_name = self.partner_id.name or "Guest"
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
