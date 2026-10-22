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


@tagged('post_install', '-at_install')
class TestCleaningTeamDuty(TransactionCase):
    """Test cases for cleaning.team.duty model."""

    def setUp(self):
        super().setUp()
        self.CleaningTeamDuty = self.env['cleaning.team.duty']

        self.customer = self.env['res.partner'].create({'name': 'Customer'})
        self.state = self.env['res.country.state'].create({
            'name': 'Duty State',
            'code': 'DS',
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
            'name': 'Duty Team',
            'team_leader_id': self.leader_detail.id,
            'members_ids': [(6, 0, [self.leader_detail.id])],
            'duty_type': 'morning',
        })
        self.booking = self.env['cleaning.booking'].create({
            'customer_name_id': self.customer.id,
            'address': 'Test Address',
            'building_type_id': self.env['building.type'].create(
                {'name': 'House'}).id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_team_id': self.team.id,
            'location_state_id': self.state.id,
            'unit_price': 50.0,
        })

    def _create_duty(self, **kwargs):
        vals = {
            'team_id': self.team.id,
            'team_leader_id': self.leader_emp.id,
            'customer_id': self.customer.id,
            'location_state_id': self.state.id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_id': self.booking.id,
        }
        vals.update(kwargs)
        return self.CleaningTeamDuty.create(vals)

    def test_create_duty(self):
        """Test creating a cleaning team duty."""
        duty = self._create_duty()
        self.assertEqual(duty.team_id, self.team)
        self.assertEqual(duty.state, 'draft')
        self.assertEqual(duty.customer_id, self.customer)

    def test_action_start(self):
        """Test starting cleaning sets start time."""
        duty = self._create_duty()
        self.assertFalse(duty.start_cleaning)
        duty.action_start()
        self.assertTrue(duty.start_cleaning)
        self.assertTrue(duty.start_time)

    def test_action_finish(self):
        """Test finishing cleaning sets end time and total hours."""
        duty = self._create_duty()
        duty.action_start()
        duty.action_finish()
        self.assertTrue(duty.end_cleaning)
        self.assertFalse(duty.inspection_boolean)
        self.assertTrue(duty.end_time)
        self.assertTrue(duty.cleaning_id.total_hour_of_working is not None)

    def test_action_finish_without_start(self):
        """Test that finishing without starting does nothing."""
        duty = self._create_duty()
        duty.action_finish()
        self.assertFalse(duty.end_cleaning)
        self.assertFalse(duty.end_time)

    def test_action_inspection(self):
        """Test inspection action opens inspection form with defaults."""
        duty = self._create_duty()
        action = duty.action_inspection()
        self.assertEqual(action['res_model'], 'cleaning.inspection')
        self.assertEqual(action['type'], 'ir.actions.act_window')
        self.assertEqual(action['context']['default_cleaning_team_duty_id'],
                         duty.id)

    def test_action_view_inspection(self):
        """Test view inspection smart button action."""
        duty = self._create_duty()
        action = duty.action_view_inspection()
        self.assertEqual(action['res_model'], 'cleaning.inspection')
        self.assertEqual(action['domain'],
                         [('cleaning_team_duty_id', '=', duty.id)])

    def test_inspection_count(self):
        """Test inspection count is computed correctly."""
        duty = self._create_duty()
        self.assertEqual(duty.inspection_count, 0)
        self.env['cleaning.inspection'].create({
            'inspector_name_id': self.env.user.id,
            'cleaning_id': self.booking.id,
            'inspection_date_and_time': date.today(),
            'cleaning_team_id': self.team.id,
            'cleaning_team_duty_id': duty.id,
        })
        duty.invalidate_recordset(['inspection_count'])
        self.assertEqual(duty.inspection_count, 1)

    def test_inspection_boolean_compute(self):
        """Test inspection boolean is based on inspection count."""
        duty = self._create_duty()
        self.assertFalse(duty.inspection_boolean)
        self.env['cleaning.inspection'].create({
            'inspector_name_id': self.env.user.id,
            'cleaning_id': self.booking.id,
            'inspection_date_and_time': date.today(),
            'cleaning_team_id': self.team.id,
            'cleaning_team_duty_id': duty.id,
        })
        duty.invalidate_recordset(['inspection_count', 'inspection_boolean'])
        self.assertTrue(duty.inspection_boolean)