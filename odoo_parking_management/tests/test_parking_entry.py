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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestParkingEntry(TransactionCase):
    """Test cases for the ParkingEntry model (models/parking_entry.py).
    Covers: create, _compute_duration, onchange_slot_type_id,
            action_check_in, action_check_out, action_register_payment.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Parking Partner',
            'phone': '9876543210',
            'email': 'parktest@example.com',
        })
        cls.location = cls.env['location.details'].create({
            'name': 'Test Location',
        })
        cls.slot_type = cls.env['slot.type'].create({
            'vehicle_type': 'Car',
            'code': 'CAR',
            'allowed_park_duration': 2.0,
        })
        cls.slot = cls.env['slot.details'].create({
            'code': 'S001',
            'name': 'Slot 1',
            'slot_type_id': cls.slot_type.id,
        })
        cls.fleet_brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })
        cls.fleet_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.fleet_brand.id,
        })
        cls.fleet_vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.fleet_model.id,
            'license_plate': 'KL01AB0001',
        })
        cls.vehicle = cls.env['vehicle.details'].create({
            'vehicle_name': 'Test Car',
            'vehicle_id': cls.fleet_vehicle.id,
            'partner_id': cls.partner.id,
            'number_plate': 'KL01AB0001',
            'ownership_type': 'outsider',
        })

    def _make_parking_entry(self, customer_type='public'):
        """Helper to create a parking entry with all required fields."""
        return self.env['parking.entry'].create({
            'partner_id': self.partner.id,
            'vehicle_id': self.vehicle.id,
            'slot_type_id': self.slot_type.id,
            'slot_id': self.slot.id,
            'location_id': self.location.id,
            'customer_type': customer_type,
            'parking_cost': 50.0,
        })

    def test_create_public_parking_entry(self):
        """Test create() assigns an ir.sequence name for public customer type
        and does not leave it as the default 'New'."""
        entry = self._make_parking_entry(customer_type='public')
        self.assertTrue(entry.name,
                        "Parking entry name should be set after create().")
        self.assertNotEqual(entry.name, 'New',
                            "Public entry name must not remain 'New'.")

    def test_create_private_parking_entry(self):
        """Test create() assigns an ir.sequence name for private customer type
        and does not leave it as the default 'New'."""
        entry = self._make_parking_entry(customer_type='private')
        self.assertTrue(entry.name,
                        "Parking entry name should be set after create().")
        self.assertNotEqual(entry.name, 'New',
                            "Private entry name must not remain 'New'.")

    def test_create_sets_default_state_draft(self):
        """Test create() leaves the state at the default 'draft' value."""
        entry = self._make_parking_entry()
        self.assertEqual(entry.state, 'draft',
                         "Newly created entry state should be 'draft'.")

    def test_compute_duration_after_check_in_and_check_out(self):
        """Test _compute_duration computes a non-negative duration once
        both check_in and check_out timestamps are present."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        self.assertGreaterEqual(
            entry.duration, 0,
            "_compute_duration should return a non-negative value.")

    def test_compute_duration_without_check_out(self):
        """Test _compute_duration returns 0/False when check_out is not set."""
        entry = self._make_parking_entry()
        self.assertFalse(
            entry.duration,
            "Duration should be 0/False when check_out has not been recorded.")

    def test_onchange_slot_type_id_returns_domain(self):
        """Test onchange_slot_type_id() returns a dict containing a 'domain'
        key that filters slot_id by the selected slot type."""
        entry = self._make_parking_entry()
        result = entry.onchange_slot_type_id()
        self.assertIsInstance(result, dict,
                              "onchange_slot_type_id must return a dict.")
        self.assertIn('domain', result,
                      "Return value must contain 'domain' key.")
        self.assertIn('slot_id', result['domain'],
                      "Domain must define a filter for 'slot_id'.")

    def test_onchange_slot_type_id_domain_filters_by_slot_type(self):
        """Test that the domain produced by onchange_slot_type_id() restricts
        slot_id to slots belonging to the current slot_type_id."""
        entry = self._make_parking_entry()
        result = entry.onchange_slot_type_id()
        domain = result['domain']['slot_id']
        # The domain should contain a condition on slot_type_id
        self.assertTrue(
            any('slot_type_id' in str(cond) for cond in domain),
            "Domain for slot_id must filter by slot_type_id.")

    def test_action_check_in_sets_state(self):
        """Test action_check_in() transitions state to 'check_in'."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        self.assertEqual(entry.state, 'check_in',
                         "State must be 'check_in' after action_check_in().")

    def test_action_check_in_sets_check_in_bool(self):
        """Test action_check_in() sets check_in_bool to True and
        check_out_bool to False."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        self.assertTrue(entry.check_in_bool,
                        "check_in_bool must be True after check-in.")
        self.assertFalse(entry.check_out_bool,
                         "check_out_bool must be False after check-in.")

    def test_action_check_in_records_timestamp(self):
        """Test action_check_in() records a non-null check_in datetime."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        self.assertTrue(entry.check_in,
                        "check_in datetime must be set after action_check_in().")

    def test_action_check_out_sets_state(self):
        """Test action_check_out() transitions state to 'check_out'."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        self.assertEqual(entry.state, 'check_out',
                         "State must be 'check_out' after action_check_out().")

    def test_action_check_out_sets_check_out_bool(self):
        """Test action_check_out() sets check_out_bool to True and
        check_in_bool to False."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        self.assertTrue(entry.check_out_bool,
                        "check_out_bool must be True after check-out.")
        self.assertFalse(entry.check_in_bool,
                         "check_in_bool must be False after check-out.")

    def test_action_check_out_records_timestamp(self):
        """Test action_check_out() records a non-null check_out datetime."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        self.assertTrue(entry.check_out,
                        "check_out datetime must be set after action_check_out().")

    def test_action_register_payment_returns_dict(self):
        """Test action_register_payment() returns a valid action dictionary."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        result = entry.action_register_payment()
        self.assertIsInstance(result, dict,
                              "action_register_payment must return a dict.")

    def test_action_register_payment_action_type(self):
        """Test action_register_payment() returns an ir.actions.act_window."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        result = entry.action_register_payment()
        self.assertEqual(result.get('type'), 'ir.actions.act_window',
                         "Action type must be 'ir.actions.act_window'.")

    def test_action_register_payment_target_model(self):
        """Test action_register_payment() targets the register.payment.wizard
        model."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        result = entry.action_register_payment()
        self.assertEqual(result.get('res_model'), 'register.payment.wizard',
                         "res_model must be 'register.payment.wizard'.")

    def test_action_register_payment_context_defaults(self):
        """Test action_register_payment() passes correct default values
        to the wizard context."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        result = entry.action_register_payment()
        ctx = result.get('context', {})
        self.assertEqual(ctx.get('default_partner_id'), self.partner.id,
                         "Wizard context must carry default_partner_id.")
        self.assertEqual(ctx.get('default_amount'), entry.parking_cost,
                         "Wizard context must carry default_amount.")
        self.assertEqual(ctx.get('default_ref'), entry.name,
                         "Wizard context must carry default_ref.")

    def test_action_register_payment_opens_in_new_target(self):
        """Test action_register_payment() opens the wizard in a new dialog."""
        entry = self._make_parking_entry()
        entry.action_check_in()
        entry.action_check_out()
        result = entry.action_register_payment()
        self.assertEqual(result.get('target'), 'new',
                         "Wizard must be opened with target='new'.")
