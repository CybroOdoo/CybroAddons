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
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestSalonControllers(HttpCase):
    """Website booking routes, called as an anonymous (public) visitor."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        cls.stage_draft = env.ref('salon_management.salon_stage_00')
        cls.stage_open = env.ref('salon_management.salon_stage_01')
        cls.stage_cancel = env.ref('salon_management.salon_stage_04')
        cls.chair = env['salon.chair'].sudo().create({
            'date': datetime(2031, 3, 10), 'active_booking_chairs': True})
        cls.hidden_chair = env['salon.chair'].sudo().create({
            'date': datetime(2031, 3, 10), 'active_booking_chairs': False})
        cls.service = env['salon.service'].create(
            {'name': 'Web Cut', 'price': 40.0, 'time_taken': 1.0})
        cls.service2 = env['salon.service'].create(
            {'name': 'Web Wash', 'price': 20.0, 'time_taken': 0.5})

    def _rpc(self, route, params):
        response = self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': params}),
            headers={'Content-Type': 'application/json'})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertNotIn('error', body, body.get('error'))
        return body['result']

    def _booking_params(self, **kw):
        params = {
            'name': 'Web Customer', 'date': '2031-05-12',
            'salon_time': '10:00', 'phone': '555', 'email': 'w@example.com',
            'chair': self.chair.id,
            'service_list': [self.service.id, self.service2.id],
            'tz': 'Asia/Kolkata',
        }
        params.update(kw)
        return params

    # ------------------------------------------------------------------
    # /page/salon_details
    # ------------------------------------------------------------------
    def test_salon_details_creates_booking_in_utc(self):
        result = self._rpc('/page/salon_details', self._booking_params())
        self.assertEqual(result, {'result': True})
        booking = self.env['salon.booking'].search(
            [('name', '=', 'Web Customer')])
        self.assertEqual(len(booking), 1)
        # 10:00 in Asia/Kolkata (UTC+5:30) is 04:30 UTC
        self.assertEqual(booking.time, datetime(2031, 5, 12, 4, 30))
        self.assertEqual(booking.chair_id, self.chair)
        self.assertEqual(booking.service_ids, self.service | self.service2)
        self.assertEqual(booking.state, 'draft')
        self.assertEqual(booking.phone, '555')
        self.assertEqual(booking.email, 'w@example.com')

    def test_salon_details_without_timezone_uses_utc(self):
        self._rpc('/page/salon_details',
                  self._booking_params(tz=None, name='UTC Customer'))
        booking = self.env['salon.booking'].search(
            [('name', '=', 'UTC Customer')])
        self.assertEqual(booking.time, datetime(2031, 5, 12, 10, 0))

    def test_salon_details_invalid_timezone_falls_back(self):
        self._rpc('/page/salon_details',
                  self._booking_params(tz='Mars/Olympus', name='Bad TZ'))
        booking = self.env['salon.booking'].search([('name', '=', 'Bad TZ')])
        self.assertEqual(booking.time, datetime(2031, 5, 12, 10, 0))

    def test_salon_details_invalid_date(self):
        result = self._rpc('/page/salon_details',
                           self._booking_params(date='not-a-date'))
        self.assertFalse(result['result'])
        self.assertIn('valid date and time', result['error'])
        self.assertFalse(self.env['salon.booking'].search(
            [('name', '=', 'Web Customer')]))

    def test_salon_details_chair_conflict(self):
        self.assertTrue(self._rpc(
            '/page/salon_details', self._booking_params())['result'])
        result = self._rpc('/page/salon_details', self._booking_params(
            name='Second Customer'))
        self.assertFalse(result['result'])
        self.assertIn('already', result['error'])
        self.assertFalse(self.env['salon.booking'].search(
            [('name', '=', 'Second Customer')]))

    def test_salon_details_unexpected_error(self):
        model_cls = type(self.env['salon.booking'])
        with patch.object(model_cls, 'create',
                          side_effect=Exception("boom")):
            result = self._rpc('/page/salon_details',
                               self._booking_params())
        self.assertFalse(result['result'])
        self.assertIn("couldn't submit", result['error'])

    # ------------------------------------------------------------------
    # /page/salon_check_date
    # ------------------------------------------------------------------
    def _make_order(self, chair, start, stage=None):
        order = self.env['salon.order'].create({
            'customer_name': 'Existing', 'chair_id': chair.id,
            'start_time': start,
            'order_line_ids': [(0, 0, {
                'service_id': self.service.id, 'price': 40.0,
                'price_subtotal': 40.0, 'time_taken': 1.0})],
        })
        if stage:
            order.stage_id = stage
        return order

    def test_salon_check_date(self):
        # 10:00 IST == 04:30 UTC, lasts one hour
        order = self._make_order(self.chair, datetime(2031, 5, 12, 4, 30))
        self._make_order(self.chair, datetime(2031, 5, 13, 4, 30))  # other day
        self._make_order(self.hidden_chair, datetime(2031, 5, 12, 4, 30))
        result = self._rpc('/page/salon_check_date', {
            'check_date': '2031-05-12', 'tz': 'Asia/Kolkata'})
        self.assertIn(str(self.chair.id), result)
        self.assertNotIn(str(self.hidden_chair.id), result)
        chair_data = result[str(self.chair.id)]
        self.assertEqual(chair_data['name'], self.chair.name)
        self.assertEqual(len(chair_data['orders']), 1)
        self.assertEqual(chair_data['orders'][0]['number'], order.id)
        self.assertEqual(chair_data['orders'][0]['start_time_only'], '10:00')
        self.assertEqual(chair_data['orders'][0]['end_time_only'], '11:00')

    def test_salon_check_date_ignores_cancelled(self):
        self._make_order(self.chair, datetime(2031, 5, 12, 4, 30),
                         stage=self.stage_cancel)
        result = self._rpc('/page/salon_check_date', {
            'check_date': '2031-05-12', 'tz': 'Asia/Kolkata'})
        self.assertEqual(result[str(self.chair.id)]['orders'], [])

    def test_salon_check_date_without_timezone(self):
        self._make_order(self.chair, datetime(2031, 5, 12, 4, 30))
        result = self._rpc('/page/salon_check_date',
                           {'check_date': '2031-05-12'})
        chair_data = result[str(self.chair.id)]
        self.assertEqual(chair_data['orders'][0]['start_time_only'], '04:30')

    # ------------------------------------------------------------------
    # website pages
    # ------------------------------------------------------------------
    def test_thank_you_page(self):
        response = self.url_open(
            '/page/salon_management/salon_booking_thank_you')
        self.assertEqual(response.status_code, 200)

    def test_booking_form_page(self):
        self._make_order(self.chair,
                         fields.Datetime.now() + timedelta(minutes=1))
        response = self.url_open('/salon_booking_form')
        self.assertEqual(response.status_code, 200)

    # ------------------------------------------------------------------
    # /salon/chairs (dashboard)
    # ------------------------------------------------------------------
    def test_get_salon_chair_requires_login(self):
        """Anonymous visitors must not get chair/revenue data."""
        response = self.url_open(
            '/salon/chairs',
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call',
                             'params': {}}),
            headers={'Content-Type': 'application/json'})
        self.assertIn('error', response.json())

    def test_get_salon_chair(self):
        order = self._make_order(self.chair, datetime(2031, 5, 12, 4, 30))
        order.action_confirm()
        self.env.ref('base.user_admin').group_ids |= self.env.ref(
            'salon_management.group_salon_manager')
        self.authenticate('admin', 'admin')
        chairs = self._rpc('/salon/chairs', {})
        by_id = {chair['id']: chair for chair in chairs}
        busy, idle = by_id[self.chair.id], by_id[self.hidden_chair.id]
        self.assertEqual(busy['name'], self.chair.name)
        self.assertEqual(busy['orders'], 1)
        self.assertTrue(busy['busy'])
        self.assertEqual(busy['stylist'], '')
        self.assertEqual(idle['orders'], 0)
        self.assertFalse(idle['busy'])
