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
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestFlightManagementCommon(TransactionCase):
    """Common setup shared by all Flight Management test cases."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # NOTE: names/codes are deliberately distinct from the values used in
        # demo/flight_management_demo.xml (e.g. 'Narrow Body'/'NB', 'Boeing',
        # 'KLAX', 'KJFK') since demo data is loaded before tests run and would
        # otherwise collide with the unique constraints on these models.
        cls.aircraft_class = cls.env['flight.aircraft.class'].create({
            'name': 'Test Wide Body',
            'code': 'TWB',
        })
        cls.make = cls.env['flight.aircraft.make'].create({
            'name': 'Test Airbus',
            'code': 'TAIR',
        })
        cls.model = cls.env['flight.aircraft.model'].create({
            'name': 'Test A320',
            'code': 'TA320',
            'make_id': cls.make.id,
            'class_id': cls.aircraft_class.id,
            'default_capacity': 180,
        })
        cls.aircraft = cls.env['flight.aircraft'].create({
            'name': 'TEST-REG-001',
            'code': 'TAC001',
            'model_id': cls.model.id,
            'capacity': 180,
        })
        cls.origin = cls.env['flight.aerodrome'].create({
            'name': 'Test Kennedy International',
            'icao_code': 'ZZJK',
            'iata_code': 'ZJK',
            'city': 'Test New York',
        })
        cls.destination = cls.env['flight.aerodrome'].create({
            'name': 'Test Angeles International',
            'icao_code': 'ZZLX',
            'iata_code': 'ZLX',
            'city': 'Test Los Angeles',
        })

    def _create_flight(self, **overrides):
        departure = fields.Datetime.now() + timedelta(days=1)
        vals = {
            'origin_id': self.origin.id,
            'destination_id': self.destination.id,
            'scheduled_departure': departure,
            'scheduled_arrival': departure + timedelta(hours=6),
            'aircraft_id': self.aircraft.id,
        }
        vals.update(overrides)
        return self.env['flight.flight'].create(vals)


class TestFlightAircraftClass(TestFlightManagementCommon):

    def test_name_unique_constraint(self):
        """Two aircraft classes cannot share the same name."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['flight.aircraft.class'].create({'name': 'Test Wide Body'})


class TestFlightAircraftMake(TestFlightManagementCommon):

    def test_name_unique_constraint(self):
        """Two manufacturers cannot share the same name."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['flight.aircraft.make'].create({'name': 'Test Airbus'})

    def test_model_ids_reverse_relation(self):
        """model_ids should reflect models created against the manufacturer."""
        self.assertIn(self.model, self.make.model_ids)


class TestFlightAircraftModel(TestFlightManagementCommon):

    def test_make_id_required(self):
        """A model cannot be created without a manufacturer."""
        with self.assertRaises(Exception):
            self.env['flight.aircraft.model'].create({'name': 'A321'})

    def test_name_make_unique_constraint(self):
        """The same model name cannot repeat under the same manufacturer."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['flight.aircraft.model'].create({
                'name': 'Test A320',
                'make_id': self.make.id,
            })

    def test_same_name_different_make_allowed(self):
        """The same model name is allowed under a different manufacturer."""
        other_make = self.env['flight.aircraft.make'].create({'name': 'Test Boeing'})
        model = self.env['flight.aircraft.model'].create({
            'name': 'Test A320',
            'make_id': other_make.id,
        })
        self.assertEqual(model.name, 'Test A320')

    def test_display_name_computation(self):
        """display_name should combine manufacturer and model name."""
        self.assertEqual(self.model.display_name, 'Test Airbus Test A320')


class TestFlightAerodrome(TestFlightManagementCommon):

    def test_icao_code_unique_constraint(self):
        """Two aerodromes cannot share the same ICAO code."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['flight.aerodrome'].create({
                'name': 'Duplicate Airport',
                'icao_code': 'ZZJK',
            })

    def test_display_name_with_icao_code(self):
        """display_name should be prefixed with the ICAO code when present."""
        self.assertEqual(self.origin.display_name, '[ZZJK] Test Kennedy International')

    def test_display_name_without_icao_code(self):
        """display_name should fall back to the plain name without an ICAO code."""
        aerodrome = self.env['flight.aerodrome'].create({'name': 'Unnamed Strip'})
        self.assertEqual(aerodrome.display_name, 'Unnamed Strip')

    def test_display_name_recomputes_on_icao_change(self):
        """display_name should update when the ICAO code changes later."""
        aerodrome = self.env['flight.aerodrome'].create({'name': 'Test Field'})
        aerodrome.icao_code = 'ZZZQ'
        self.assertEqual(aerodrome.display_name, '[ZZZQ] Test Field')


class TestFlightAircraft(TestFlightManagementCommon):

    def test_related_make_and_class_stored(self):
        """make_id and class_id should follow the selected aircraft model."""
        self.assertEqual(self.aircraft.make_id, self.make)
        self.assertEqual(self.aircraft.class_id, self.aircraft_class)

    def test_related_fields_update_when_model_changes(self):
        """Changing model_id should recompute the stored related fields."""
        other_make = self.env['flight.aircraft.make'].create({'name': 'Test Boeing'})
        other_class = self.env['flight.aircraft.class'].create({'name': 'Test Narrow Body'})
        other_model = self.env['flight.aircraft.model'].create({
            'name': 'Test 777',
            'make_id': other_make.id,
            'class_id': other_class.id,
        })
        self.aircraft.model_id = other_model
        self.assertEqual(self.aircraft.make_id, other_make)
        self.assertEqual(self.aircraft.class_id, other_class)

    def test_name_unique_constraint(self):
        """Two aircraft cannot share the same tail number."""
        with mute_logger('odoo.sql_db'), self.assertRaises(Exception):
            self.env['flight.aircraft'].create({
                'name': 'TEST-REG-001',
                'model_id': self.model.id,
            })

    def test_duplicate_code_raises_validation_error(self):
        """create() should reject a duplicate internal code with a clear error."""
        with self.assertRaises(ValidationError):
            self.env['flight.aircraft'].create({
                'name': 'TEST-REG-002',
                'code': 'TAC001',
                'model_id': self.model.id,
            })

    def test_default_status_is_active(self):
        """A newly created aircraft should default to the active status."""
        aircraft = self.env['flight.aircraft'].create({
            'name': 'TEST-REG-003',
            'model_id': self.model.id,
        })
        self.assertEqual(aircraft.status, 'active')


class TestFlightFlight(TestFlightManagementCommon):

    def test_flight_number_sequence_assigned(self):
        """A flight number should be generated from the ir.sequence on create."""
        flight = self._create_flight()
        self.assertTrue(flight.name)
        self.assertNotEqual(flight.name, 'New')

    def test_default_state_is_draft(self):
        """A newly created flight should start in the draft state."""
        flight = self._create_flight()
        self.assertEqual(flight.state, 'draft')

    def test_origin_destination_must_differ(self):
        """Origin and destination cannot be the same aerodrome."""
        with self.assertRaises(ValidationError):
            self._create_flight(destination_id=self.origin.id)

    def test_scheduled_arrival_after_departure(self):
        """Scheduled arrival earlier than departure should be rejected."""
        departure = fields.Datetime.now() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self._create_flight(
                scheduled_departure=departure,
                scheduled_arrival=departure - timedelta(hours=1),
            )

    def test_scheduled_arrival_equal_departure_rejected(self):
        """Scheduled arrival equal to departure should also be rejected."""
        departure = fields.Datetime.now() + timedelta(days=1)
        with self.assertRaises(ValidationError):
            self._create_flight(
                scheduled_departure=departure,
                scheduled_arrival=departure,
            )

    def test_full_lifecycle_happy_path(self):
        """A flight should progress through the full lifecycle without errors."""
        flight = self._create_flight()

        flight.action_confirm_schedule()
        self.assertEqual(flight.state, 'scheduled')

        flight.action_dispatch()
        self.assertEqual(flight.state, 'dispatched')

        flight.action_start()
        self.assertEqual(flight.state, 'in_progress')
        self.assertTrue(flight.actual_departure)

        flight.action_complete()
        self.assertEqual(flight.state, 'completed')
        self.assertTrue(flight.actual_arrival)

    def test_cancel_from_scheduled(self):
        """A scheduled flight should be cancellable."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        flight.action_cancel()
        self.assertEqual(flight.state, 'cancelled')

    def test_cancelled_flight_cannot_be_cancelled_again(self):
        """Cancelling an already cancelled flight should raise an error."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        flight.action_cancel()
        with self.assertRaises(ValidationError):
            flight.action_cancel()

    def test_completed_flight_cannot_be_cancelled(self):
        """A completed flight should not be cancellable."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        flight.action_dispatch()
        flight.action_start()
        flight.action_complete()
        with self.assertRaises(ValidationError):
            flight.action_cancel()

    def test_reset_to_draft(self):
        """action_reset_to_draft should return a flight to the draft state."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        flight.action_reset_to_draft()
        self.assertEqual(flight.state, 'draft')

    def test_confirm_schedule_requires_draft_state(self):
        """Scheduling a flight that is not in draft should raise an error."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        with self.assertRaises(ValidationError):
            flight.action_confirm_schedule()

    def test_confirm_schedule_requires_aircraft(self):
        """Scheduling a flight without an assigned aircraft should be rejected."""
        flight = self._create_flight(aircraft_id=False)
        with self.assertRaises(ValidationError):
            flight.action_confirm_schedule()

    def test_dispatch_requires_scheduled_state(self):
        """Dispatching a draft flight (skipping scheduling) should raise an error."""
        flight = self._create_flight()
        with self.assertRaises(ValidationError):
            flight.action_dispatch()

    def test_dispatch_requires_active_aircraft(self):
        """An aircraft that is not active should block dispatch."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        self.aircraft.status = 'maintenance'
        with self.assertRaises(ValidationError):
            flight.action_dispatch()

    def test_start_requires_dispatched_state(self):
        """Starting a flight that has not been dispatched should raise an error."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        with self.assertRaises(ValidationError):
            flight.action_start()

    def test_complete_requires_in_progress_state(self):
        """Completing a flight that is not in progress should raise an error."""
        flight = self._create_flight()
        flight.action_confirm_schedule()
        flight.action_dispatch()
        with self.assertRaises(ValidationError):
            flight.action_complete()


class TestFlightEvent(TestFlightManagementCommon):

    def test_event_creation(self):
        """A flight event should be linked to its parent flight."""
        flight = self._create_flight()
        event = self.env['flight.event'].create({
            'flight_id': flight.id,
            'event_type': 'takeoff',
            'timestamp': fields.Datetime.now(),
        })
        self.assertIn(event, flight.event_ids)

    def test_event_requires_flight(self):
        """A flight event cannot be created without a parent flight."""
        with self.assertRaises(Exception):
            self.env['flight.event'].create({
                'event_type': 'takeoff',
                'timestamp': fields.Datetime.now(),
            })

    def test_event_cascade_delete_with_flight(self):
        """Deleting a flight should cascade-delete its events."""
        flight = self._create_flight()
        event = self.env['flight.event'].create({
            'flight_id': flight.id,
            'event_type': 'landing',
            'timestamp': fields.Datetime.now(),
        })
        flight.unlink()
        self.assertFalse(event.exists())

    def test_events_ordered_by_timestamp(self):
        """Flight events should be returned ordered by timestamp ascending."""
        flight = self._create_flight()
        now = fields.Datetime.now()
        second = self.env['flight.event'].create({
            'flight_id': flight.id,
            'event_type': 'landing',
            'timestamp': now + timedelta(hours=1),
        })
        first = self.env['flight.event'].create({
            'flight_id': flight.id,
            'event_type': 'takeoff',
            'timestamp': now,
        })
        events = self.env['flight.event'].search([('flight_id', '=', flight.id)])
        self.assertEqual(list(events), [first, second])