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
from unittest.mock import patch

from odoo.addons.mail.models.mail_template import MailTemplate
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import SalonCommon


@tagged('post_install', '-at_install')
class TestSalonBooking(SalonCommon):

    # ------------------------------------------------------------------
    # creation + confirmation mail
    # ------------------------------------------------------------------
    def test_create_defaults(self):
        booking = self.make_booking()
        self.assertEqual(booking.state, 'draft')
        self.assertEqual(booking.company_id, self.env.company)

    def test_creation_sends_received_mail(self):
        with patch.object(MailTemplate, 'send_mail',
                          autospec=True) as send_mail:
            booking = self.make_booking()
        self.assertEqual(send_mail.call_count, 1)
        self.assertEqual(send_mail.call_args.args[1], booking.id)

    def test_no_mail_without_email(self):
        with patch.object(MailTemplate, 'send_mail',
                          autospec=True) as send_mail:
            self.make_booking(email=False)
        send_mail.assert_not_called()

    def test_mail_failure_does_not_block_creation(self):
        with patch.object(MailTemplate, 'send_mail', autospec=True,
                          side_effect=Exception("SMTP down")):
            booking = self.make_booking()
        self.assertTrue(booking.exists())

    def test_creation_without_template(self):
        self.env.ref(
            'salon_management.mail_template_salon_request_received'
        ).unlink()
        booking = self.make_booking()
        self.assertTrue(booking.exists())

    # ------------------------------------------------------------------
    # estimated duration + availability
    # ------------------------------------------------------------------
    def test_estimated_duration(self):
        both = self.make_booking(
            services=self.service_hair | self.service_nail)
        self.assertEqual(both._get_estimated_duration(), 1.5)
        none = self.make_booking(time=self.at(days=1), services=self.env[
            'salon.service'])
        self.assertEqual(none._get_estimated_duration(), 0.5)

    def test_conflict_with_existing_order(self):
        self.make_order()  # 09:00 - 10:30
        with self.assertRaises(ValidationError):
            self.make_booking(time=self.at(hours=1))

    def test_no_conflict_after_order(self):
        self.make_order()  # 09:00 - 10:30
        booking = self.make_booking(time=self.at(hours=1.5))
        self.assertTrue(booking.id)

    def test_no_conflict_with_cancelled_order(self):
        self.make_order().action_cancel()
        booking = self.make_booking()
        self.assertTrue(booking.id)

    def test_no_conflict_on_other_chair(self):
        self.make_order()
        booking = self.make_booking(chair=self.chair2)
        self.assertTrue(booking.id)

    def test_conflict_with_same_time_booking(self):
        self.make_booking()
        with self.assertRaises(ValidationError):
            self.make_booking()

    def test_rejected_booking_frees_the_slot(self):
        first = self.make_booking()
        first.action_reject_booking()
        again = self.make_booking()
        self.assertTrue(again.id)

    def test_conflict_helpers_without_chair_or_time(self):
        booking = self.env['salon.booking'].new({})
        self.assertFalse(booking._get_conflicting_orders())
        self.assertFalse(booking._get_conflicting_bookings())

    # ------------------------------------------------------------------
    # approve / reject
    # ------------------------------------------------------------------
    def test_approve_creates_single_order(self):
        booking = self.make_booking(
            services=self.service_hair | self.service_nail)
        with patch.object(MailTemplate, 'send_mail', autospec=True):
            booking.action_approve_booking()
        self.assertEqual(booking.state, 'approved')
        order = self.env['salon.order'].search(
            [('chair_id', '=', self.chair.id),
             ('start_time', '=', booking.time)])
        self.assertEqual(len(order), 1)
        self.assertEqual(order.customer_name, booking.name)
        self.assertTrue(order.booking_identifier)
        self.assertEqual(order.stage_id, self.stage_draft)
        self.assertEqual(len(order.order_line_ids), 2)
        self.assertEqual(order.price_subtotal, 150.0)
        self.assertEqual(order.time_taken_total, 1.5)

    def test_approve_sends_mail(self):
        booking = self.make_booking()
        with patch.object(MailTemplate, 'send_mail',
                          autospec=True) as send_mail:
            booking.action_approve_booking()
        self.assertEqual(send_mail.call_args.args[1], booking.id)

    def test_approve_blocked_by_new_order(self):
        booking = self.make_booking()
        self.make_order()  # created after the booking request
        with self.assertRaises(ValidationError):
            booking.action_approve_booking()
        self.assertEqual(booking.state, 'draft')

    def test_approve_blocked_by_other_booking(self):
        booking = self.make_booking()
        # an already approved booking (skips the draft-only constraint)
        self.make_booking(state='approved')
        with self.assertRaises(ValidationError):
            booking.action_approve_booking()

    def test_reject(self):
        booking = self.make_booking()
        with patch.object(MailTemplate, 'send_mail',
                          autospec=True) as send_mail:
            booking.action_reject_booking()
        self.assertEqual(booking.state, 'rejected')
        self.assertEqual(send_mail.call_args.args[1], booking.id)
        self.assertFalse(self.env['salon.order'].search(
            [('chair_id', '=', self.chair.id),
             ('start_time', '=', booking.time)]))

    # ------------------------------------------------------------------
    # filtered orders (booking form helper)
    # ------------------------------------------------------------------
    def test_filtered_orders_for_booking_day(self):
        order = self.make_order()
        other_day = self.make_order(start=self.at(days=2))
        booking = self.env['salon.booking'].new({
            'chair_id': self.chair.id, 'time': self.at(hours=3)})
        orders = booking.filtered_order_ids._origin
        self.assertIn(order, orders)
        self.assertNotIn(other_day, orders)

    def test_filtered_orders_without_time(self):
        booking = self.env['salon.booking'].new(
            {'chair_id': self.chair.id})
        # falls back on today's date, must not crash
        self.assertFalse(booking.filtered_order_ids.filtered(
            lambda o: o.start_time == self.at()))

    # ------------------------------------------------------------------
    # dashboard
    # ------------------------------------------------------------------
    def test_dashboard_data(self):
        order = self.make_order(partner_id=self.customer.id)
        order.action_confirm()
        order.action_create_invoice()
        booking = self.make_booking(time=self.at(days=1))
        booking.action_approve_booking()
        self.make_booking(time=self.at(days=2), state='rejected')
        data = self.env['salon.booking'].get_booking_count()
        for key in ('bookings', 'sales', 'orders', 'clients',
                    'revenue_today', 'currency_id', 'chairs',
                    'orders_by_stage', 'bookings_by_state', 'table_rows',
                    'services_summary'):
            self.assertIn(key, data)
        self.assertGreaterEqual(data['bookings'], 1)
        self.assertGreaterEqual(data['sales'], 1)
        self.assertGreaterEqual(data['orders'], 2)
        self.assertGreaterEqual(data['clients'], 1)
        self.assertGreaterEqual(data['revenue_today'], 150.0)
        self.assertEqual(data['currency_id'], self.env.company.currency_id.id)
        self.assertIn(self.chair, data['chairs'])
        self.assertEqual(len(data['orders_by_stage']), 5)
        self.assertEqual(
            {s['key']: s['name'] for s in data['bookings_by_state']},
            {'draft': 'Draft', 'approved': 'Approved',
             'rejected': 'Rejected'})
        invoiced = [s for s in data['orders_by_stage']
                    if s['id'] == self.stage_invoiced.id][0]
        self.assertGreaterEqual(invoiced['count'], 1)
        types = {row['type'] for row in data['table_rows']}
        self.assertEqual(types, {'Order', 'Booking'})
        self.assertLessEqual(len(data['table_rows']), 12)
        dates = [row['date'] for row in data['table_rows']]
        self.assertEqual(dates, sorted(dates, reverse=True))
        hair = [s for s in data['services_summary']
                if s['id'] == self.service_hair.id][0]
        self.assertEqual(hair['orders_count'], 2)
        self.assertEqual(hair['revenue'], 200.0)

    # ------------------------------------------------------------------
    # quick booking from the dashboard
    # ------------------------------------------------------------------
    def test_quick_create_booking(self):
        result = self.env['salon.booking'].quick_create_booking({
            'name': 'Quick', 'phone': '999', 'email': 'q@example.com',
            'chair_id': self.chair.id, 'time': '2031-04-01 10:00:00',
            'service_ids': [self.service_hair.id, self.service_nail.id],
        })
        booking = self.env['salon.booking'].browse(result['id'])
        self.assertEqual(result['name'], 'Quick')
        self.assertEqual(booking.service_ids,
                         self.service_hair | self.service_nail)
        self.assertEqual(booking.state, 'draft')

    def test_quick_create_booking_without_services(self):
        result = self.env['salon.booking'].quick_create_booking({
            'name': 'Quick', 'chair_id': self.chair.id,
            'time': '2031-04-02 10:00:00'})
        self.assertFalse(self.env['salon.booking'].browse(
            result['id']).service_ids)

    def test_quick_create_booking_validation(self):
        base = {'name': 'Quick', 'chair_id': self.chair.id,
                'time': '2031-04-03 10:00:00'}
        for missing in ('name', 'chair_id', 'time'):
            vals = dict(base)
            vals.pop(missing)
            with self.assertRaises(ValidationError):
                self.env['salon.booking'].quick_create_booking(vals)

    def test_quick_create_booking_conflict(self):
        vals = {'name': 'Quick', 'chair_id': self.chair.id,
                'time': '2031-04-04 10:00:00'}
        self.env['salon.booking'].quick_create_booking(vals)
        with self.assertRaises(ValidationError):
            self.env['salon.booking'].quick_create_booking(vals)
