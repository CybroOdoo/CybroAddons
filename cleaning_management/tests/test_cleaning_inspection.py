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
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestCleaningInspection(TransactionCase):
    """Test cases for cleaning.inspection model."""

    def setUp(self):
        super().setUp()
        self.CleaningInspection = self.env['cleaning.inspection']

        self.customer = self.env['res.partner'].create({'name': 'Customer'})
        self.state = self.env['res.country.state'].create({
            'name': 'Inspection State',
            'code': 'IS',
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
            'name': 'Inspection Team',
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
        self.duty = self.env['cleaning.team.duty'].create({
            'team_id': self.team.id,
            'team_leader_id': self.leader_emp.id,
            'customer_id': self.customer.id,
            'location_state_id': self.state.id,
            'cleaning_date': date.today() + timedelta(days=1),
            'cleaning_time': 'morning',
            'cleaning_id': self.booking.id,
        })

    def _create_inspection(self, **kwargs):
        vals = {
            'inspector_name_id': self.env.user.id,
            'cleaning_id': self.booking.id,
            'inspection_date_and_time': date.today(),
            'cleaning_team_id': self.team.id,
            'cleaning_team_duty_id': self.duty.id,
        }
        vals.update(kwargs)
        return self.CleaningInspection.create(vals)

    def test_create_inspection_default_state(self):
        """Test new inspection defaults to draft state."""
        inspection = self._create_inspection()
        self.assertEqual(inspection.state, 'draft')
        self.assertFalse(inspection.dirty_clean)

    def test_inspection_required_fields(self):
        """Test required fields on inspection creation."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.CleaningInspection.create({})

    def test_action_clean(self):
        """Test clean action updates all related records."""
        inspection = self._create_inspection()
        inspection.action_clean()
        self.assertEqual(inspection.state, 'cleaned')
        self.assertTrue(inspection.dirty_clean)
        self.assertEqual(inspection.cleaning_id.state, 'cleaned')
        self.assertTrue(inspection.cleaning_id.clean_stage)
        self.assertEqual(inspection.cleaning_id.cleaning_inspection_id,
                         inspection)
        self.assertEqual(inspection.cleaning_team_duty_id.state, 'cleaned')

    def test_action_dirt(self):
        """Test dirty action updates inspection and duty."""
        inspection = self._create_inspection()
        inspection.action_dirt()
        self.assertEqual(inspection.state, 'dirty')
        self.assertTrue(inspection.dirty_clean)
        self.assertEqual(inspection.cleaning_team_duty_id.state, 'dirty')

    def test_action_reclean(self):
        """Test reclean action resets state to draft."""
        inspection = self._create_inspection()
        inspection.action_clean()
        self.assertEqual(inspection.state, 'cleaned')
        inspection.action_reclean()
        self.assertEqual(inspection.state, 'draft')

    def test_inspection_rec_name(self):
        """Test rec_name returns cleaning team."""
        inspection = self._create_inspection()
        self.assertEqual(inspection.display_name, self.team.display_name)

    def test_action_clean_restores_cancel_stage(self):
        """After booking, cancel_stage is False; cleaning restores it."""
        self.booking.action_booking()
        self.assertFalse(self.booking.cancel_stage)
        inspection = self._create_inspection()
        inspection.action_clean()
        self.assertTrue(self.booking.cancel_stage)