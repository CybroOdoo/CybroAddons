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
from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from .common import TestSalonCommon


@tagged('post_install', '-at_install', 'pos_salon')
class TestSalonBooking(TestSalonCommon):
    """Test suite for salon.booking model."""

    __test__ = True

    def test_01_create_booking_success(self):
        """Test successful creation of a salon booking and partner fields synchronization."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'amount_total': 100.0,
            'service_name': 'Haircut & Styling',
            'service_lines': json.dumps([{
                'name': 'Haircut & Styling',
                'price': 100.0,
                'duration': '30 min'
            }]),
            'config_id': self.pos_config.id,
        })
        self.assertEqual(booking.customer_name, self.customer_partner.name)
        self.assertEqual(booking.customer_phone, self.customer_partner.phone)
        self.assertEqual(booking.customer_email, self.customer_partner.email)
        self.assertEqual(booking.state, 'draft')
        self.assertEqual(booking.payment_state, 'unpaid')

    def test_02_create_booking_sync_phone_to_partner(self):
        """When customer has no phone, creating booking should update partner phone."""
        self.assertFalse(self.customer_no_phone.phone)
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_no_phone.id,
            'customer_phone': '+9988776655',
            'date': fields.Date.today(),
            'config_id': self.pos_config.id,
        })
        self.assertEqual(booking.customer_phone, '+9988776655')
        self.assertEqual(self.customer_no_phone.phone, '+9988776655')

    def test_03_create_booking_missing_partner_error(self):
        """Creating a booking without a partner should raise UserError."""
        with self.assertRaises(UserError):
            self.env['salon.booking'].create({
                'customer_name': 'No Partner Customer',
                'customer_phone': '+1234567890',
                'date': fields.Date.today(),
                'config_id': self.pos_config.id,
            })

    def test_04_create_booking_missing_phone_error(self):
        """Creating a booking without phone when partner has no phone should raise UserError."""
        with self.assertRaises(UserError):
            self.env['salon.booking'].create({
                'partner_id': self.customer_no_phone.id,
                'customer_phone': '',
                'date': fields.Date.today(),
                'config_id': self.pos_config.id,
            })

    def test_05_ensure_partner(self):
        """Test _ensure_partner returns partner_id or searches/creates partner."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'config_id': self.pos_config.id,
        })
        partner = booking._ensure_partner()
        self.assertEqual(partner.id, self.customer_partner.id)

    def test_06_compute_amounts_and_amenity_names(self):
        """Test calculation of amount_payable, amount_due, and amenity_names."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'amount_total': 50.0,
            'amenity_ids': [(6, 0, [self.amenity_spa.id, self.amenity_massage.id])],
            'config_id': self.pos_config.id,
        })
        # 50.0 service + 30.0 spa + 20.0 massage = 100.0
        self.assertAlmostEqual(booking.amount_payable, 100.0)
        self.assertAlmostEqual(booking.amount_due, 100.0)
        self.assertIn(self.amenity_spa.name, booking.amenity_names)
        self.assertIn(self.amenity_massage.name, booking.amenity_names)

        # Mark paid: amount_due should become 0.0
        booking.payment_state = 'paid'
        self.assertAlmostEqual(booking.amount_due, 0.0)

    def test_07_slot_utility_helpers(self):
        """Test time and slot conversion helper methods."""
        Booking = self.env['salon.booking']
        # _slot_to_minutes
        self.assertEqual(Booking._slot_to_minutes('10:00 AM'), 600)
        self.assertEqual(Booking._slot_to_minutes('10:30 AM'), 630)
        self.assertEqual(Booking._slot_to_minutes('12:00 PM'), 720)
        self.assertEqual(Booking._slot_to_minutes('01:30 PM'), 810)
        self.assertEqual(Booking._slot_to_minutes('12:00 AM'), 0)
        self.assertIsNone(Booking._slot_to_minutes('Invalid time'))

        # _minutes_to_label
        self.assertEqual(Booking._minutes_to_label(600), '10:00 AM')
        self.assertEqual(Booking._minutes_to_label(720), '12:00 PM')
        self.assertEqual(Booking._minutes_to_label(810), '1:30 PM')

        # _line_duration
        self.assertEqual(Booking._line_duration({'duration': '45 min'}), 45)
        self.assertEqual(Booking._line_duration({'duration': 60}), 60)
        self.assertEqual(Booking._line_duration({}), 30)

        # _slot_buckets
        slot_json = json.dumps({'svc1': ['10:00 AM', '10:30 AM']})
        self.assertEqual(Booking._slot_buckets(slot_json), {600, 630})

        # _walkin_buckets
        lines = [{'duration': '60 min'}]
        # 610 starts at slot floor 600, duration 60 -> {600, 630}
        self.assertEqual(Booking._walkin_buckets(610, lines), {600, 630})

    def test_08_compute_time_period(self):
        """Test time_period calculation for scheduled and walk-in bookings."""
        # Scheduled booking
        booking_sched = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'slot': json.dumps({'s1': ['10:00 AM', '10:30 AM']}),
            'config_id': self.pos_config.id,
        })
        self.assertEqual(booking_sched.time_period, '10:00 AM - 11:00 AM')

        # Walk-in booking
        booking_walkin = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'slot': 'Walk-in',
            'walkin_start': 660,  # 11:00 AM
            'service_lines': json.dumps([{'name': 'Wash', 'duration': '30 min'}]),
            'config_id': self.pos_config.id,
        })
        self.assertEqual(booking_walkin.time_period, '11:00 AM - 11:30 AM')

    def test_09_rating_constraints_and_stars(self):
        """Test rating constrains (0-5) and rating_stars computation."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'config_id': self.pos_config.id,
        })
        booking.rating = 4
        self.assertEqual(booking.rating_stars, '★★★★☆')

        booking.rating = 5
        self.assertEqual(booking.rating_stars, '★★★★★')

        booking.rating = 0
        self.assertEqual(booking.rating_stars, '')

        # Rating > 5 raises ValidationError
        with self.assertRaises(ValidationError):
            booking.rating = 6

        # Rating < 0 raises ValidationError
        with self.assertRaises(ValidationError):
            booking.rating = -1

    def test_10_review_url_computation(self):
        """Test review_url computation when review_token is present."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'config_id': self.pos_config.id,
        })
        self.assertFalse(booking.review_url)
        booking.review_token = 'token_test_123'
        self.assertTrue(booking.review_url)
        self.assertIn('/salon/review/token_test_123', booking.review_url)

    def test_11_action_mark_arrived(self):
        """Test staff marking arrival for confirmed booking."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'draft',
            'config_id': self.pos_config.id,
        })
        # Draft booking raises UserError
        with self.assertRaises(UserError):
            booking.action_mark_arrived()

        booking.state = 'confirmed'
        booking.action_mark_arrived()
        self.assertTrue(booking.checked_in)
        self.assertTrue(booking.checked_in_time)

    def test_12_action_cancel(self):
        """Test action_cancel on draft, confirmed, done, and paid bookings."""
        # Cancel draft
        booking_draft = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'draft',
            'payment_state': 'unpaid',
            'config_id': self.pos_config.id,
        })
        booking_draft.action_cancel()
        self.assertEqual(booking_draft.state, 'cancelled')

        # Cancel confirmed
        booking_conf = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'confirmed',
            'payment_state': 'unpaid',
            'config_id': self.pos_config.id,
        })
        booking_conf.action_cancel()
        self.assertEqual(booking_conf.state, 'cancelled')

        # Cancel done booking raises UserError
        booking_done = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'done',
            'payment_state': 'unpaid',
            'config_id': self.pos_config.id,
        })
        with self.assertRaises(UserError):
            booking_done.action_cancel()

        # Cancel paid booking raises UserError
        booking_paid = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'confirmed',
            'payment_state': 'paid',
            'config_id': self.pos_config.id,
        })
        with self.assertRaises(UserError):
            booking_paid.action_cancel()

    def test_13_action_done_auto_commission(self):
        """Test action_done calculates automatic commission percentage correctly."""
        self.pos_config.write({
            'apply_commission': True,
            'commission_type': 'auto',
            'commission_percent': 15.0,
        })
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'confirmed',
            'amount_total': 200.0,
            'specialist_id': self.specialist_partner.id,
            'config_id': self.pos_config.id,
        })
        booking.action_done()
        self.assertEqual(booking.state, 'done')
        # 15% of 200.0 = 30.0
        self.assertAlmostEqual(booking.commission_amount, 30.0)

    def test_14_action_done_manual_commission(self):
        """Test action_done accepts manual commission amount."""
        self.pos_config.write({
            'apply_commission': True,
            'commission_type': 'manual',
        })
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'confirmed',
            'amount_total': 200.0,
            'specialist_id': self.specialist_partner.id,
            'config_id': self.pos_config.id,
        })
        booking.action_done(commission_amount=45.0)
        self.assertEqual(booking.state, 'done')
        self.assertAlmostEqual(booking.commission_amount, 45.0)

    def test_15_action_done_draft_error(self):
        """Calling action_done on a non-confirmed booking should raise UserError."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'draft',
            'config_id': self.pos_config.id,
        })
        with self.assertRaises(UserError):
            booking.action_done()

    def test_16_action_prepare_payment(self):
        """Test action_prepare_payment returns correct POS order dictionary and raises on invalid state."""
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': fields.Date.today(),
            'state': 'draft',
            'amount_total': 60.0,
            'service_name': 'Facial Cleanse',
            'config_id': self.pos_config.id,
        })
        # Draft booking raises UserError
        with self.assertRaises(UserError):
            booking.action_prepare_payment()

        # Confirmed booking prepares payment lines
        booking.state = 'confirmed'
        res = booking.action_prepare_payment()
        self.assertEqual(res['partner_id'], self.customer_partner.id)
        self.assertTrue(res['lines'])
        self.assertAlmostEqual(res['lines'][0]['price'], 60.0)

        # Already paid raises UserError
        booking.payment_state = 'paid'
        with self.assertRaises(UserError):
            booking.action_prepare_payment()

        # Manual commission requires commission_amount > 0
        booking.payment_state = 'unpaid'
        self.pos_config.write({
            'apply_commission': True,
            'commission_type': 'manual',
        })
        booking.specialist_id = self.specialist_partner.id
        with self.assertRaises(UserError):
            booking.action_prepare_payment(commission_amount=0.0)

    def test_17_seat_assignment_and_availability(self):
        """Test seat allocation and availability checks when capacity is reached."""
        self.pos_config.salon_seats = 2
        today = fields.Date.today()
        slot_10am = json.dumps({'svc': ['10:00 AM']})

        # Booking 1 takes seat 1
        b1 = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': slot_10am,
            'state': 'confirmed',
            'config_id': self.pos_config.id,
        })
        b1._assign_seat()
        self.assertEqual(b1.seat_no, 1)

        # Booking 2 takes seat 2
        b2 = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': slot_10am,
            'state': 'confirmed',
            'config_id': self.pos_config.id,
        })
        b2._assign_seat()
        self.assertEqual(b2.seat_no, 2)

        # 3rd booking at 10:00 AM exceeds capacity -> _check_availability raises UserError
        with self.assertRaises(UserError):
            self.env['salon.booking']._check_availability({
                'config_id': self.pos_config.id,
                'date': today,
                'slot': slot_10am,
            })

        # get_unavailable_slots should include 10:00 AM
        busy_slots = self.env['salon.booking'].get_unavailable_slots(self.pos_config.id, today)
        self.assertIn('10:00 AM', busy_slots)

    def test_18_specialist_conflict(self):
        """Test that booking the same specialist in the same slot raises UserError."""
        today = fields.Date.today()
        slot_2pm = json.dumps({'svc': ['2:00 PM']})

        self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': slot_2pm,
            'specialist_id': self.specialist_partner.id,
            'state': 'confirmed',
            'config_id': self.pos_config.id,
        })

        # Attempt to book same specialist in same slot
        with self.assertRaises(UserError):
            self.env['salon.booking']._check_availability({
                'config_id': self.pos_config.id,
                'date': today,
                'slot': slot_2pm,
                'specialist_id': self.specialist_partner.id,
            })

    def test_19_get_walkin_plan(self):
        """Test get_walkin_plan logic during open hours and after closing."""
        today = fields.Date.today()
        plan = self.env['salon.booking'].get_walkin_plan(
            config_id=self.pos_config.id,
            date=today,
            duration=30,
            now_minute=660,  # 11:00 AM
        )
        self.assertEqual(plan['start'], '11:00 AM')
        self.assertIn('free_now', plan)
        self.assertIn('free_starts', plan)

        # After salon closing time (20:00 = 1200 mins), should raise UserError
        with self.assertRaises(UserError):
            self.env['salon.booking'].get_walkin_plan(
                config_id=self.pos_config.id,
                date=today,
                duration=30,
                now_minute=1230,  # 8:30 PM
            )

    def test_20_reschedule_options_and_reschedule_booking(self):
        """Test reschedule options generation and rescheduling an appointment."""
        today = fields.Date.today()
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': json.dumps({'svc': ['10:00 AM']}),
            'state': 'confirmed',
            'config_id': self.pos_config.id,
        })
        booking._assign_seat()

        # Get reschedule options
        options = self.env['salon.booking'].get_reschedule_options(booking.id, now_minute=600)
        self.assertTrue(options)

        # Reschedule to 11:00 AM
        res = self.env['salon.booking'].reschedule_booking(booking.id, '11:00 AM')
        self.assertTrue(res)
        self.assertIn('11:00 AM', booking.slot)

        # Arrived booking cannot be rescheduled
        booking.checked_in = True
        with self.assertRaises(UserError):
            self.env['salon.booking'].reschedule_booking(booking.id, '12:00 PM')

    def test_21_create_booking_walkin_rpc(self):
        """Test create_booking RPC method for walk-ins automatically checks in customer."""
        today = fields.Date.today()
        booking_id = self.env['salon.booking'].create_booking({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': 'Walk-in',
            'walkin_start': 600,
            'config_id': self.pos_config.id,
            'service_lines': json.dumps([{'name': 'Shampoo', 'price': 20.0, 'duration': '30 min'}]),
        })
        booking = self.env['salon.booking'].browse(booking_id)
        self.assertTrue(booking.checked_in)
        self.assertTrue(booking.checked_in_time)

    def test_22_create_booking_reschedule_services(self):
        """Test create_booking with reschedule moves services and handles paid services."""
        today = fields.Date.today()
        old_booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': json.dumps({'s1': ['10:00 AM']}),
            'state': 'confirmed',
            'payment_state': 'paid',
            'amount_total': 50.0,
            'config_id': self.pos_config.id,
            'service_lines': json.dumps([{
                'id': 'svc_cut',
                'name': 'Haircut',
                'price': 50.0,
                'duration': '30 min',
            }]),
        })

        new_booking_id = self.env['salon.booking'].create_booking({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': json.dumps({'svc_cut': ['2:00 PM']}),
            'config_id': self.pos_config.id,
            'service_lines': json.dumps([{
                'id': 'svc_cut',
                'name': 'Haircut',
                'price': 50.0,
                'duration': '30 min',
            }]),
        }, reschedule=[{
            'booking_id': old_booking.id,
            'service_id': 'svc_cut',
            'name': 'Haircut',
        }])

        new_booking = self.env['salon.booking'].browse(new_booking_id)
        # Because old service was paid, new line price is 0 and marked prepaid_from
        new_lines = new_booking._get_lines()
        self.assertEqual(new_lines[0]['price'], 0)
        self.assertEqual(new_lines[0]['prepaid_from'], old_booking.id)
        # Old booking state marked rescheduled
        self.assertEqual(old_booking.state, 'rescheduled')

    def test_23_get_customer_day_services_and_options(self):
        """Test get_customer_day_services and get_booking_options queries."""
        today = fields.Date.today()
        self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'slot': json.dumps({'s1': ['10:00 AM']}),
            'state': 'confirmed',
            'config_id': self.pos_config.id,
            'service_lines': json.dumps([{'name': 'Spa Bath', 'price': 30.0}]),
        })
        services = self.env['salon.booking'].get_customer_day_services(
            self.customer_partner.id, today)
        self.assertTrue(len(services) >= 1)
        self.assertEqual(services[0]['name'], 'Spa Bath')

        options = self.env['salon.booking'].get_booking_options(self.pos_config.id)
        self.assertTrue(options['specialists'])
        self.assertTrue(options['amenities'])

    def test_24_get_commission_data_permissions(self):
        """Test get_commission_data checks POS manager security group."""
        today = fields.Date.today()
        # Booking marked done and paid
        booking = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'state': 'done',
            'payment_state': 'paid',
            'amount_total': 100.0,
            'commission_amount': 10.0,
            'specialist_id': self.specialist_partner.id,
            'config_id': self.pos_config.id,
        })

        # Run as admin / pos manager
        data = self.env['salon.booking'].get_commission_data(self.pos_config.id, scope='all')
        self.assertTrue(data['allowed'])
        self.assertTrue(any(row['id'] == booking.id for row in data['rows']))

    def test_25_action_send_review_mail(self):
        """Test action_send_review_mail button validations."""
        today = fields.Date.today()
        # Non-done booking raises UserError
        booking_draft = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'state': 'draft',
            'config_id': self.pos_config.id,
        })
        with self.assertRaises(UserError):
            booking_draft.action_send_review_mail()

        # Done booking without customer email raises UserError
        booking_no_email = self.env['salon.booking'].create({
            'partner_id': self.customer_no_email.id,
            'date': today,
            'state': 'done',
            'config_id': self.pos_config.id,
        })
        with self.assertRaises(UserError):
            booking_no_email.action_send_review_mail()

        # Done booking with email generates review token
        booking_valid = self.env['salon.booking'].create({
            'partner_id': self.customer_partner.id,
            'date': today,
            'state': 'done',
            'config_id': self.pos_config.id,
        })
        booking_valid.action_send_review_mail()
        self.assertTrue(booking_valid.review_token)
        self.assertTrue(booking_valid.review_mail_sent)

        # Already reviewed booking raises UserError
        booking_valid.review_date = fields.Datetime.now()
        with self.assertRaises(UserError):
            booking_valid.action_send_review_mail()
