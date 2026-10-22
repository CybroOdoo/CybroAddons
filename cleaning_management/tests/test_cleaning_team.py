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
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestCleaningTeam(TransactionCase):
    """Test cases for cleaning.team model."""

    def setUp(self):
        super().setUp()
        self.CleaningTeam = self.env['cleaning.team']
        self.EmployeeDetails = self.env['employee.details']

        self.morning_shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })
        self.emp1 = self.env['hr.employee'].create({'name': 'Leader A'})
        self.emp2 = self.env['hr.employee'].create({'name': 'Member B'})
        self.emp3 = self.env['hr.employee'].create({'name': 'Member C'})

        self.leader_detail = self.EmployeeDetails.create({
            'employee_name_id': self.emp1.id,
            'time_shift_id': self.morning_shift.id,
        })
        self.member_detail1 = self.EmployeeDetails.create({
            'employee_name_id': self.emp2.id,
            'time_shift_id': self.morning_shift.id,
        })
        self.member_detail2 = self.EmployeeDetails.create({
            'employee_name_id': self.emp3.id,
            'time_shift_id': self.morning_shift.id,
        })

    def _create_team(self, name='Team Alpha', duty_type='morning'):
        return self.CleaningTeam.create({
            'name': name,
            'team_leader_id': self.leader_detail.id,
            'members_ids': [(6, 0, [self.member_detail1.id,
                                    self.member_detail2.id])],
            'duty_type': duty_type,
        })

    def test_create_team(self):
        """Test creating a cleaning team."""
        team = self._create_team()
        self.assertEqual(team.name, 'Team Alpha')
        self.assertEqual(team.team_leader_id, self.leader_detail)
        self.assertEqual(len(team.members_ids), 2)
        self.assertEqual(team.duty_type, 'morning')

    def test_team_name_unique_constraint(self):
        """Test that team names must be unique (models.Constraint)."""
        self._create_team(name='Unique Team')
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self._create_team(name='Unique Team')

    def test_team_required_fields(self):
        """Test required fields on team creation."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.CleaningTeam.create({'name': 'Incomplete'})
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.CleaningTeam.create({
                'name': 'No Leader',
                'duty_type': 'morning',
            })

    def test_onchange_team_leader_sets_member(self):
        """Test that setting team leader adds leader to members."""
        team = self.CleaningTeam.new({
            'name': 'Test Team',
            'team_leader_id': self.leader_detail.id,
            'duty_type': 'morning',
        })
        team._onchange_team_leader_or_duty_type()
        self.assertIn(self.leader_detail.id, team.members_ids.ids)

    def test_onchange_duty_type_filters_emp_details(self):
        """Test that duty type filters available employee details."""
        team = self.CleaningTeam.new({
            'name': 'Filter Team',
            'duty_type': 'morning',
        })
        team._onchange_team_leader_or_duty_type()
        self.assertIn(self.leader_detail.id, team.emp_detail_ids.ids)
        self.assertIn(self.member_detail1.id, team.emp_detail_ids.ids)

    def test_onchange_without_duty_type_loads_all_employees(self):
        """No duty type: every employee detail is available (else branch)."""
        team = self.CleaningTeam.new({'name': 'No Duty Team'})
        team._onchange_team_leader_or_duty_type()
        self.assertCountEqual(team.emp_detail_ids.ids,
                              self.EmployeeDetails.search([]).ids)