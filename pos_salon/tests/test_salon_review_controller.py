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
import re
from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install', 'pos_salon')
class TestSalonReviewController(HttpCase):
    """Test suite for SalonReviewController HTTP endpoints."""

    __test__ = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Review Test Customer',
            'email': 'review_customer@test.com',
            'phone': '+1987654321',
        })
        cls.specialist = cls.env['res.partner'].create({
            'name': 'Review Test Specialist',
            'email': 'review_specialist@test.com',
            'phone': '+1987654322',
        })
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Review Test POS Config',
            'is_salon': True,
            'take_review': True,
            'module_pos_restaurant': False,
        })
        cls.booking = cls.env['salon.booking'].create({
            'customer_name': cls.customer.name,
            'customer_phone': cls.customer.phone,
            'customer_email': cls.customer.email,
            'partner_id': cls.customer.id,
            'specialist_id': cls.specialist.id,
            'date': fields.Date.today(),
            'state': 'done',
            'config_id': cls.pos_config.id,
            'service_name': 'Spa Deluxe Service',
            'review_token': 'test_token_valid_12345',
        })

    def _extract_csrf(self, html_text):
        """Extract csrf_token from page HTML if present."""
        match = re.search(r'name="csrf_token"\s+value="([^"]+)"', html_text)
        return match.group(1) if match else ''

    def test_01_review_page_invalid_token(self):
        """Visiting review page with an invalid or expired token shows invalid template."""
        res = self.url_open('/salon/review/invalid_dummy_token_99999')
        self.assertEqual(res.status_code, 200)
        self.assertIn('Link not valid', res.text)

    def test_02_review_page_valid_token(self):
        """Visiting review page with valid token for completed booking displays review form."""
        res = self.url_open(f'/salon/review/{self.booking.review_token}')
        self.assertEqual(res.status_code, 200)
        self.assertIn('How was your visit?', res.text)
        self.assertIn('Spa Deluxe Service', res.text)

    def test_03_review_submit_valid(self):
        """Submitting a valid star rating and review note persists the feedback."""
        token = self.booking.review_token
        page_res = self.url_open(f'/salon/review/{token}')
        csrf_token = self._extract_csrf(page_res.text)

        submit_res = self.url_open(
            f'/salon/review/{token}/submit',
            data={
                'csrf_token': csrf_token,
                'rating': '5',
                'note': 'Fantastic service and ambiance!',
            },
        )
        self.assertEqual(submit_res.status_code, 200)

        # Refresh booking from database and verify review fields
        self.booking.invalidate_recordset()
        self.assertEqual(self.booking.rating, 5)
        self.assertEqual(self.booking.review_note, 'Fantastic service and ambiance!')
        self.assertTrue(self.booking.review_date)

    def test_04_review_submit_invalid_rating(self):
        """Submitting an out-of-range rating returns the form with an error message."""
        booking_invalid_test = self.env['salon.booking'].create({
            'partner_id': self.customer.id,
            'date': fields.Date.today(),
            'state': 'done',
            'config_id': self.pos_config.id,
            'review_token': 'token_rating_out_of_bounds',
        })
        token = booking_invalid_test.review_token
        page_res = self.url_open(f'/salon/review/{token}')
        csrf_token = self._extract_csrf(page_res.text)

        submit_res = self.url_open(
            f'/salon/review/{token}/submit',
            data={
                'csrf_token': csrf_token,
                'rating': '10',  # Invalid rating > 5
                'note': 'Invalid rating test',
            },
        )
        self.assertEqual(submit_res.status_code, 200)
        self.assertIn('Please choose a star rating', submit_res.text)

        booking_invalid_test.invalidate_recordset()
        self.assertEqual(booking_invalid_test.rating, 0)
        self.assertFalse(booking_invalid_test.review_date)

    def test_05_review_submit_already_reviewed(self):
        """Submitting a review when booking is already reviewed redirects without modifying."""
        token = self.booking.review_token
        # Obtain a valid session CSRF token while the form is rendered
        page_res = self.url_open(f'/salon/review/{token}')
        csrf_token = self._extract_csrf(page_res.text)

        # Now mark booking as already reviewed
        self.booking.write({
            'rating': 4,
            'review_note': 'Original review',
            'review_date': fields.Datetime.now(),
        })

        submit_res = self.url_open(
            f'/salon/review/{token}/submit',
            data={
                'csrf_token': csrf_token,
                'rating': '1',
                'note': 'Attempt to overwrite review',
            },
        )
        self.assertEqual(submit_res.status_code, 200)

        self.booking.invalidate_recordset()
        self.assertEqual(self.booking.rating, 4)
        self.assertEqual(self.booking.review_note, 'Original review')
