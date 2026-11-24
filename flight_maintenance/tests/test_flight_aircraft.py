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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFlightAircraft(TransactionCase):
    """Unit tests for flight.aircraft model extensions in flight_maintenance."""

    @classmethod
    def setUpClass(cls):
        """Set up test aircraft, equipment, stages, and metric test records."""
        super().setUpClass()
        cls.Aircraft = cls.env['flight.aircraft']
        cls.Metric = cls.env['flight.aircraft.metric']
        cls.Request = cls.env['maintenance.request']
        cls.Equipment = cls.env['maintenance.equipment']
        cls.Stage = cls.env['maintenance.stage']

        cls.stage_open = cls.Stage.search([('done', '=', False)], limit=1)
        if not cls.stage_open:
            cls.stage_open = cls.Stage.create({
                'name': 'Open Stage (Aircraft Test)',
                'done': False,
                'sequence': 1,
            })
        cls.stage_done = cls.Stage.search([('done', '=', True)], limit=1)
        if not cls.stage_done:
            cls.stage_done = cls.Stage.create({
                'name': 'Done Stage (Aircraft Test)',
                'done': True,
                'sequence': 99,
            })

        aircraft_vals = {'name': 'AC-TEST-001', 'status': 'active'}
        if 'model_id' in cls.Aircraft._fields:
            Model = cls.env.get('flight.aircraft.model')
            if Model is not None:
                model = Model.search([], limit=1)
                if not model and 'name' in Model._fields:
                    Make = cls.env.get('flight.aircraft.make')
                    make = False
                    if Make is not None:
                        make = Make.search([], limit=1)
                        if not make and 'name' in Make._fields:
                            make = Make.create({'name': 'Test Make'})
                    model_vals = {'name': 'Test Model'}
                    if make and 'make_id' in Model._fields:
                        model_vals['make_id'] = make.id
                    model = Model.create(model_vals)
                if model:
                    aircraft_vals['model_id'] = model.id

        cls.aircraft = cls.Aircraft.create(aircraft_vals)

    def test_01_aircraft_create_auto_syncs_equipment(self):
        """Creating an aircraft automatically creates and links a maintenance.equipment record."""
        self.assertTrue(
            self.aircraft.equipment_id,
            "Aircraft must have an equipment_id populated on creation.",
        )
        self.assertIn(
            self.aircraft.name,
            self.aircraft.equipment_id.name,
            "Linked equipment name should incorporate aircraft name.",
        )

    def test_02_aircraft_rename_updates_equipment_name(self):
        """Renaming an aircraft updates the linked maintenance.equipment record name."""
        equipment = self.aircraft.equipment_id
        self.aircraft.write({'name': 'AC-TEST-RENAMED'})
        self.assertIn(
            'AC-TEST-RENAMED',
            equipment.name,
            "Renaming aircraft must synchronize equipment name.",
        )

    def test_03_aircraft_model_change_updates_equipment_name(self):
        """Changing aircraft model triggers equipment name synchronization."""
        Model = self.env.get('flight.aircraft.model')
        if Model is not None and 'name' in Model._fields:
            Make = self.env.get('flight.aircraft.make')
            make = False
            if Make is not None:
                make = Make.search([], limit=1)
                if not make and 'name' in Make._fields:
                    make = Make.create({'name': 'Airbus'})
            model_vals = {'name': 'Airbus A320'}
            if make and 'make_id' in Model._fields:
                model_vals['make_id'] = make.id
            new_model = Model.create(model_vals)
            self.aircraft.write({'model_id': new_model.id})
            self.assertIn(
                'Airbus A320',
                self.aircraft.equipment_id.name,
                "Changing aircraft model must update equipment name with new model.",
            )

    def test_04_aircraft_metric_totals_calculation(self):
        """Running totals on aircraft correctly aggregate all 4 metric types."""
        self.Metric.create([
            {
                'aircraft_id': self.aircraft.id,
                'metric_type': 'airframe_hours',
                'value': 10.5,
            },
            {
                'aircraft_id': self.aircraft.id,
                'metric_type': 'airframe_hours',
                'value': 4.5,
            },
            {
                'aircraft_id': self.aircraft.id,
                'metric_type': 'engine_hours',
                'value': 12.0,
            },
            {
                'aircraft_id': self.aircraft.id,
                'metric_type': 'cycles',
                'value': 5,
            },
            {
                'aircraft_id': self.aircraft.id,
                'metric_type': 'fuel_used',
                'value': 250.0,
            },
        ])
        self.aircraft.invalidate_recordset()
        self.assertAlmostEqual(self.aircraft.airframe_hours_total, 15.0)
        self.assertAlmostEqual(self.aircraft.engine_hours_total, 12.0)
        self.assertAlmostEqual(self.aircraft.cycles_total, 5.0)
        self.assertAlmostEqual(self.aircraft.fuel_used_total, 250.0)

    def test_05_aircraft_maintenance_request_count(self):
        """maintenance_request_count accurately reflects number of linked requests."""
        self.assertEqual(self.aircraft.maintenance_request_count, 0)
        self.Request.create({
            'name': 'Routine Inspection',
            'aircraft_id': self.aircraft.id,
            'equipment_id': self.aircraft.equipment_id.id,
            'stage_id': self.stage_open.id,
        })
        self.aircraft.invalidate_recordset()
        self.assertEqual(self.aircraft.maintenance_request_count, 1)

    def test_06_aircraft_action_view_maintenance_requests(self):
        """action_view_maintenance_requests returns act_window dictionary for aircraft requests."""
        action = self.aircraft.action_view_maintenance_requests()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'maintenance.request')
        self.assertIn(('aircraft_id', '=', self.aircraft.id), action.get('domain', []))
        self.assertEqual(action.get('context', {}).get('default_aircraft_id'), self.aircraft.id)
        self.assertTrue(action.get('context', {}).get('default_grounding'))

    def test_07_aircraft_grounding_status_workflow(self):
        """Aircraft transitions between active, maintenance, and preserves manual grounded."""
        self.assertEqual(self.aircraft.status, 'active')

        # 1. Open grounding request sets status to maintenance
        req = self.Request.create({
            'name': 'Grounded for Repair',
            'aircraft_id': self.aircraft.id,
            'stage_id': self.stage_open.id,
            'grounding': True,
        })
        self.assertEqual(self.aircraft.status, 'maintenance')

        # 2. Closing request restores status to active
        req.write({'stage_id': self.stage_done.id})
        self.assertEqual(self.aircraft.status, 'active')

        # 3. Non-grounding open request leaves status active
        self.Request.create({
            'name': 'Minor Defect (Non-grounding)',
            'aircraft_id': self.aircraft.id,
            'stage_id': self.stage_open.id,
            'grounding': False,
        })
        self.assertEqual(self.aircraft.status, 'active')

        # 4. Manual 'grounded' status is never overwritten by maintenance logic
        self.aircraft.write({'status': 'grounded'})
        self.Request.create({
            'name': 'Engine Check',
            'aircraft_id': self.aircraft.id,
            'stage_id': self.stage_open.id,
            'grounding': True,
        })
        self.assertEqual(self.aircraft.status, 'grounded')
