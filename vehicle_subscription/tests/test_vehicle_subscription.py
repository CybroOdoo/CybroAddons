# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from datetime import timedelta
from odoo import fields
from odoo.tests import common, tagged
from odoo.tests.common import mute_logger
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestVehicleSubscription(common.TransactionCase):
    """Test cases for the vehicle_subscription module.

    Covers:
        - Fleet subscription duration and price computation.
        - Date validation constraints.
        - Invoicing flow from subscription.
        - Subscription change request approval logic.
        - Cancellation request approval logic.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # ── Setup Data ────────────────────────────────────────────────────────
        cls.partner = cls.env['res.partner'].create({
            'name': 'Subscription Customer',
            'email': 'customer@test.com',
        })

        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand',
        })

        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
            'seats': 5,
        })

        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-001',
            'subscription_price': 50.0,  # Price per day
            'free_km': 100,
        })

        cls.vehicle_2 = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-002',
            'subscription_price': 60.0,
        })

        cls.ins_type = cls.env['insurance.type'].create({
            'name': 'Full Coverage',
        })
        cls.env['insurance.coverage'].create({
            'description': 'Theft',
            'coverage_price': 100.0,
            'coverage_id': cls.ins_type.id,
        })
        cls.env['insurance.coverage'].create({
            'description': 'Collision',
            'coverage_price': 150.0,
            'coverage_id': cls.ins_type.id,
        })

        cls.today = fields.Date.today()
        cls.vehicle_ins = cls.env['vehicle.insurance'].create({
            'vehicle_id': cls.vehicle.id,
            'insurance_type_id': cls.ins_type.id,
            'start_date': cls.today,
            'end_date': cls.today + timedelta(days=365),
        })

    def test_01_subscription_duration(self):
        """Test duration computation on fleet.subscription."""
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=10),
        })
        self.assertEqual(sub.duration, 10, "Duration should be 10 days")

    def test_02_subscription_price(self):
        """Test price computation (duration * per_day_price + insurance)."""
        # Duration: 10 days. Vehicle price: 50/day. Insurance: 100+150=250.
        # Expected: 10 * 50 + 250 = 500 + 250 = 750.
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'insurance_type_id': self.vehicle_ins.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=10),
        })
        self.assertEqual(sub.price, 750.0, "Price should be 750.0")

    def test_03_date_validation_constraint(self):
        """Test that start_date > end_date raises ValidationError."""
        with mute_logger('odoo.sql_db'):
            with self.assertRaises(ValidationError):
                with self.cr.savepoint():
                    self.env['fleet.subscription'].create({
                        'vehicle_id': self.vehicle.id,
                        'customer_id': self.partner.id,
                        'start_date': self.today + timedelta(days=5),
                        'end_date': self.today,
                    })

    def test_04_action_invoice(self):
        """Test that action_invoice creates a sale order correctly."""
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'insurance_type_id': self.vehicle_ins.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=10),
        })
        # Mock price and extra_price
        sub.action_invoice()
        self.assertTrue(sub.sale_id, "Sale order should be created")
        self.assertEqual(sub.state, 'subscribed', "State should be 'subscribed'")
        self.assertEqual(sub.sale_id.partner_id.id, self.partner.id)
        self.assertEqual(sub.sale_id.order_line[0].price_unit, sub.price + sub.extra_price)

    def test_05_subscription_request_approval(self):
        """Test approving a subscription (vehicle change) request."""
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=10),
            'state': 'subscribed',
        })
        # Need to set sale_id for approval logic
        sub.action_invoice()

        req = self.env['subscription.request'].create({
            'customer_id': self.partner.id,
            'current_vehicle_id': self.vehicle.id,
            'new_vehicle_id': self.vehicle_2.id,
            'reason_to_change': 'Upgrade',
        })
        req.action_approve()

        self.assertEqual(req.state, 'approved')
        self.assertEqual(sub.vehicle_id.id, self.vehicle_2.id, "Subscription vehicle should be updated")
        self.assertEqual(sub.sale_id.order_line[0].name, self.vehicle_2.name, "Sale order line name should be updated")

    def test_06_extra_price_without_fuel(self):
        """Test extra price computation without fuel choice."""
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'start_date': self.today,
            'end_date': self.today + timedelta(days=10),
            'fuel': 'without_fuel',
            'extra_km': 10,
            'charge_km': 15,
        })
        # Formula: extra_km * charge_km = 10 * 15 = 150
        self.assertEqual(sub.extra_price, 150.0)

    def test_07_cancellation_request_flow(self):
        """Test approving a cancellation request."""
        sub = self.env['fleet.subscription'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'start_date': self.today - timedelta(days=5), # Started 5 days ago
            'end_date': self.today + timedelta(days=5),   # Total 10 days
            'state': 'subscribed',
        })
        sub.action_invoice()
        # Initial price: 5 days used out of 10.
        # Subscription price per day: 50. Total untaxed: 50 * 10 = 500 (ignoring insurance for simplicity in this case)

        cancel_req = self.env['cancellation.request'].create({
            'vehicle_id': self.vehicle.id,
            'customer_id': self.partner.id,
            'date': self.today,
            'reason': 'Not needed anymore',
        })

        # To test the refund/invoice logic, we need to handle paid_amount
        # Let's mock a payment or just check the flow.
        # action_approve calculates uptodate_price and compares with paid_amount.

        # If no amount is paid, it should create an invoice for the period used.
        cancel_req.action_approve()
        self.assertEqual(cancel_req.state, 'approved')
        self.assertTrue(sub.invoice_ids or sub.sale_id.invoice_ids, "Should have processed invoice/refund logic")
