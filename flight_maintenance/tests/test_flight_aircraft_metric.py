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
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestFlightAircraftMetric(TransactionCase):
    """Unit tests for flight.aircraft.metric model in flight_maintenance."""

    @classmethod
    def setUpClass(cls):
        """Set up test aircraft, model, and aerodromes for metric entries."""
        super().setUpClass()
        cls.Aircraft = cls.env['flight.aircraft']
        cls.Metric = cls.env['flight.aircraft.metric']
        cls.Flight = cls.env['flight.flight']
        cls.Aerodrome = cls.env['flight.aerodrome']

        aero_vals_a = {'name': 'Origin Aerodrome'}
        aero_vals_b = {'name': 'Dest Aerodrome'}
        for field_name, val_a, val_b in (
            ('icao_code', 'MO01', 'MD01'),
            ('iata_code', 'M01', 'M02'),
            ('code', 'MO01', 'MD01'),
        ):
            if field_name in cls.Aerodrome._fields:
                aero_vals_a[field_name] = val_a
                aero_vals_b[field_name] = val_b
        cls.origin = cls.Aerodrome.create(aero_vals_a)
        cls.dest = cls.Aerodrome.create(aero_vals_b)

        aircraft_vals = {'name': 'METRIC-TEST-AC', 'status': 'active'}
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
                            make = Make.create({'name': 'Metric Make'})
                    model_vals = {'name': 'Metric Model'}
                    if make and 'make_id' in Model._fields:
                        model_vals['make_id'] = make.id
                    model = Model.create(model_vals)
                if model:
                    aircraft_vals['model_id'] = model.id

        cls.aircraft = cls.Aircraft.create(aircraft_vals)

    def test_01_create_metric_all_types(self):
        """Creating metric records for each supported metric type succeeds."""
        for m_type in ('airframe_hours', 'engine_hours', 'cycles', 'fuel_used'):
            metric = self.Metric.create({
                'aircraft_id': self.aircraft.id,
                'metric_type': m_type,
                'value': 10.0,
                'notes': f'Test entry for {m_type}',
            })
            self.assertTrue(metric.id)
            self.assertEqual(metric.metric_type, m_type)
            self.assertEqual(metric.value, 10.0)
            self.assertTrue(metric.date)

    def test_02_negative_value_raises_validation_error(self):
        """Constraint _check_value raises ValidationError when value is negative."""
        with self.assertRaises(ValidationError):
            self.Metric.create({
                'aircraft_id': self.aircraft.id,
                'metric_type': 'airframe_hours',
                'value': -0.5,
            })

    def test_03_zero_value_allowed(self):
        """Zero metric value is accepted by the constraint."""
        metric = self.Metric.create({
            'aircraft_id': self.aircraft.id,
            'metric_type': 'cycles',
            'value': 0.0,
        })
        self.assertEqual(metric.value, 0.0)

    def test_04_metric_ordering(self):
        """Metric records default to descending date order."""
        now = fields.Datetime.now()
        m1 = self.Metric.create({
            'aircraft_id': self.aircraft.id,
            'metric_type': 'airframe_hours',
            'value': 1.0,
            'date': now - timedelta(days=2),
        })
        m2 = self.Metric.create({
            'aircraft_id': self.aircraft.id,
            'metric_type': 'airframe_hours',
            'value': 2.0,
            'date': now - timedelta(days=1),
        })
        metrics = self.Metric.search([('id', 'in', (m1.id, m2.id))])
        self.assertEqual(metrics[0], m2, "Newer date entry must be ordered first.")
        self.assertEqual(metrics[1], m1)
