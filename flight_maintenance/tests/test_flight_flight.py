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
class TestFlightFlight(TransactionCase):
    """Unit tests for flight.flight action_complete override in flight_maintenance."""

    @classmethod
    def setUpClass(cls):
        """Set up aerodromes, model, aircraft, and flights for testing flight completion."""
        super().setUpClass()
        cls.Aircraft = cls.env['flight.aircraft']
        cls.Metric = cls.env['flight.aircraft.metric']
        cls.Flight = cls.env['flight.flight']
        cls.Aerodrome = cls.env['flight.aerodrome']

        aero_a = {'name': 'Origin Flt Test'}
        aero_b = {'name': 'Dest Flt Test'}
        for field_name, code_a, code_b in (
            ('icao_code', 'FO01', 'FD01'),
            ('iata_code', 'FO1', 'FD1'),
            ('code', 'FO01', 'FD01'),
        ):
            if field_name in cls.Aerodrome._fields:
                aero_a[field_name] = code_a
                aero_b[field_name] = code_b
        cls.origin = cls.Aerodrome.create(aero_a)
        cls.dest = cls.Aerodrome.create(aero_b)

        aircraft_vals = {'name': 'FLT-TEST-AC', 'status': 'active'}
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
                            make = Make.create({'name': 'Flight Make'})
                    model_vals = {'name': 'Flight Model'}
                    if make and 'make_id' in Model._fields:
                        model_vals['make_id'] = make.id
                    model = Model.create(model_vals)
                if model:
                    aircraft_vals['model_id'] = model.id

        cls.aircraft = cls.Aircraft.create(aircraft_vals)

    def _prepare_flight_vals(self, **extra):
        """Prepare valid flight.flight creation dictionary."""
        now = fields.Datetime.now()
        vals = {
            'aircraft_id': self.aircraft.id,
            'origin_id': self.origin.id,
            'destination_id': self.dest.id,
            'scheduled_departure': now - timedelta(hours=3),
            'scheduled_arrival': now - timedelta(hours=1),
        }
        if 'name' in self.Flight._fields and 'name' not in extra:
            vals['name'] = 'FLT-TEST-001'
        if 'destination_id' not in self.Flight._fields and 'dest_id' in self.Flight._fields:
            vals['dest_id'] = vals.pop('destination_id')
        vals.update(extra)
        return {k: v for k, v in vals.items() if k in self.Flight._fields}

    def test_01_action_complete_creates_airframe_hours_and_cycles(self):
        """Completing a flight with valid departure and arrival creates metric entries."""
        now = fields.Datetime.now()
        departure = now - timedelta(hours=2)
        arrival = now

        flight = self.Flight.create(self._prepare_flight_vals(
            name='FLT-COMPLETE-01',
            actual_departure=departure,
            actual_arrival=arrival,
        ))
        flight.write({'state': 'in_progress', 'actual_departure': departure, 'actual_arrival': arrival})

        metrics_count_before = self.Metric.search_count([('flight_id', '=', flight.id)])
        self.assertEqual(metrics_count_before, 0)

        flight.action_complete()

        metrics = self.Metric.search([('flight_id', '=', flight.id)])
        self.assertEqual(len(metrics), 2, "Flight completion must create exactly 2 metric entries.")

        airframe = metrics.filtered(lambda m: m.metric_type == 'airframe_hours')
        cycles = metrics.filtered(lambda m: m.metric_type == 'cycles')

        self.assertTrue(airframe)
        self.assertTrue(cycles)
        self.assertAlmostEqual(airframe.value, 2.0, places=2)
        self.assertEqual(cycles.value, 1.0)
        self.assertEqual(airframe.aircraft_id, self.aircraft)
        self.assertEqual(cycles.aircraft_id, self.aircraft)

    def test_02_action_complete_without_actual_times_skips_metrics(self):
        """Completing a flight without actual_departure/actual_arrival skips metric creation."""
        flight = self.Flight.create(self._prepare_flight_vals(name='FLT-NOTIMES-02'))
        write_vals = {'state': 'in_progress'}
        if 'actual_departure' in self.Flight._fields:
            write_vals['actual_departure'] = False
        if 'actual_arrival' in self.Flight._fields:
            write_vals['actual_arrival'] = False
        flight.write(write_vals)

        flight.action_complete()
        metrics = self.Metric.search([('flight_id', '=', flight.id)])
        self.assertEqual(len(metrics), 0, "No metrics should be created when actual times are missing.")

    def test_03_action_complete_negative_duration_skips_metrics(self):
        """Completing a flight where arrival <= departure skips metric creation."""
        now = fields.Datetime.now()
        departure = now + timedelta(hours=2)
        flight = self.Flight.create(self._prepare_flight_vals(
            name='FLT-NEGTIME-03',
            actual_departure=departure,
            actual_arrival=now,
        ))
        flight.write({
            'state': 'in_progress',
            'actual_departure': departure,
            'actual_arrival': now,
        })

        flight.action_complete()
        metrics = self.Metric.search([('flight_id', '=', flight.id)])
        self.assertEqual(len(metrics), 0, "Zero or negative duration must not log metrics.")

    def test_04_action_complete_without_aircraft_skips_metrics(self):
        """Completing a flight without an aircraft assigned skips metric creation."""
        now = fields.Datetime.now()
        flight = self.Flight.create(self._prepare_flight_vals(
            name='FLT-NOAC-04',
            aircraft_id=False,
            actual_departure=now - timedelta(hours=1),
            actual_arrival=now,
        ))
        flight.write({'state': 'in_progress', 'aircraft_id': False})

        flight.action_complete()
        metrics = self.Metric.search([('flight_id', '=', flight.id)])
        self.assertEqual(len(metrics), 0, "Flight without aircraft must not log metrics.")
