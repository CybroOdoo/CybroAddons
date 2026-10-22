# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import re
from datetime import date, timedelta

from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestCleaningController(HttpCase):
    """Tests for CleaningRequest controller routes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({'name': 'Web Customer'})
        cls.building_type = cls.env['building.type'].create({'name': 'Web Apt'})
        cls.state = cls.env['res.country.state'].create({
            'name': 'Web State', 'code': 'WS',
            'country_id': cls.env.ref('base.us').id,
        })
        cls.shift = cls.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0, 'shift_time_to': 16.0,
        })
        cls.emp = cls.env['hr.employee'].create({'name': 'Web Leader'})
        cls.emp_detail = cls.env['employee.details'].create({
            'employee_name_id': cls.emp.id,
            'time_shift_id': cls.shift.id,
        })
        cls.morning_team = cls.env['cleaning.team'].create({
            'name': 'Web Morning Team',
            'team_leader_id': cls.emp_detail.id,
            'members_ids': [(6, 0, [cls.emp_detail.id])],
            'duty_type': 'morning',
        })
        cls.evening_team = cls.env['cleaning.team'].create({
            'name': 'Web Evening Team',
            'team_leader_id': cls.emp_detail.id,
            'members_ids': [(6, 0, [cls.emp_detail.id])],
            'duty_type': 'evening',
        })
        cls.tomorrow = date.today() + timedelta(days=1)

    # -------- helpers -------- #
    def _available_teams(self, cleaning_date, cleaning_time):
        return self.make_jsonrpc_request(
            '/cleaning/available_teams',
            {'cleaning_date': cleaning_date, 'cleaning_time': cleaning_time})

    def _csrf_token(self):
        """Read a CSRF token bound to the logged-in test session."""
        response = self.url_open('/cleaning/request/form')
        for pattern in (r'name="csrf_token"[^>]*value="([^"]+)"',
                        r'value="([^"]+)"[^>]*name="csrf_token"'):
            match = re.search(pattern, response.text)
            if match:
                return match.group(1)
        self.fail("No CSRF token found on the booking form")

    def _submit(self, **overrides):
        self.authenticate('admin', 'admin')
        data = {
            'customer_name_id': self.env.ref('base.partner_admin').id,
            'address': '99 Web Street',
            'building_type_id': self.building_type.id,
            'booking_date': str(date.today()),
            'cleaning_date': str(self.tomorrow),
            'cleaning_time': 'morning',
            'cleaning_team_id': self.morning_team.id,
            'location_state_id': self.state.id,
            'description': 'via web',
            'csrf_token': self._csrf_token(),
        }
        data.update(overrides)
        return self.url_open('/cleaning/request/form/submit', data=data)

    def _booking_count(self):
        return self.env['cleaning.booking'].search_count([])

    # ============ /cleaning/available_teams ============ #
    def test_available_teams_returns_free_teams(self):
        result = self._available_teams(str(self.tomorrow), 'morning')
        ids = [t['id'] for t in result]
        self.assertIn(self.morning_team.id, ids)
        self.assertNotIn(self.evening_team.id, ids)

    def test_available_teams_excludes_busy_team(self):
        self.env['cleaning.team.duty'].create({
            'team_id': self.morning_team.id,
            'team_leader_id': self.emp.id,
            'customer_id': self.customer.id,
            'location_state_id': self.state.id,
            'cleaning_date': self.tomorrow,
            'cleaning_time': 'morning',
            'state': 'draft',
        })
        result = self._available_teams(str(self.tomorrow), 'morning')
        self.assertNotIn(self.morning_team.id, [t['id'] for t in result])

    def test_available_teams_invalid_time_returns_empty(self):
        self.assertEqual(self._available_teams(str(self.tomorrow), 'noon'), [])

    def test_available_teams_missing_date_returns_empty(self):
        self.assertEqual(self._available_teams(None, 'morning'), [])

    def test_available_teams_malformed_date_returns_empty(self):
        self.assertEqual(self._available_teams('bad-date', 'morning'), [])

    # ============ /cleaning/request/form (GET) ============ #
    def test_request_form_requires_login(self):
        """Public visitor is redirected (do not follow the redirect)."""
        response = self.url_open('/cleaning/request/form',
                                 allow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 403))

    def test_request_form_renders_for_user(self):
        self.authenticate('admin', 'admin')
        response = self.url_open('/cleaning/request/form')
        self.assertEqual(response.status_code, 200)
        self.assertIn('customer_name_id', response.text)

    # ============ /cleaning/request/form/submit (POST) ============ #
    def test_submit_creates_booking(self):
        before = self._booking_count()
        response = self._submit()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before + 1)
        booking = self.env['cleaning.booking'].search(
            [], order='id desc', limit=1)
        self.assertEqual(booking.customer_name_id,
                         self.env.ref('base.partner_admin'))
        self.assertEqual(booking.cleaning_team_id, self.morning_team)
        self.assertEqual(booking.address, '99 Web Street')
        self.assertEqual(booking.cleaning_time, 'morning')

    def test_submit_missing_date_renders_error(self):
        before = self._booking_count()
        response = self._submit(cleaning_date='')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_malformed_date_renders_error(self):
        before = self._booking_count()
        response = self._submit(cleaning_date='garbage')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_missing_customer_renders_error(self):
        before = self._booking_count()
        response = self._submit(customer_name_id='')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_missing_required_fields_render_error(self):
        for field in ('address', 'building_type_id', 'cleaning_team_id',
                      'location_state_id'):
            with self.subTest(field=field):
                before = self._booking_count()
                response = self._submit(**{field: ''})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self._booking_count(), before)

    def test_submit_invalid_cleaning_time_renders_error(self):
        before = self._booking_count()
        response = self._submit(cleaning_time='noon')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_non_numeric_id_renders_error(self):
        before = self._booking_count()
        response = self._submit(customer_name_id='abc')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_for_another_customer_renders_error(self):
        """A user can only book for their own partner."""
        before = self._booking_count()
        response = self._submit(customer_name_id=self.customer.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self._booking_count(), before)

    def test_submit_requires_login(self):
        """Public visitors cannot create bookings."""
        before = self._booking_count()
        response = self.url_open('/cleaning/request/form/submit',
                                 data={'cleaning_date': str(self.tomorrow)},
                                 allow_redirects=False)
        self.assertIn(response.status_code, (302, 303, 400, 403))
        self.assertEqual(self._booking_count(), before)

    def test_form_only_lists_own_partner(self):
        """The customer dropdown must not expose other partners."""
        self.authenticate('admin', 'admin')
        response = self.url_open('/cleaning/request/form')
        self.assertNotIn('Web Customer', response.text)