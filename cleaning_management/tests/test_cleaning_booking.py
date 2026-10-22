# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Safa KB(odoo@cybrosys.com)
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
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestCleaningBooking(TransactionCase):
    """Test cases for cleaning.booking model."""

    def setUp(self):
        super().setUp()
        self.CleaningBooking = self.env['cleaning.booking']

        self.customer = self.env['res.partner'].create({
            'name': 'John Doe',
        })
        self.building_type = self.env['building.type'].create({
            'name': 'Apartment',
        })
        self.state = self.env['res.country.state'].create({
            'name': 'Test State',
            'code': 'TS',
            'country_id': self.env.ref('base.us').id,
        })

        self.morning_shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })
        self.leader_emp = self.env['hr.employee'].create({'name': 'Leader'})
        self.leader_detail = self.env['employee.details'].create({
            'employee_name_id': self.leader_emp.id,
            'time_shift_id': self.morning_shift.id,
        })
        self.team = self.env['cleaning.team'].create({
            'name': 'Booking Team',
            'team_leader_id': self.leader_detail.id,
            'members_ids': [(6, 0, [self.leader_detail.id])],
            'duty_type': 'morning',
        })

    def _create_booking(self, **kwargs):
        vals = {
            'customer_name_id': self.customer.id,
            'address': '123 Test Street',
            'building_type_id': self.building_type.id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_team_id': self.team.id,
            'location_state_id': self.state.id,
            'unit_price': 50.0,
        }
        vals.update(kwargs)
        return self.CleaningBooking.create(vals)

    def test_create_booking_default_state(self):
        """Test new booking defaults to draft state."""
        booking = self._create_booking()
        self.assertEqual(booking.state, 'draft')
        self.assertTrue(booking.confirm_stage)
        self.assertTrue(booking.clean_stage)
        self.assertTrue(booking.cancel_stage)

    def test_booking_required_fields(self):
        """Test required fields on booking creation."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.CleaningBooking.create({})

    def test_action_booking(self):
        """Test confirm action creates duty and changes state."""
        booking = self._create_booking()
        booking.action_booking()
        self.assertEqual(booking.state, 'booked')
        self.assertFalse(booking.confirm_stage)
        self.assertFalse(booking.clean_stage)
        self.assertFalse(booking.cancel_stage)
        self.assertTrue(booking.cleaning_team_duty_id)
        self.assertEqual(booking.cleaning_team_duty_id.team_id, self.team)
        self.assertEqual(booking.cleaning_team_duty_id.customer_id,
                         self.customer)
        # duty members are hr.employee records, not employee.details
        self.assertEqual(booking.cleaning_team_duty_id.members_ids,
                         self.team.members_ids.employee_name_id)
        self.assertEqual(booking.cleaning_team_duty_id.team_leader_id,
                         self.leader_emp)

    def test_action_cancel(self):
        """Test cancel action changes state and duty state."""
        booking = self._create_booking()
        booking.action_booking()
        booking.action_cancel()
        self.assertEqual(booking.state, 'cancelled')
        self.assertFalse(booking.confirm_stage)
        self.assertTrue(booking.cancel_stage)
        self.assertTrue(booking.clean_stage)
        self.assertEqual(booking.cleaning_team_duty_id.state, 'cancelled')

    def test_action_create_invoice_without_unit_price(self):
        """Test invoice creation fails when unit price is zero."""
        booking = self._create_booking(unit_price=0.0)
        with self.assertRaises(ValidationError):
            booking.action_create_invoice()

    def test_action_create_invoice(self):
        """Test invoice creation with valid unit price."""
        booking = self._create_booking(unit_price=100.0)
        booking.total_hour_of_working = '2'
        action = booking.action_create_invoice()
        self.assertEqual(action['res_model'], 'account.move')
        invoice = self.env['account.move'].browse(action['res_id'])
        self.assertEqual(invoice.move_type, 'out_invoice')
        self.assertEqual(invoice.partner_id, self.customer)
        self.assertEqual(invoice.cleaning_id, booking)
        self.assertEqual(invoice.invoice_line_ids[0].price_unit, 200.0)

    def test_compute_invoice_count(self):
        """Test invoice count computation."""
        booking = self._create_booking(unit_price=100.0)
        booking.total_hour_of_working = '1'
        self.assertEqual(booking.invoice_count, 0)
        booking.action_create_invoice()
        booking.invalidate_recordset(['invoice_count'])
        self.assertEqual(booking.invoice_count, 1)

    def test_action_view_invoice(self):
        """Test invoice smart button action."""
        booking = self._create_booking()
        action = booking.action_view_invoice()
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['res_model'], 'account.move')
        self.assertEqual(action['domain'], [('cleaning_id', '=', booking.id)])

    def test_onchange_cleaning_time_filters_teams(self):
        """Test that selecting cleaning time filters available teams."""
        booking = self.CleaningBooking.new({
            'customer_name_id': self.customer.id,
            'address': 'Test',
            'building_type_id': self.building_type.id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'location_state_id': self.state.id,
            'unit_price': 50.0,
        })
        booking._onchange_cleaning_time()
        self.assertIn(self.team.id, booking.cleaning_team_ids.ids)

    def test_onchange_cleaning_team_id(self):
        """Test that selecting team updates cleaning time."""
        booking = self.CleaningBooking.new({
            'cleaning_team_id': self.team.id,
        })
        booking._onchange_cleaning_team_id()
        self.assertEqual(booking.cleaning_time, 'morning')

    def test_onchange_cleaning_time_excludes_busy_teams(self):
        """A team with an open duty on the same date and time is excluded."""
        booking = self._create_booking()
        booking.action_booking()
        new_booking = self.CleaningBooking.new({
            'cleaning_date': booking.cleaning_date,
            'cleaning_time': 'morning',
        })
        new_booking._onchange_cleaning_time()
        self.assertNotIn(self.team.id, new_booking.cleaning_team_ids.ids)

    def test_booking_date_default_is_today(self):
        """The default must be evaluated on each create, not at import."""
        booking = self._create_booking()
        self.assertEqual(booking.booking_date, date.today())