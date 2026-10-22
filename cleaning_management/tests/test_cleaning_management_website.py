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
class TestCleaningManagementWebsite(TransactionCase):
    """Test cases for cleaning.management.website model."""

    def setUp(self):
        super().setUp()
        customer = self.env['res.partner'].create({'name': 'Site Customer'})
        state = self.env['res.country.state'].create({
            'name': 'Site State', 'code': 'SS',
            'country_id': self.env.ref('base.us').id,
        })
        shift = self.env['cleaning.shift'].create({
            'shift_type': 'Morning Shift',
            'shift_time_from': 8.0,
            'shift_time_to': 16.0,
        })
        self.leader_emp = self.env['hr.employee'].create({'name': 'Leader'})
        leader_detail = self.env['employee.details'].create({
            'employee_name_id': self.leader_emp.id,
            'time_shift_id': shift.id,
        })
        self.team = self.env['cleaning.team'].create({
            'name': 'Site Team',
            'team_leader_id': leader_detail.id,
            'members_ids': [(6, 0, [leader_detail.id])],
            'duty_type': 'morning',
        })
        self.duty = self.env['cleaning.team.duty'].create({
            'team_id': self.team.id,
            'team_leader_id': self.leader_emp.id,
            'customer_id': customer.id,
            'location_state_id': state.id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
        })

    def test_get_team_details(self):
        """Teams and duties are returned for the website frontend."""
        result = self.env['cleaning.management.website'].get_team_details()
        team_entry = next(
            t for t in result['team_list'] if t['id'] == self.team.id)
        self.assertEqual(team_entry['name'], 'Site Team')
        self.assertEqual(team_entry['duty'], 'morning')
        duty_entry = next(
            d for d in result['duty'] if d['id'] == self.duty.id)
        self.assertEqual(duty_entry['team_id'], self.team.id)
        self.assertEqual(duty_entry['duty'], 'morning')