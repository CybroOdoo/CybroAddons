# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import common
from datetime import date, timedelta


class TestVehicleSubscription(common.TransactionCase):
    """Test suite for the vehicle_subscription module.

    Covers:
        - Subscription creation and state transitions
        - Subscription vehicle change via subscription.request
        - Cancellation request approval with full payment
        - Cancellation request approval with no/partial payment
    """

    @classmethod
    def setUpClass(cls):
        super(TestVehicleSubscription, cls).setUpClass()
        # Disable tracking to speed up tests and avoid email side-effects
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # 1. Create a customer
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })

        # 2. Setup Vehicle Model and Brand
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({
            'name': 'Test Brand'
        })
        cls.vehicle_model = cls.env['fleet.vehicle.model'].create({
            'name': 'Test Model',
            'brand_id': cls.brand.id,
            'seats': 4,
            'vehicle_type': 'car',
        })

        # 3. Setup Insurance Type
        cls.insurance_type = cls.env['insurance.type'].create({
            'name': 'Full Coverage',
            'coverage_ids': [(0, 0, {'description': 'Basic', 'coverage_price': 200.0})],
        })

        # 4. Create Vehicles
        cls.vehicle_1 = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST-001',
            'subscription_price': 50.0,
            'free_km': 1000,
            'charge_km': 12,
            'fuel_rate': 300,
        })
        cls.vehicle_2 = cls.env['fleet.vehicle'].create({
            'model_id': cls.vehicle_model.id,
            'license_plate': 'TEST-002',
            'subscription_price': 60.0,
            'free_km': 1200,
            'charge_km': 12,
            'fuel_rate': 300,
        })

        # 5. Create Insurance records for the vehicles
        start_date = date.today() - timedelta(days=5)
        end_date = date.today() + timedelta(days=360)
        cls.insurance_1 = cls.env['vehicle.insurance'].create({
            'vehicle_id': cls.vehicle_1.id,
            'insurance_type_id': cls.insurance_type.id,
            'start_date': start_date,
            'end_date': end_date,
        })
        cls.insurance_2 = cls.env['vehicle.insurance'].create({
            'vehicle_id': cls.vehicle_2.id,
            'insurance_type_id': cls.insurance_type.id,
            'start_date': start_date,
            'end_date': end_date,
        })

        # 6. Add a completed service log so vehicles appear in _get_vehicle_domain()
        #    The method requires at least one service with state='done' and no
        #    'running', 'new', or 'cancelled' entries.
        cls.env['fleet.vehicle.log.services'].create({
            'vehicle_id': cls.vehicle_1.id,
            'state': 'done',
        })
        cls.env['fleet.vehicle.log.services'].create({
            'vehicle_id': cls.vehicle_2.id,
            'state': 'done',
        })

    # ------------------------------------------------------------------
    # Test 01 – Create subscription and generate sale order
    # ------------------------------------------------------------------
    def test_01_create_subscription(self):
        """Subscription starts in draft; action_invoice moves it to subscribed."""
        subscription = self.env['fleet.subscription'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle_1.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'insurance_type_id': self.insurance_1.id,
            'extra_km': 0,
            'fuel': 'without_fuel',
        })
        self.assertEqual(
            subscription.state, 'draft',
            "Subscription should start in 'draft' state"
        )

        subscription.action_invoice()

        self.assertTrue(
            subscription.sale_id,
            "action_invoice() should create a linked sale order"
        )
        self.assertEqual(
            subscription.state, 'subscribed',
            "Subscription state should be 'subscribed' after action_invoice()"
        )

    # ------------------------------------------------------------------
    # Test 02 – Change subscription vehicle via subscription.request
    # ------------------------------------------------------------------
    def test_02_change_subscription(self):
        """A subscription.request should change the vehicle on approval."""
        subscription = self.env['fleet.subscription'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle_1.id,
            'start_date': date.today(),
            'end_date': date.today() + timedelta(days=30),
            'insurance_type_id': self.insurance_1.id,
            'extra_km': 0,
            'fuel': 'without_fuel',
        })
        subscription.action_invoice()
        self.assertEqual(subscription.state, 'subscribed')

        # Verify vehicle 2 is available in the domain
        available_ids = subscription._get_vehicle_domain()
        self.assertIn(
            self.vehicle_2.id, available_ids,
            "Vehicle 2 should appear in the available vehicle domain"
        )

        # Create and approve the vehicle-change request
        sub_request = self.env['subscription.request'].create({
            'current_vehicle_id': self.vehicle_1.id,
            'new_vehicle_id': self.vehicle_2.id,
            'customer_id': self.customer.id,
            'reason_to_change': 'Upgrade',
        })
        self.assertEqual(
            sub_request.state, 'to_approve',
            "New subscription request should be in 'to_approve' state"
        )

        sub_request.action_approve()

        self.assertEqual(
            sub_request.state, 'approved',
            "Subscription request should be 'approved' after action_approve()"
        )
        subscription.invalidate_recordset()  # refresh from DB
        self.assertEqual(
            subscription.vehicle_id.id, self.vehicle_2.id,
            "Subscription vehicle should be updated to vehicle_2 after approval"
        )
        self.assertTrue(
            subscription.invisible_sub,
            "invisible_sub flag should be True after vehicle change"
        )

    # ------------------------------------------------------------------
    # Test 03 – Cancellation with a fully-paid invoice
    # ------------------------------------------------------------------
    def test_03_cancel_subscription_full_payment(self):
        """Cancellation request approved when invoice is fully paid."""
        subscription = self.env['fleet.subscription'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle_1.id,
            'start_date': date.today() - timedelta(days=10),
            'end_date': date.today() + timedelta(days=20),
            'insurance_type_id': self.insurance_1.id,
            'extra_km': 0,
            'fuel': 'without_fuel',
        })
        subscription.action_invoice()
        subscription.sale_id.action_confirm()
        invoice = subscription.sale_id._create_invoices()
        subscription.invoice_ids = [(4, invoice.id)]

        # Post the invoice
        if invoice.state != 'posted':
            invoice.action_post()

        # Simulate full payment
        self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({
            'amount': invoice.amount_total,
        })._create_payments()

        cancel_request = self.env['cancellation.request'].create({
            'vehicle_id': self.vehicle_1.id,
            'customer_id': self.customer.id,
            'date': date.today() + timedelta(days=5),
            'reason': 'No longer needed',
        })

        cancel_request.action_approve()

        self.assertEqual(
            cancel_request.state, 'approved',
            "Cancellation request should be 'approved'"
        )
        subscription.invalidate_recordset()
        self.assertEqual(
            subscription.state, 'cancel',
            "Subscription state should be 'cancel' after approval"
        )

    # ------------------------------------------------------------------
    # Test 04 – Cancellation with an unpaid invoice
    # ------------------------------------------------------------------
    def test_04_cancel_subscription_partial_payment(self):
        """Cancellation request approved when invoice has no payment."""
        subscription = self.env['fleet.subscription'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle_2.id,
            'start_date': date.today() - timedelta(days=10),
            'end_date': date.today() + timedelta(days=20),
            'insurance_type_id': self.insurance_1.id,
            'extra_km': 0,
            'fuel': 'without_fuel',
        })
        subscription.action_invoice()
        subscription.sale_id.action_confirm()
        invoice = subscription.sale_id._create_invoices()
        subscription.invoice_ids = [(4, invoice.id)]

        # Leave the invoice unpaid so the "no payment" branch is exercised
        cancel_request = self.env['cancellation.request'].create({
            'vehicle_id': self.vehicle_2.id,
            'customer_id': self.customer.id,
            'date': date.today() + timedelta(days=5),
            'reason': 'Cannot afford',
        })

        cancel_request.action_approve()

        self.assertEqual(
            cancel_request.state, 'approved',
            "Cancellation request should be 'approved'"
        )
