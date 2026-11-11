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
import logging
from datetime import datetime, time, timedelta
import pytz
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SalonBooking(models.Model):
    """Creates 'salon booking' to create salon bookings"""
    _name = 'salon.booking'
    _description = 'Salon Booking'

    name = fields.Char(required=True, help="Name of customer")
    state = fields.Selection(default="draft",
                             selection=[('draft', 'Draft'),
                                        ('approved', 'Approved'),
                                        ('rejected', 'Rejected')],
                             help="State of the booking")
    time = fields.Datetime(string="Date", required=True,
                           help="Start time of the booking")
    phone = fields.Char(help="Phone number of customer.")
    email = fields.Char(string="E-Mail", help="Email of the customer")
    service_ids = fields.Many2many(comodel_name='salon.service',
                                   string="Services",
                                   help="Salon services")
    chair_id = fields.Many2one('salon.chair',
                               required=True, help="Select the chair for "
                                                   "booking")
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda self: self.env.company,
                                 help="Default company")
    filtered_order_ids = fields.Many2many(comodel_name='salon.order',
                                          string="Salon Orders",
                                          compute="_compute_filtered_order_ids",
                                          help="Orders for each salon")

    @api.depends('time', 'chair_id')
    def _compute_filtered_order_ids(self):
        """Computes the filtered_order_ids field"""
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        for booking in self:
            if booking.time:
                date_only = pytz.UTC.localize(booking.time).astimezone(
                    tz).date()
            else:
                date_only = fields.Date.context_today(booking)
            date_start = tz.localize(
                datetime.combine(date_only, time(0, 0, 0))
            ).astimezone(pytz.UTC).replace(tzinfo=None)
            date_end = tz.localize(
                datetime.combine(date_only, time(23, 59, 59))
            ).astimezone(pytz.UTC).replace(tzinfo=None)
            booking.filtered_order_ids = self.env['salon.order'].search([
                ('chair_id', '=', booking.chair_id.id),
                ('start_time', '>=', date_start),
                ('start_time', '<=', date_end)])

    def _get_estimated_duration(self):
        """Estimated duration (in hours) of the booking, based on the
        total time of the requested services. Falls back to half an hour
        when no service (or no time on the services) is set, so the
        booking always occupies a real slot on the chair for the overlap
        checks below."""
        self.ensure_one()
        duration = sum(self.sudo().service_ids.mapped('time_taken'))
        return duration or 0.5

    def _get_conflicting_orders(self):
        """Salon orders already occupying the chair during this booking's
        estimated time window."""
        self.ensure_one()
        if not self.chair_id or not self.time:
            return self.env['salon.order']
        end_time = self.time + timedelta(hours=self._get_estimated_duration())
        cancelled_stage_id = self.env['salon.stage']._get_stage_id('cancelled')
        domain = [
            ('chair_id', '=', self.chair_id.id),
            ('start_time', '<', end_time),
            ('end_time', '>', self.time),
        ]
        if cancelled_stage_id:
            domain.append(('stage_id', '!=', cancelled_stage_id))
        return self.env['salon.order'].sudo().search(domain)

    def _get_conflicting_bookings(self):
        """Other (still relevant) bookings requesting the same chair at
        the exact same time."""
        self.ensure_one()
        if not self.chair_id or not self.time:
            return self.env['salon.booking']
        return self.env['salon.booking'].sudo().search([
            ('chair_id', '=', self.chair_id.id),
            ('id', '!=', self.id),
            ('state', '!=', 'rejected'),
            ('time', '=', self.time),
        ])

    @api.model_create_multi
    def create(self, vals_list):
        """Create the booking(s) and immediately let the customer know
        their request came through.

        Without this, a customer who submits the website form only sees
        a generic "Thank you" page - if they navigate away, refresh, or
        the page fails to load for any reason, they have no proof the
        booking was actually received, and no reference to it while it
        sits waiting for staff approval. A confirmation e-mail closes
        that gap and reflects the true state of the request (received,
        not yet approved)."""
        bookings = super().create(vals_list)
        # Website visitors submit this form as the public user, which has
        # no read access to mail.template/mail.mail. Sending the
        # confirmation e-mail must run with elevated rights (sudo), and
        # any failure here (missing mail server, mail access, etc.) must
        # never bubble up and cause the caller to roll back the booking
        # that was already successfully created.
        template = self.env.ref(
            'salon_management.mail_template_salon_request_received',
            raise_if_not_found=False)
        if template:
            for booking in bookings:
                if booking.email:
                    try:
                        template.sudo().send_mail(booking.id, force_send=True)
                    except Exception:
                        _logger.warning(
                            "Could not send booking confirmation e-mail "
                            "for salon.booking %s", booking.id,
                            exc_info=True)
        return bookings

    @api.constrains('chair_id', 'time', 'service_ids', 'state')
    def _check_chair_availability(self):
        """A chair cannot be requested/booked for two overlapping salon
        orders or bookings at the same time."""
        for booking in self:
            if booking.state != 'draft':
                continue
            if booking._get_conflicting_orders():
                raise ValidationError(self.env._(
                    "The chair '%(chair)s' is already occupied by another "
                    "salon order at the selected time. Please choose a "
                    "different chair or time slot.",
                    chair=booking.sudo().chair_id.name))
            if booking._get_conflicting_bookings():
                raise ValidationError(self.env._(
                    "The chair '%(chair)s' already has another booking "
                    "requested for the same time. Please choose a different "
                    "chair or time slot.",
                    chair=booking.sudo().chair_id.name))

    def action_approve_booking(self):
        """Approve the booking for salon services.

        A single salon order is created for the booking (one order line
        per requested service) instead of one order per service, so the
        chair only ever ends up linked to a single salon order for this
        time slot."""
        draft_stage_id = self.env['salon.stage']._get_stage_id('draft')
        for booking in self:
            if booking._get_conflicting_orders():
                raise ValidationError(self.env._(
                    "The chair '%(chair)s' is already occupied by another "
                    "salon order at the selected time. Please choose a "
                    "different chair or time slot.",
                    chair=booking.sudo().chair_id.name))
            if booking._get_conflicting_bookings():
                raise ValidationError(self.env._(
                    "The chair '%(chair)s' already has another booking "
                    "requested for the same time. Please choose a different "
                    "chair or time slot.",
                    chair=booking.sudo().chair_id.name))
            booking.state = "approved"
            booking.env['salon.order'].create({
                'customer_name': booking.name,
                'chair_id': booking.chair_id.id,
                'start_time': booking.time,
                'date': fields.Datetime.now(),
                'stage_id': draft_stage_id,
                'booking_identifier': True,
                'order_line_ids': [(0, 0, {
                    'service_id': service.id,
                    'time_taken': service.time_taken,
                    'price': service.price,
                    'price_subtotal': service.price,
                }) for service in booking.service_ids],
            })
            self.env.ref(
                'salon_management.mail_template_salon_approved'
                ).sudo().send_mail(booking.id, force_send=True)

    def action_reject_booking(self):
        """Reject booking for salon services"""
        self.env.ref(
            'salon_management.mail_template_salon_rejected'
            ).sudo().send_mail(self.id, force_send=True)
        self.state = "rejected"

    def get_booking_count(self):
        """Gets the dashboard data: counts of salon bookings, salon orders,
        salon clients, today's revenue, a breakdown of orders/bookings per
        state, a combined recent orders/bookings table and a per-service
        summary.
        Returns: dict consumed by the dashboard widget."""
        # Resolve stage ids dynamically to avoid relying on hardcoded ids.
        get_stage = self.env['salon.stage']._get_stage_id
        invoiced_or_closed = [
            s for s in [get_stage('invoiced'), get_stage('closed')] if s]

        today_orders = self.env['salon.order'].search(
            [('stage_id', 'in', invoiced_or_closed),
             ('date', '>=', fields.Date.context_today(self)),
             ('date', '<', fields.Date.context_today(self) + timedelta(days=1))])

        # --- Orders grouped by stage (Draft / Open / Invoiced / Closed / Cancelled) ---
        stage_model = self.env['salon.stage']
        stages = stage_model.browse(stage_model._search([], order='sequence'))
        orders_by_stage = [{
            'id': stage.id,
            'name': stage.name,
            'count': self.env['salon.order'].search_count(
                [('stage_id', '=', stage.id)]),
        } for stage in stages]

        # --- Bookings grouped by state (Draft / Approved / Rejected) ---
        state_selection = self.env['salon.booking']._fields['state'].selection
        bookings_by_state = [{
            'key': key,
            'name': label,
            'count': self.env['salon.booking'].search_count(
                [('state', '=', key)]),
        } for key, label in state_selection]

        # --- Combined recent Orders/Bookings table ---
        table_rows = []
        for order in self.env['salon.order'].search([], order='date desc', limit=10):
            table_rows.append({
                'id': order.id,
                'model': 'salon.order',
                'type': 'Order',
                'reference': order.name,
                'customer': order.customer_name,
                'chair': order.chair_id.name or '',
                'date': fields.Datetime.to_string(order.start_time) if order.start_time else '',
                'state': order.stage_id.name or '',
                'amount': order.price_subtotal,
            })
        for booking in self.env['salon.booking'].search([], order='time desc', limit=10):
            table_rows.append({
                'id': booking.id,
                'model': 'salon.booking',
                'type': 'Booking',
                'reference': booking.name,
                'customer': booking.name,
                'chair': booking.chair_id.name or '',
                'date': fields.Datetime.to_string(booking.time) if booking.time else '',
                'state': dict(state_selection).get(booking.state, booking.state),
                'amount': sum(booking.service_ids.mapped('price')),
            })
        table_rows.sort(key=lambda row: row['date'], reverse=True)

        # --- Services summary: how many orders per service ---
        services_summary = []
        service_model = self.env['salon.service']
        for service in service_model.browse(service_model._search([])):
            lines = self.env['salon.order.line'].search(
                [('service_id', '=', service.id)])
            services_summary.append({
                'id': service.id,
                'name': service.name,
                'price': service.price,
                'orders_count': len(lines),
                'revenue': sum(lines.mapped('price_subtotal')),
            })

        return {
            'bookings': self.env['salon.booking'].search_count(
                [('state', '=', 'approved')]),
            'sales': self.env['salon.order'].search_count(
                [('stage_id', 'in', invoiced_or_closed)]),
            'orders': self.env['salon.order'].search_count([]),
            'clients': self.env['res.partner'].search_count(
                [('partner_salon', '=', True)]),
            'revenue_today': sum(today_orders.mapped('price_subtotal')),
            'revenue_stage_ids': invoiced_or_closed,
            'currency_id': self.env.company.currency_id.id,
            'chairs': self.env['salon.chair'].browse(
                self.env['salon.chair']._search([])),
            'orders_by_stage': orders_by_stage,
            'bookings_by_state': bookings_by_state,
            'table_rows': table_rows[:12],
            'services_summary': services_summary,
        }

    @api.model
    def quick_create_booking(self, vals):
        """Create a salon booking directly from the dashboard's quick
        booking form.

        :param vals: dict with keys name, phone, email, chair_id, time
            (string 'YYYY-MM-DD HH:MM:SS' in UTC) and service_ids (list
            of salon.service ids).
        :return: dict with the id/name of the created booking.
        :raises ValidationError: if required data is missing or the
            chair is already booked for an overlapping period.
        """
        if not vals.get('name'):
            raise ValidationError(self.env._("Please enter the customer's name."))
        if not vals.get('chair_id'):
            raise ValidationError(self.env._("Please select a chair."))
        if not vals.get('time'):
            raise ValidationError(self.env._("Please select a date & time."))
        service_ids = vals.get('service_ids') or []
        booking = self.create({
            'name': vals.get('name'),
            'phone': vals.get('phone'),
            'email': vals.get('email'),
            'chair_id': vals.get('chair_id'),
            'time': vals.get('time'),
            'service_ids': [(6, 0, service_ids)],
        })
        return {'id': booking.id, 'name': booking.name}
