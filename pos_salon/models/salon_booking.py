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
import json
import logging
import secrets
from odoo import api, fields, models
from odoo.exceptions import ValidationError, UserError
_logger = logging.getLogger(__name__)


class SalonBooking(models.Model):
    """Store customer, service, schedule, and status details for a booking."""

    _name = "salon.booking"
    _description = "Salon Booking"
    _rec_name = "customer_name"

    customer_name = fields.Char(
        required=True,
        help='Enter the name of the customer making the booking.',
    )
    customer_phone = fields.Char(
        required=True,
        help='Enter the phone number of the customer making the booking.',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer record (res.partner) the booking belongs to.',
    )
    customer_email = fields.Char(
        help="Customer's email address.",
    )
    service_lines = fields.Text(
        help='JSON list of {name, price} used to build the POS order lines.',
    )
    pos_order_id = fields.Many2one(
        'pos.order',
        string='POS Order',
        readonly=True,
        copy=False,
        help='POS order that paid this booking.',
    )
    date = fields.Date(
        string='Booking Date',
        required=True,
        help='Select the date scheduled for the booking.',
    )
    slot = fields.Char(
        string='Time Slot',
        help='Store the selected appointment time slot.',
    )
    service_name = fields.Char(
        string='Service',
        help='Store the services selected for the booking.',
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'),
         ('done', 'Completed'), ('cancelled', 'Cancelled'), ('rescheduled', 'Rescheduled')],
        string='Status',
        default='draft',
        help='Select the current status of the salon booking.',
    )
    payment_state = fields.Selection(
        [('unpaid', 'Unpaid'), ('partial', 'Partially Paid'), ('paid', 'Paid')],
        string='Payment Status',
        default='unpaid',
        copy=False,
        index=True,
        help='Payment status. It is separate from the service status.',
    )
    amount_payable = fields.Float(
        string='Amount',
        compute='_compute_amounts',
        help='Services plus amenities, the full amount of the booking.',
    )
    amount_due = fields.Float(
        compute='_compute_amounts',
        help='Amount still to be paid. It is 0 once the booking is paid.',
    )
    specialist_id = fields.Many2one(
        'res.partner',
        help='Specialist assigned to perform the booked services.',
    )
    amenity_ids = fields.Many2many(
        'product.product',
        string='Amenities',
        help='Amenities selected for this booking.',
    )
    specialist_name = fields.Char(
        related='specialist_id.name',
    )
    amenity_names = fields.Char(
        compute='_compute_amenity_names',
    )
    config_id = fields.Many2one(
        'pos.config',
        string='Point of Sale',
        help='Point of sale where the booking was created.',
    )
    amount_total = fields.Float(
        string='Total Amount',
        help='Total price of the booked services.',
    )
    commission_amount = fields.Float(
        help='Commission earned by the specialist for this booking.',
    )
    rescheduled_from_id = fields.Many2one(
        'salon.booking',
        readonly=True,
        copy=False,
        help='Earlier booking whose service was moved into this booking.',
    )
    checked_in = fields.Boolean(
        string='Arrived',
        copy=False,
        help='The customer has arrived and is using the seat. Walk-ins are arrived at creation.',
    )
    checked_in_time = fields.Datetime(string='Arrival Time', copy=False)
    seat_no = fields.Integer(
        string='Seat',
        copy=False,
        help='Seat number the booking uses. 0 means not assigned.',
    )
    walkin_start = fields.Integer(
        string='Walk-in Start (minutes)',
        copy=False,
        help='Slot-rounded start of a walk-in, in minutes from midnight (10:00 AM = 600).',
    )
    time_period = fields.Char(
        compute='_compute_time_period',
        help='Start and end time, e.g. 10:00 AM - 12:30 PM. Works for walk-ins and bookings.',
    )
    review_token = fields.Char(copy=False, index=True, readonly=True,
                               groups='point_of_sale.group_pos_manager')
    review_url = fields.Char(compute='_compute_review_url',
                             groups='point_of_sale.group_pos_manager')
    review_mail_sent = fields.Boolean(copy=False, readonly=True)
    rating = fields.Integer(copy=False, readonly=True, aggregator='avg')
    rating_stars = fields.Char(string='Review', compute='_compute_rating_stars')
    review_note = fields.Text(string='Review Comment', copy=False, readonly=True)
    review_date = fields.Datetime(string='Reviewed On', copy=False, readonly=True)
    commission_enabled = fields.Boolean(related='config_id.apply_commission',
                                        string='Commission Enabled')

    @api.constrains('rating')
    def _check_rating(self):
        for booking in self:
            if not 0 <= booking.rating <= 5:
                raise ValidationError(self.env._("Rating must be between 0 and 5."))

    @api.depends('review_token')
    def _compute_review_url(self):
        for booking in self:
            booking.review_url = (
                '%s/salon/review/%s' % (booking.get_base_url(), booking.review_token)
                if booking.review_token else False)

    @api.depends('rating')
    def _compute_rating_stars(self):
        for booking in self:
            booking.rating_stars = (
                    '★' * booking.rating + '☆' * (5 - booking.rating)) if booking.rating else ''

    def _send_review_mail(self):
        """Queue the review mail. It never raises, so Complete is never blocked."""
        template = self.env.ref('pos_salon.mail_template_salon_review',
                                raise_if_not_found=False)
        if not template:
            return
        template = template.sudo()
        queued = False
        for booking in self.sudo():
            if (booking.state != 'done' or not booking.config_id.take_review
                    or not booking.customer_email or booking.review_date):
                continue
            try:
                with self.env.cr.savepoint():
                    if not booking.review_token:
                        booking.review_token = secrets.token_urlsafe(24)
                    template.send_mail(booking.id, force_send=False)
                    booking.review_mail_sent = True
                    queued = True
            except Exception:
                _logger.exception("Review mail failed for booking %s", booking.id)
        if queued:  # run the mail queue now instead of waiting for the cron
            self.env.ref('mail.ir_cron_mail_scheduler_action').sudo()._trigger()

    def action_send_review_mail(self):
        """Resend button on the backend form."""
        for booking in self:
            if booking.state != 'done':
                raise UserError(self.env._("Only completed bookings can be reviewed."))
            if not booking.customer_email:
                raise UserError(self.env._("This customer has no email address."))
            if booking.review_date:
                raise UserError(self.env._("This booking is already reviewed."))
        self._send_review_mail()

    @api.depends('amount_total', 'amenity_ids', 'payment_state')
    def _compute_amounts(self):
        for booking in self:
            total = (booking.amount_total or 0.0) + sum(booking.amenity_ids.mapped('lst_price'))
            booking.amount_payable = total
            booking.amount_due = 0.0 if booking.payment_state == 'paid' else total

    @api.depends('amenity_ids')
    def _compute_amenity_names(self):
        for booking in self:
            booking.amenity_names = ', '.join(booking.amenity_ids.mapped('name'))

    @api.depends('slot', 'walkin_start', 'service_lines', 'create_date')
    def _compute_time_period(self):
        slot = self.SLOT_MINUTES
        for booking in self:
            period = ''
            if (booking.slot or '').strip() == 'Walk-in':
                start = booking.walkin_start
                if not start and booking.create_date:  # walk-ins from before walkin_start
                    local = fields.Datetime.context_timestamp(booking, booking.create_date)
                    start = ((local.hour * 60 + local.minute) // slot) * slot
                duration = sum(self._line_duration(line) for line in booking._get_lines()) or slot
                period = '%s - %s' % (self._minutes_to_label(start),
                                      self._minutes_to_label(start + duration))
            else:
                buckets = sorted(self._slot_buckets(booking.slot))
                if buckets:
                    period = '%s - %s' % (self._minutes_to_label(buckets[0]),
                                          self._minutes_to_label(buckets[-1] + slot))
            booking.time_period = period

    @api.model_create_multi
    def create(self, vals_list):
        """Require a customer record and keep name/phone/email in sync with it."""
        for vals in vals_list:
            partner = self.env['res.partner'].browse(vals.get('partner_id')).exists()
            if not partner:
                raise UserError(self.env._("Please select a customer."))
            phone = (vals.get('customer_phone') or partner.phone or '').strip()
            if not phone:
                raise UserError(self.env._("Please fill in the customer's phone number."))
            if not partner.phone:
                partner.sudo().write({'phone': phone})
            vals['customer_phone'] = phone
            vals['customer_name'] = vals.get('customer_name') or partner.name
            vals['customer_email'] = vals.get('customer_email') or partner.email
        return super().create(vals_list)

    def _ensure_partner(self):
        """Old bookings only have a name/phone: link (or create) a partner."""
        self.ensure_one()
        if not self.partner_id:
            Partner = self.env['res.partner'].sudo()
            partner = Partner.search([
                ('name', '=', self.customer_name),
                ('phone', '=', self.customer_phone),
            ], limit=1) or Partner.create({
                'name': self.customer_name,
                'phone': self.customer_phone,
                'email': self.customer_email,
            })
            self.partner_id = partner
        return self.partner_id

    def action_prepare_payment(self, commission_amount=0.0):
        """Validate a booking and return what the POS needs to build the order."""
        self.ensure_one()
        if self.state not in ('confirmed', 'done'):
            raise UserError(self.env._("Only confirmed or completed bookings can be paid."))
        if self.payment_state == 'paid':
            raise UserError(self.env._("This booking is already paid."))
        config = self.config_id
        if config.apply_commission and self.specialist_id:
            if config.commission_type == 'manual':
                if not commission_amount or commission_amount <= 0:
                    raise UserError(self.env._(
                        "Please add the commission amount before taking the payment."))
                self.commission_amount = commission_amount
        partner = self._ensure_partner()
        product = self.env.ref('pos_salon.product_salon_service')
        try:
            lines = json.loads(self.service_lines or '[]')
        except ValueError:
            lines = []
        if not lines:
            lines = [{'name': self.service_name or self.env._("Salon Service"),
                      'price': self.amount_total}]
        for line in lines:
            if line.get('category'):
                line['name'] = "%s - %s" % (line['category'], line.get('name'))
            if line.get('prepaid_from'):
                line['name'] = self.env._(
                    "%(name)s - already paid (booking #%(ref)s)",
                    name=line.get('name'), ref=line['prepaid_from'])
        lines += [{'name': a.name, 'price': a.lst_price} for a in self.amenity_ids]
        return {
            'partner_id': partner.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'lines': lines,
        }

    def _mark_paid(self, order):
        """Called when the linked POS order is paid: only the payment status changes."""
        for booking in self.filtered(lambda b: b.payment_state != 'paid'):
            booking.write({'payment_state': 'paid', 'pos_order_id': order.id})

    def _get_lines(self):
        """Return the stored service lines as a list of dicts."""
        self.ensure_one()
        try:
            lines = json.loads(self.service_lines or '[]')
        except ValueError:
            return []
        return lines if isinstance(lines, list) else []

    def _get_slot_data(self):
        """Return {service_id: [times]} for scheduled bookings ({} for walk-ins)."""
        self.ensure_one()
        try:
            data = json.loads(self.slot or '{}')
        except ValueError:
            return {}
        return data if isinstance(data, dict) else {}

    def _slot_label(self, service_id):
        self.ensure_one()
        if (self.slot or '').strip() == 'Walk-in':
            return 'Walk-in'
        times = self._get_slot_data().get(service_id) or []
        return times[0] if times else ''

    @staticmethod
    def _line_matches(line, service_id, name):
        """New lines carry an id; old bookings only have a name."""
        if line.get('id'):
            return bool(service_id) and line['id'] == service_id
        return line.get('name') == name

    @api.model
    def get_customer_day_services(self, partner_id, date=None):
        """Services this customer already has booked on the given day."""
        date = date or fields.Date.context_today(self)
        bookings = self.search([
            ('partner_id', '=', partner_id),
            ('date', '=', date),
            ('state', 'in', ('confirmed', 'done')),
        ])
        result = []
        for booking in bookings:
            for line in booking._get_lines():
                if line.get('moved_to'):
                    continue
                result.append({
                    'booking_id': booking.id,
                    'service_id': line.get('id') or False,
                    'name': line.get('name'),
                    'slot': booking._slot_label(line.get('id')),
                    'paid': booking.payment_state == 'paid' or bool(line.get('prepaid_from')),
                    'completed': booking.state == 'done',
                    'can_reschedule': booking.state == 'confirmed',
                })
        return result

    def _release_services(self, indexes, new_booking):
        """Take moved services out of this (old) booking."""
        self.ensure_one()
        lines = self._get_lines()
        if self.payment_state == 'paid':
            # Paid: keep the booking as history, just mark the service as moved.
            for i in indexes:
                lines[i]['moved_to'] = new_booking.id
            vals = {'service_lines': json.dumps(lines)}
            if all(line.get('moved_to') for line in lines):
                vals['state'] = 'rescheduled'
            self.write(vals)
            return
        # Not paid yet: remove the services from this booking.
        removed_ids = [lines[i].get('id') for i in indexes]
        keep = [line for i, line in enumerate(lines) if i not in indexes]
        vals = {
            'service_lines': json.dumps(keep),
            'service_name': ', '.join(line.get('name') or '' for line in keep),
            'amount_total': sum(line.get('price') or 0 for line in keep),
        }
        slot_data = self._get_slot_data()
        if slot_data:
            for service_id in removed_ids:
                slot_data.pop(service_id, None)
            vals['slot'] = json.dumps(slot_data)
        self.write(vals)
        if not keep:
            self.action_cancel()

    @api.model
    def create_booking(self, vals, reschedule=None):
        """Create a booking, optionally moving services from earlier bookings.

        reschedule: [{'booking_id': 12, 'service_id': 'haircut_men', 'name': 'Men'}]
        Services that were already paid are added to the new booking at 0.
        """
        vals = dict(vals)
        if (vals.get('slot') or '').strip() == 'Walk-in':
            vals['checked_in'] = True
            vals['checked_in_time'] = fields.Datetime.now()
        try:
            lines = json.loads(vals.get('service_lines') or '[]')
        except ValueError:
            lines = []
        moves = {}
        for item in reschedule or []:
            old = self.browse(item.get('booking_id')).exists()
            if not old or old.state != 'confirmed':
                raise UserError(self.env._("The earlier booking can no longer be rescheduled."))
            old_lines = old._get_lines()
            idx = next((i for i, line in enumerate(old_lines)
                        if not line.get('moved_to')
                        and self._line_matches(line, item.get('service_id'), item.get('name'))), None)
            new_line = next((line for line in lines
                             if self._line_matches(line, item.get('service_id'), item.get('name'))), None)
            if idx is None or new_line is None:
                raise UserError(self.env._("%s is not part of the earlier booking.",
                                  item.get('name') or self.env._("This service")))
            old_line = old_lines[idx]
            if old.payment_state == 'paid' or old_line.get('prepaid_from'):
                new_line.update({
                    'price': 0,
                    'paid_price': old_line.get('paid_price') or old_line.get('price') or 0,
                    'prepaid_from': old_line.get('prepaid_from') or old.id,
                })
            moves.setdefault(old, []).append(idx)
        if moves:
            vals['service_lines'] = json.dumps(lines)
            vals['amount_total'] = sum(line.get('price') or 0 for line in lines)
            vals['rescheduled_from_id'] = list(moves)[0].id
        self._check_availability(vals, [old.id for old in moves])
        booking = self.create(vals)
        booking._assign_seat()
        for old, indexes in moves.items():
            old._release_services(indexes, booking)
        if (moves and lines and not booking.amenity_ids
                and all(line.get('prepaid_from') for line in lines)):
            booking.payment_state = 'paid'
        return booking.id

    SLOT_MINUTES = 30
    OPEN_MINUTES = 10 * 60
    CLOSE_MINUTES = 20 * 60

    @staticmethod
    def _slot_to_minutes(label):
        """'10:30 AM' -> 630"""
        try:
            time_part, suffix = (label or '').strip().split(' ')
            hours, minutes = [int(x) for x in time_part.split(':')]
        except ValueError:
            return None
        if suffix == 'PM' and hours < 12:
            hours += 12
        if suffix == 'AM' and hours == 12:
            hours = 0
        return hours * 60 + minutes

    @staticmethod
    def _minutes_to_label(minutes):
        """630 -> '10:30 AM'"""
        hours, mins = divmod(minutes, 60)
        suffix = 'PM' if hours >= 12 else 'AM'
        return '%d:%02d %s' % (((hours + 11) % 12) + 1, mins, suffix)

    @staticmethod
    def _line_duration(line):
        """Minutes of a service line ('45 min' -> 45). Old bookings: 30."""
        digits = ''.join(ch for ch in str(line.get('duration') or '') if ch.isdigit())
        return int(digits) if digits else 30

    @api.model
    def _slot_buckets(self, slot_json):
        """Slot starts (in minutes) of a scheduled booking."""
        try:
            data = json.loads(slot_json or '{}')
        except ValueError:
            return set()
        buckets = set()
        if isinstance(data, dict):
            for times in data.values():
                for label in times:
                    minutes = self._slot_to_minutes(label)
                    if minutes is not None:
                        buckets.add(minutes)
        return buckets

    @api.model
    def _walkin_buckets(self, start_minute, lines):
        """A walk-in holds a seat from its slot start (10:10 -> 10:00) for the service time."""
        duration = sum(self._line_duration(line) for line in lines) or self.SLOT_MINUTES
        start = (start_minute // self.SLOT_MINUTES) * self.SLOT_MINUTES
        buckets = set()
        bucket = start
        while bucket < start + duration:
            buckets.add(bucket)
            bucket += self.SLOT_MINUTES
        return buckets

    def _get_busy_buckets(self):
        self.ensure_one()
        if (self.slot or '').strip() == 'Walk-in':
            start = self.walkin_start
            if not start:
                local = fields.Datetime.context_timestamp(self, self.create_date)
                start = local.hour * 60 + local.minute
            return self._walkin_buckets(start, self._get_lines())
        return self._slot_buckets(self.slot)

    @api.model
    def _slot_usage(self, config_id, date, exclude_ids=None):
        """Return ({minute: seats used}, {specialist id: {busy minutes}})."""
        bookings = self.search([
            ('config_id', '=', config_id),
            ('date', '=', date),
            ('state', '=', 'confirmed'),
            ('id', 'not in', list(exclude_ids or [])),
        ])
        seats, specialists = {}, {}
        for booking in bookings:
            for minute in booking._get_busy_buckets():
                seats[minute] = seats.get(minute, 0) + 1
                if booking.specialist_id:
                    specialists.setdefault(booking.specialist_id.id, set()).add(minute)
        return seats, specialists

    @api.model
    def get_unavailable_slots(self, config_id, date, specialist_id=False, exclude_booking_ids=None):
        """Slot labels that cannot be booked: seats are full or the specialist is busy."""
        config = self.env['pos.config'].browse(config_id).exists()
        seats, specialists = self._slot_usage(config_id, date, exclude_booking_ids)
        busy = set()
        if config and config.salon_seats:
            busy |= {m for m, used in seats.items() if used >= config.salon_seats}
        if specialist_id:
            busy |= specialists.get(specialist_id, set())
        return [self._minutes_to_label(m) for m in sorted(busy)]

    @api.model
    def _check_availability(self, vals, exclude_ids=None):
        """Server-side check, so two cashiers cannot take the last seat together."""
        config = self.env['pos.config'].browse(vals.get('config_id')).exists()
        if not config:
            return
        slot = (vals.get('slot') or '').strip()
        try:
            lines = json.loads(vals.get('service_lines') or '[]')
        except ValueError:
            lines = []
        if slot == 'Walk-in':
            start = vals.get('walkin_start')
            if start is None:
                local = fields.Datetime.context_timestamp(self, fields.Datetime.now())
                start = local.hour * 60 + local.minute
            buckets = self._walkin_buckets(start, lines)
        else:
            buckets = self._slot_buckets(slot)
        seats, specialists = self._slot_usage(config.id, vals.get('date'), exclude_ids)
        specialist_id = vals.get('specialist_id') or False
        for minute in sorted(buckets):
            label = self._minutes_to_label(minute)
            if config.salon_seats and seats.get(minute, 0) >= config.salon_seats:
                raise UserError(self.env._("No seat is free at %s. Please choose another time.", label))
            if specialist_id and minute in specialists.get(specialist_id, set()):
                raise UserError(self.env._(
                    "The selected specialist is busy at %s. Please choose another time or specialist.",
                    label))

    def _minute_busy(self, config, seats, specialists, specialist_id, minute):
        """True if all seats are taken (or the specialist is busy) in that slot."""
        if config.salon_seats and seats.get(minute, 0) >= config.salon_seats:
            return True
        return bool(specialist_id) and minute in specialists.get(specialist_id, set())

    def _board_row(self):
        """One booking as shown in the walk-in conflict list."""
        self.ensure_one()
        buckets = sorted(self._get_busy_buckets())
        is_walkin = (self.slot or '').strip() == 'Walk-in'
        return {
            'id': self.id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'service_name': self.service_name,
            'seat_no': self.seat_no,
            'is_walkin': is_walkin,
            'checked_in': self.checked_in,
            'start': self._minutes_to_label(buckets[0]) if buckets else '',
            'end': self._minutes_to_label(buckets[-1] + self.SLOT_MINUTES) if buckets else '',
            'start_minute': buckets[0] if buckets else 0,
            'can_reschedule': self.state == 'confirmed' and not self.checked_in and not is_walkin,
        }

    def _assign_seat(self):
        """Give the booking the lowest seat that is free for all of its slots."""
        self.ensure_one()
        config = self.config_id
        if not config.salon_seats:
            return
        buckets = self._get_busy_buckets()
        others = self.search([
            ('config_id', '=', config.id),
            ('date', '=', self.date),
            ('state', '=', 'confirmed'),
            ('id', '!=', self.id),
        ])
        used = {other.seat_no for other in others
                if other.seat_no and other._get_busy_buckets() & buckets}
        for seat in range(1, config.salon_seats + 1):
            if seat not in used:
                self.seat_no = seat
                return
        self.seat_no = 0

    @api.model
    def get_walkin_plan(self, config_id, date, duration, now_minute, specialist_id=False):
        """Can a walk-in start now? If not: who holds the seats, and when is it free."""
        config = self.env['pos.config'].browse(config_id).exists()
        slot = self.SLOT_MINUTES
        start = max((now_minute // slot) * slot, self.OPEN_MINUTES)
        if start >= self.CLOSE_MINUTES:
            raise UserError(self.env._("The salon is closed for today."))
        duration = duration or slot
        seats, specialists = self._slot_usage(config_id, date)

        def window(first):
            return range((first // slot) * slot, first + duration, slot)

        def busy(minute):
            return self._minute_busy(config, seats, specialists, specialist_id, minute)

        seat_full = {m for m in window(start)
                     if config.salon_seats and seats.get(m, 0) >= config.salon_seats}
        conflict_minutes = {m for m in window(start) if busy(m)}
        conflicts = []
        if conflict_minutes:
            bookings = self.search([
                ('config_id', '=', config_id),
                ('date', '=', date),
                ('state', '=', 'confirmed'),
            ])
            for booking in bookings:
                held = booking._get_busy_buckets()
                same_specialist = specialist_id and booking.specialist_id.id == specialist_id
                if held & seat_full or (same_specialist and held & conflict_minutes):
                    conflicts.append(booking._board_row())
            conflicts.sort(key=lambda row: row['start_minute'])
        free_starts = [
            self._minutes_to_label(first)
            for first in range(start, self.CLOSE_MINUTES, slot)
            if first + duration <= self.CLOSE_MINUTES
               and not any(busy(m) for m in window(first))
        ]
        return {
            'start': self._minutes_to_label(start),
            'free_now': not conflict_minutes,
            'conflicts': conflicts,
            'free_starts': free_starts[:8],
        }

    @api.model
    def get_reschedule_options(self, booking_id, now_minute):
        """Start times this booking can be moved to (all its slots shift together)."""
        booking = self.browse(booking_id).exists()
        if not booking or booking.state != 'confirmed' or booking.checked_in:
            raise UserError(self.env._("This booking can no longer be rescheduled."))
        buckets = sorted(booking._get_busy_buckets())
        if not buckets:
            return []
        config = booking.config_id
        specialist_id = booking.specialist_id.id
        seats, specialists = self._slot_usage(config.id, booking.date, [booking.id])
        slot = self.SLOT_MINUTES
        earliest = max((now_minute // slot) * slot, self.OPEN_MINUTES)
        options = []
        for first in range(earliest, self.CLOSE_MINUTES, slot):
            shifted = [m - buckets[0] + first for m in buckets]
            if shifted[-1] + slot > self.CLOSE_MINUTES:
                break
            if first == buckets[0]:
                continue
            if not any(self._minute_busy(config, seats, specialists, specialist_id, m)
                       for m in shifted):
                options.append(self._minutes_to_label(first))
        return options[:8]

    @api.model
    def reschedule_booking(self, booking_id, new_start):
        """Move a booking that has not arrived to a new start time, same booking."""
        booking = self.browse(booking_id).exists()
        if not booking or booking.state != 'confirmed' or booking.checked_in:
            raise UserError(self.env._("This booking can no longer be rescheduled."))
        if (booking.slot or '').strip() == 'Walk-in':
            raise UserError(self.env._("A walk-in cannot be rescheduled here."))
        first = self._slot_to_minutes(new_start)
        data = booking._get_slot_data()
        old = sorted(m for times in data.values()
                     for m in map(self._slot_to_minutes, times) if m is not None)
        if first is None or not old:
            raise UserError(self.env._("Please choose a valid time."))
        delta = first - old[0]
        if first < self.OPEN_MINUTES or old[-1] + delta + self.SLOT_MINUTES > self.CLOSE_MINUTES:
            raise UserError(self.env._("That time is outside the opening hours."))
        new_slot = json.dumps({
            sid: [self._minutes_to_label(self._slot_to_minutes(t) + delta) for t in times]
            for sid, times in data.items()
        })
        self._check_availability({
            'config_id': booking.config_id.id,
            'date': booking.date,
            'slot': new_slot,
            'service_lines': booking.service_lines,
            'specialist_id': booking.specialist_id.id,
        }, [booking.id])
        booking.write({'slot': new_slot, 'seat_no': 0})
        booking._assign_seat()
        return True

    def action_mark_arrived(self):
        """Staff confirms the booked customer has arrived."""
        for booking in self:
            if booking.state != 'confirmed':
                raise UserError(self.env._("Only confirmed bookings can be marked as arrived."))
        self.write({'checked_in': True, 'checked_in_time': fields.Datetime.now()})

    @api.model
    def get_booking_options(self, config_id):
        """Return the specialists and amenities configured for a POS config."""
        config = self.env['pos.config'].browse(config_id).exists()
        if not config:
            return {'specialists': [], 'amenities': []}
        return {
            'specialists': [
                {'id': partner.id, 'name': partner.name}
                for partner in config.specialist_ids
            ],
            'amenities': [
                {'id': product.id, 'name': product.name, 'price': product.lst_price}
                for product in config.amenities_ids
            ],
        }

    @api.model
    def get_commission_data(self, config_id, scope='today'):
        """Return commission rows and per-specialist totals for the POS screen."""
        config = self.env['pos.config'].browse(config_id).exists()
        if not config or not config.apply_commission:
            return {'allowed': False,
                    'message': self.env._("Commission is not enabled for this shop.")}
        if not self.env.user.has_group('point_of_sale.group_pos_manager'):
            return {'allowed': False,
                    'message': self.env._("Only POS managers can view commission.")}
        domain = [
            ('config_id', '=', config.id),
            ('state', 'in', ('done', 'rescheduled')),
            ('payment_state', '=', 'paid'),
            ('amount_total', '>', 0),
            ('specialist_id', '!=', False),
        ]
        if scope == 'today':
            domain.append(('date', '=', fields.Date.context_today(self)))
        rows = []
        totals = {}
        for booking in self.search(domain, order='date desc, id desc'):
            rows.append({
                'id': booking.id,
                'date': str(booking.date),
                'customer_name': booking.customer_name,
                'service_name': booking.service_name,
                'specialist': booking.specialist_id.name,
                'amount_total': booking.amount_total,
                'commission_amount': booking.commission_amount,
            })
            item = totals.setdefault(booking.specialist_id.id, {
                'specialist': booking.specialist_id.name,
                'count': 0, 'amount': 0.0, 'commission': 0.0,
            })
            item['count'] += 1
            item['amount'] += booking.amount_total
            item['commission'] += booking.commission_amount
        return {
            'allowed': True,
            'rows': rows,
            'totals': list(totals.values()),
            'grand_amount': sum(t['amount'] for t in totals.values()),
            'grand_commission': sum(t['commission'] for t in totals.values()),
        }

    def action_done(self, commission_amount=None):
        """Mark the service as completed. Payment is not touched here."""
        for booking in self:
            if booking.state != 'confirmed':
                raise UserError(self.env._("Only confirmed bookings can be completed."))
        for booking in self:
            vals = {'state': 'done'}
            config = booking.config_id
            if config.apply_commission and booking.specialist_id:
                if config.commission_type == 'auto':
                    vals['commission_amount'] = (
                            booking.amount_total * config.commission_percent / 100.0)
                elif commission_amount and commission_amount > 0:
                    vals['commission_amount'] = commission_amount
            booking.write(vals)
            booking._send_review_mail()

    def action_cancel(self):
        """Cancel draft or confirmed bookings that have no payment."""
        for booking in self:
            if booking.state not in ('draft', 'confirmed'):
                raise UserError(self.env._("Only draft or confirmed bookings can be cancelled."))
            if booking.payment_state != 'unpaid':
                raise UserError(self.env._(
                    "A paid booking cannot be cancelled. Refund the payment first."))
        self.write({'state': 'cancelled'})
