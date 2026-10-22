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
from datetime import date, timedelta
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCleaningManagementDashboard(TransactionCase):
    """Test cases for cleaning.management.dashboard model."""

    def setUp(self):
        super().setUp()
        self.Dashboard = self.env['cleaning.management.dashboard']

        self.customer = self.env['res.partner'].create({'name': 'Dash Cust'})
        self.state = self.env['res.country.state'].create({
            'name': 'Dash State',
            'code': 'DH',
            'country_id': self.env.ref('base.us').id,
        })
        self.shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })
        self.leader_emp = self.env['hr.employee'].create({'name': 'Leader'})
        self.leader_detail = self.env['employee.details'].create({
            'employee_name_id': self.leader_emp.id,
            'time_shift_id': self.shift.id,
        })
        self.team = self.env['cleaning.team'].create({
            'name': 'Dash Team',
            'team_leader_id': self.leader_detail.id,
            'members_ids': [(6, 0, [self.leader_detail.id])],
            'duty_type': 'morning',
        })

    def _create_booking(self, state='draft', booking_date=None):
        return self.env['cleaning.booking'].create({
            'customer_name_id': self.customer.id,
            'address': 'Dash Address',
            'building_type_id': self.env['building.type'].create(
                {'name': f'House {state}'}).id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_team_id': self.team.id,
            'location_state_id': self.state.id,
            'unit_price': 50.0,
            'state': state,
            'booking_date': booking_date or date.today(),
        })

    def _create_inspection(self, state='draft'):
        booking = self._create_booking()
        duty = self.env['cleaning.team.duty'].create({
            'team_id': self.team.id,
            'customer_id': self.customer.id,
            'cleaning_id': booking.id,
            'cleaning_date': date.today(),
            'cleaning_time': 'morning',
        })
        return self.env['cleaning.inspection'].create({
            'inspector_name_id': self.env.user.id,
            'cleaning_id': booking.id,
            'inspection_date_and_time': date.today(),
            'cleaning_team_id': self.team.id,
            'cleaning_team_duty_id': duty.id,
            'state': state,
        })

    def test_get_dashboard_count(self):
        """Test dashboard count returns correct values."""
        before = self.Dashboard.get_dashboard_count()
        self._create_booking(state='booked')
        self._create_booking(state='draft')
        counts = self.Dashboard.get_dashboard_count()
        self.assertEqual(counts['bookings'], before['bookings'] + 1)
        self.assertGreaterEqual(counts['teams'], 1)
        self.assertEqual(counts['cleaned'], before['cleaned'])
        self.assertEqual(counts['dirty'], before['dirty'])

    def test_get_the_booking_year(self):
        """Test year-wise booking data."""
        self._create_booking(state='draft', booking_date=date.today())
        self._create_booking(state='booked', booking_date=date.today())
        result = self.Dashboard.get_the_booking_year()
        self.assertIn('Draft', result['total_booking_stage_year'])
        self.assertIn('Booked', result['total_booking_stage_year'])
        self.assertEqual(result['total_booking_stage_year'],
                         ['Draft', 'Booked', 'Cleaned', 'Cancelled'])
        self.assertEqual(result['total_booking_stage_draft_year'], 1)
        self.assertEqual(result['total_booking_stage_booked_year'], 1)

    def test_get_the_booking_month(self):
        """Test month-wise booking data."""
        self._create_booking(state='draft', booking_date=date.today())
        result = self.Dashboard.get_the_booking_month()
        self.assertEqual(result['total_booking_stage_draft_month'], 1)

    def test_get_the_booking_week(self):
        """Test week-wise booking data."""
        self._create_booking(state='booked', booking_date=date.today())
        result = self.Dashboard.get_the_booking_week()
        self.assertEqual(result['total_booking_stage_booked_week'], 1)

    def test_get_the_booking_quarter(self):
        """Test quarter-wise booking data."""
        self._create_booking(state='draft', booking_date=date.today())
        result = self.Dashboard.get_the_booking_quarter()
        self.assertEqual(result['total_booking_stage_draft_quarter'], 1)

    def test_quality_year(self):
        """Test year-wise quality data."""
        self._create_inspection(state='cleaned')
        result = self.Dashboard.quality_year()
        self.assertEqual(result['cleaned_quality_year'], 1)
        self.assertEqual(result['dirty_quality_year'], 0)

    def test_quality_month(self):
        """Test month-wise quality data (was uncovered)."""
        self._create_inspection(state='cleaned')
        result = self.Dashboard.quality_month()
        self.assertIn('Cleaned', result['quality_month'])
        self.assertEqual(result['cleaned_quality_month'], 1)
        self.assertEqual(result['dirty_quality_month'], 0)

    def test_quality_week(self):
        """Test week-wise quality data."""
        self._create_inspection(state='dirty')
        result = self.Dashboard.quality_week()
        self.assertEqual(result['dirty_quality_week'], 1)

    def test_quality_quarter(self):
        """Test quarter-wise quality data."""
        self._create_inspection(state='cleaned')
        result = self.Dashboard.quality_quarter()
        self.assertEqual(result['cleaned_quality_quarter'], 1)

    def test_cleaning_count(self):
        """Test cleaning_count returns bookings and inspections."""
        before = self.Dashboard.cleaning_count()
        self._create_inspection()
        result = self.Dashboard.cleaning_count()
        self.assertEqual(len(result['bookings']), len(before['bookings']) + 1)
        self.assertEqual(len(result['inspections']),
                         len(before['inspections']) + 1)