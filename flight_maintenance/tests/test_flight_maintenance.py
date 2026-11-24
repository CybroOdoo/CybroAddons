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
from datetime import timedelta
from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFlightMaintenance(TransactionCase):
    """Integration test suite for end-to-end flight maintenance workflows."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment with aircraft, equipment, aerodromes, and stages."""
        super().setUpClass()
        cls.Aircraft = cls.env['flight.aircraft']
        cls.Metric = cls.env['flight.aircraft.metric']
        cls.Request = cls.env['maintenance.request']
        cls.Equipment = cls.env['maintenance.equipment']
        cls.Stage = cls.env['maintenance.stage']
        cls.Flight = cls.env['flight.flight']

        cls.stage_new = cls.Stage.search([('done', '=', False)], limit=1)
        if not cls.stage_new:
            cls.stage_new = cls.Stage.create({
                'name': 'New (Test)',
                'done': False,
                'sequence': 1,
            })
        cls.stage_done = cls.Stage.search([('done', '=', True)], limit=1)
        if not cls.stage_done:
            cls.stage_done = cls.Stage.create({
                'name': 'Done (Test)',
                'done': True,
                'sequence': 99,
            })

        Aerodrome = cls.env['flight.aerodrome']
        aero_vals_a = {'name': 'Test Origin Airport'}
        aero_vals_b = {'name': 'Test Destination Airport'}
        for field_name, value_a, value_b in (
            ('icao_code', 'TORG', 'TDES'),
            ('iata_code', 'TOA', 'TDA'),
            ('code', 'TORG', 'TDES'),
        ):
            if field_name in Aerodrome._fields:
                aero_vals_a[field_name] = value_a
                aero_vals_b[field_name] = value_b
        cls.aerodrome_origin = Aerodrome.create(aero_vals_a)
        cls.aerodrome_dest = Aerodrome.create(aero_vals_b)

        aircraft_vals = {'name': 'TEST-N123AB', 'status': 'active'}
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

    def _prepare_flight_vals(self, **extra):
        """Build valid flight.flight create values including required fields."""
        now = fields.Datetime.now()
        vals = {
            'aircraft_id': self.aircraft.id,
            'origin_id': self.aerodrome_origin.id,
            'destination_id': self.aerodrome_dest.id,
            'scheduled_departure': now + timedelta(hours=1),
            'scheduled_arrival': now + timedelta(hours=3),
        }
        if 'name' in self.Flight._fields and 'name' not in extra:
            vals['name'] = 'TEST-FLT-001'
        if 'destination_id' not in self.Flight._fields and 'dest_id' in self.Flight._fields:
            vals['dest_id'] = vals.pop('destination_id')
        vals.update(extra)
        return {k: v for k, v in vals.items() if k in self.Flight._fields}

    def test_end_to_end_flight_maintenance_cycle(self):
        """End-to-end integration: flight completion accumulates metrics and maintenance gates flight."""
        now = fields.Datetime.now()
        departure = now - timedelta(hours=3)
        arrival = now

        # 1. Complete a flight -> metrics accumulate
        flight = self.Flight.create(self._prepare_flight_vals(
            actual_departure=departure,
            actual_arrival=arrival,
        ))
        flight.write({'state': 'in_progress', 'actual_departure': departure, 'actual_arrival': arrival})
        flight.action_complete()

        self.aircraft.invalidate_recordset()
        self.assertAlmostEqual(self.aircraft.airframe_hours_total, 3.0, places=2)
        self.assertEqual(self.aircraft.cycles_total, 1.0)
        self.assertEqual(self.aircraft.status, 'active')

        # 2. Grounding maintenance request grounds aircraft
        req = self.Request.create({
            'name': 'Scheduled Airframe Overhaul',
            'aircraft_id': self.aircraft.id,
            'stage_id': self.stage_new.id,
            'grounding': True,
        })
        self.assertEqual(self.aircraft.status, 'maintenance')

        # 3. Completing maintenance restores active status
        req.write({'stage_id': self.stage_done.id})
        self.assertEqual(self.aircraft.status, 'active')
