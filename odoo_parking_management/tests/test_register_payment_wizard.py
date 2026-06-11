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
class TestRegisterPaymentWizard(TransactionCase):
    """Test cases for the RegisterPaymentWizard transient model
    (wizard/register_payment.py).
    Covers: parking_payment.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Wizard Test Partner',
            'phone': '1122334455',
            'email': 'wizardtest@example.com',
        })
        cls.location = cls.env['location.details'].create({
            'name': 'Wizard Test Location',
        })
        cls.slot_type = cls.env['slot.type'].create({
            'vehicle_type': 'Bike',
            'code': 'BIKE',
            'allowed_park_duration': 1.0,
        })
        cls.slot = cls.env['slot.details'].create({
            'code': 'B001',
            'name': 'Bike Slot 1',
            'slot_type_id': cls.slot_type.id,
        })
        cls.fleet_brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Wizard Brand',
        })
        cls.fleet_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Wizard Model',
            'brand_id': cls.fleet_brand.id,
        })
        cls.fleet_vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.fleet_model.id,
            'license_plate': 'KL02WZ9999',
        })
        cls.vehicle = cls.env['vehicle.details'].create({
            'vehicle_name': 'Wizard Bike',
            'vehicle_id': cls.fleet_vehicle.id,
            'partner_id': cls.partner.id,
            'number_plate': 'KL02WZ9999',
            'ownership_type': 'outsider',
        })
        # Create and progress a parking entry to the check_out stage
        cls.parking_entry = cls.env['parking.entry'].create({
            'partner_id': cls.partner.id,
            'vehicle_id': cls.vehicle.id,
            'slot_type_id': cls.slot_type.id,
            'slot_id': cls.slot.id,
            'location_id': cls.location.id,
            'customer_type': 'public',
            'parking_cost': 100.0,
        })
        cls.parking_entry.action_check_in()
        cls.parking_entry.action_check_out()

    def _create_wizard(self):
        """Helper that creates a RegisterPaymentWizard with active_id context
        pointing to the shared parking entry."""
        return self.env['register.payment.wizard'].with_context(
            active_id=self.parking_entry.id
        ).create({
            'partner_id': self.partner.id,
            'parking_duration': self.parking_entry.duration,
            'amount': self.parking_entry.parking_cost,
            'ref': self.parking_entry.name,
        })

    # -------------------------------------------------------------------------
    # Tests for parking_payment()
    # -------------------------------------------------------------------------
    def test_parking_payment_marks_paid_bool(self):
        """Test parking_payment() sets paid_bool = True on the linked
        parking.entry record."""
        # Reset flags so the test is independent
        self.parking_entry.write({'paid_bool': False, 'state': 'check_out'})
        wizard = self._create_wizard()
        wizard.parking_payment()
        self.assertTrue(
            self.parking_entry.paid_bool,
            "paid_bool must be True after parking_payment() is called.")

    def test_parking_payment_sets_state_to_payment(self):
        """Test parking_payment() changes the parking.entry state to
        'payment'."""
        self.parking_entry.write({'paid_bool': False, 'state': 'check_out'})
        wizard = self._create_wizard()
        wizard.parking_payment()
        self.assertEqual(
            self.parking_entry.state, 'payment',
            "State must be 'payment' after parking_payment() is called.")

    def test_parking_payment_creates_account_payment(self):
        """Test parking_payment() creates an account.payment record with the
        correct amount and partner."""
        self.parking_entry.write({'paid_bool': False, 'state': 'check_out'})
        wizard = self._create_wizard()
        payment_count_before = self.env['account.payment'].search_count([
            ('partner_id', '=', self.partner.id),
            ('amount', '=', self.parking_entry.parking_cost),
        ])
        wizard.parking_payment()
        payment_count_after = self.env['account.payment'].search_count([
            ('partner_id', '=', self.partner.id),
            ('amount', '=', self.parking_entry.parking_cost),
        ])
        self.assertGreater(
            payment_count_after, payment_count_before,
            "A new account.payment record must be created by parking_payment().")

    def test_parking_payment_creates_inbound_payment(self):
        """Test parking_payment() creates an inbound account.payment."""
        self.parking_entry.write({'paid_bool': False, 'state': 'check_out'})
        wizard = self._create_wizard()
        wizard.parking_payment()
        payment = self.env['account.payment'].search([
            ('partner_id', '=', self.partner.id),
            ('amount', '=', self.parking_entry.parking_cost),
        ], limit=1, order='id desc')
        self.assertTrue(payment.exists(),
                        "An account.payment must exist after parking_payment().")
        self.assertEqual(
            payment.payment_type, 'inbound',
            "The created payment must be of type 'inbound'.")

    def test_parking_payment_posts_account_payment(self):
        """Test parking_payment() posts (confirms) the created account.payment
        so its state is not 'draft'."""
        self.parking_entry.write({'paid_bool': False, 'state': 'check_out'})
        wizard = self._create_wizard()
        wizard.parking_payment()
        payment = self.env['account.payment'].search([
            ('partner_id', '=', self.partner.id),
            ('amount', '=', self.parking_entry.parking_cost),
        ], limit=1, order='id desc')
        self.assertTrue(payment.exists(),
                        "An account.payment must exist after parking_payment().")
        self.assertNotEqual(
            payment.state, 'draft',
            "The payment must be posted (not in 'draft') after parking_payment().")
