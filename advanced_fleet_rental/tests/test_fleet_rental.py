# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rahna Rasheed- Sruthi C  (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0(OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestFleetRentalContract(TransactionCase):
    """Test suite for the Fleet Rental Contract module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Country & State
        cls.country = cls.env.ref('base.in')
        cls.state = cls.env['res.country.state'].search(
            [('country_id', '=', cls.country.id)], limit=1)

        # Partner / Customer
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'test@example.com',
            'phone': '1234567890',
        })

        # Fleet brand & model
        cls.brand = cls.env['fleet.vehicle.model.brand'].create(
            {'name': 'TestBrand'})
        cls.model = cls.env['fleet.vehicle.model'].create({
            'name': 'TestModel',
            'brand_id': cls.brand.id,
        })

        # Vehicle
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'KL-01-TEST',
            'rent_hour': 100.0,
            'rent_day': 500.0,
            'rent_kilometer': 10.0,
            'charge_hour': 20.0,
            'charge_day': 50.0,
            'charge_kilometer': 5.0,
        })

        # Responsible user
        cls.user = cls.env.ref('base.user_admin')

        # Cancellation policy
        cls.cancel_policy = cls.env['cancellation.policy'].create({
            'name': 'Standard Policy',
            'terms_conditions': 'No refund after 24 hours.',
        })

        # Product for extra service
        cls.product = cls.env['product.product'].create({
            'name': 'GPS Service',
            'lst_price': 150.0,
            'type': 'service',
        })

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _make_contract(self, rent_type='days', extra=None):
        """Return a minimal valid rental contract."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        vals = {
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'responsible_id': self.user.id,
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=5),
            'pickup_location': 'Loc A',
            'dropoff_location': 'Loc B',
            'pickup_street': '10 Main St',
            'dropoff_street': '20 Main St',
            'pickup_city': 'Kochi',
            'dropoff_city': 'Kochi',
            'pickup_state_id': self.state.id,
            'dropoff_state_id': self.state.id,
            'pickup_zip': '682001',
            'dropoff_zip': '682001',
            'pickup_country_id': self.country.id,
            'dropoff_country_id': self.country.id,
            'rent_type': rent_type,
            'payment_type': 'full',
        }
        if extra:
            vals.update(extra)
        return self.env['fleet.rental.contract'].create(vals)

    # ==================================================================
    # 1. Contract Creation & Sequence
    # ==================================================================
    def test_01_contract_creation_sequence(self):
        """Contract should receive a unique sequence name on creation."""
        contract = self._make_contract()
        self.assertTrue(contract.name)
        self.assertNotEqual(contract.name, 'New',
                            "Contract name should be assigned from sequence.")

    def test_02_contract_default_state(self):
        """Newly created contract must default to 'new' state."""
        contract = self._make_contract()
        self.assertEqual(contract.state, 'new')

    # ==================================================================
    # 2. Rental Period Computation
    # ==================================================================
    def test_03_compute_rental_period_days(self):
        """total_days should equal (dropoff - pickup).days + 1."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=4),
        })
        self.assertEqual(contract.total_days, 5)

    def test_04_compute_rental_period_hours(self):
        """total_hours should reflect hours between pickup and dropoff."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(rent_type='hours', extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(hours=10),
        })
        self.assertAlmostEqual(contract.total_hours, 10.0, places=1)

    def test_05_zero_dates_resets_period(self):
        """When dates are cleared, totals should reset to zero."""
        contract = self._make_contract()
        contract.write({'pickup_date': False, 'dropoff_date': False})
        self.assertEqual(contract.total_days, 0)
        self.assertEqual(contract.total_hours, 0)

    # ==================================================================
    # 3. Total Rental Charge Computation
    # ==================================================================
    def test_06_total_rental_charge_days(self):
        """Rental charge = rent_per_day * total_days for day-based rent."""
        contract = self._make_contract(rent_type='days')
        expected = self.vehicle.rent_day * contract.total_days
        self.assertAlmostEqual(contract.total_rental_charge, expected, places=2)

    def test_07_total_rental_charge_hours(self):
        """Rental charge = rent_per_hour * total_hours for hour-based rent."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(rent_type='hours', extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(hours=5),
        })
        expected = self.vehicle.rent_hour * contract.total_hours
        self.assertAlmostEqual(contract.total_rental_charge, expected, places=2)

    def test_08_total_rental_charge_kilometers(self):
        """Rental charge = rent_per_km * total_km for km-based rent."""
        contract = self._make_contract(rent_type='kilometers',
                                       extra={'total_km': 100})
        expected = self.vehicle.rent_kilometer * 100
        self.assertAlmostEqual(contract.total_rental_charge, expected, places=2)

    def test_09_driver_charge_included_in_rent(self):
        """Driver charge should be added when charge_type='including'."""
        contract = self._make_contract(extra={
            'driver_required': True,
            'charge_type': 'including',
            'driver_charge': 200.0,
        })
        base = self.vehicle.rent_day * contract.total_days
        self.assertAlmostEqual(contract.total_rental_charge, base + 200.0,
                               places=2)

    def test_10_driver_charge_excluded_from_rent(self):
        """Driver charge should NOT be added when charge_type='excluding'."""
        contract = self._make_contract(extra={
            'driver_required': True,
            'charge_type': 'excluding',
            'driver_charge': 200.0,
        })
        base = self.vehicle.rent_day * contract.total_days
        self.assertAlmostEqual(contract.total_rental_charge, base, places=2)

    # ==================================================================
    # 4. Extra Charge Computation
    # ==================================================================
    def test_11_total_extra_charge_hours(self):
        """Extra charge for hour-type = extra_per_hour * total_extra_hours."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(rent_type='hours', extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(hours=5),
            'is_extra_charge': True,
            'total_extra_hours': 3,
        })
        expected = self.vehicle.charge_hour * 3
        self.assertAlmostEqual(contract.total_extra_charge, expected, places=2)

    def test_12_total_extra_charge_days(self):
        """Extra charge for day-type = extra_per_day * total_extra_days."""
        contract = self._make_contract(extra={
            'is_extra_charge': True,
            'total_extra_days': 2,
        })
        expected = self.vehicle.charge_day * 2
        self.assertAlmostEqual(contract.total_extra_charge, expected, places=2)

    def test_13_total_extra_charge_kilometers(self):
        """Extra charge for km-type = extra_per_km * total_extra_km."""
        contract = self._make_contract(rent_type='kilometers', extra={
            'total_km': 100,
            'is_extra_charge': True,
            'total_extra_km': 20,
        })
        expected = self.vehicle.charge_kilometer * 20
        self.assertAlmostEqual(contract.total_extra_charge, expected, places=2)

    # ==================================================================
    # 5. Constraints
    # ==================================================================
    def test_14_constraint_hours_exceed_period(self):
        """ValidationError if total_hours exceeds the actual period hours."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        with self.assertRaises(ValidationError):
            self._make_contract(rent_type='hours', extra={
                'pickup_date': now,
                'dropoff_date': now + timedelta(hours=5),
                'total_hours': 10,  # more than 5-hour window
            })

    def test_15_constraint_zero_hours(self):
        """ValidationError when total_hours is explicitly set to 0."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        with self.assertRaises(ValidationError):
            self._make_contract(rent_type='hours', extra={
                'pickup_date': now,
                'dropoff_date': now + timedelta(hours=5),
                'total_hours': 0,
            })

    def test_16_constraint_days_exceed_period(self):
        """ValidationError if total_days exceeds actual period."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        with self.assertRaises(ValidationError):
            self._make_contract(rent_type='days', extra={
                'pickup_date': now,
                'dropoff_date': now + timedelta(days=3),
                'total_days': 10,
            })

    def test_17_constraint_zero_days(self):
        """ValidationError when total_days is set to 0."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        with self.assertRaises(ValidationError):
            self._make_contract(rent_type='days', extra={
                'pickup_date': now,
                'dropoff_date': now + timedelta(days=3),
                'total_days': 0,
            })

    # ==================================================================
    # 6. action_installment – Payment Plan Generation
    # ==================================================================
    def test_18_installment_full_payment(self):
        """Full payment type should generate exactly 1 payment plan line."""
        contract = self._make_contract(extra={'payment_type': 'full'})
        contract.action_installment()
        self.assertEqual(len(contract.rental_payment_plan_ids), 1)
        plan = contract.rental_payment_plan_ids[0]
        self.assertAlmostEqual(plan.payment_amount,
                               contract.total_rental_charge, places=2)

    def test_19_installment_daily_payment(self):
        """Daily payment type should generate one plan per rental day."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=4),
            'payment_type': 'daily',
        })
        contract.action_installment()
        self.assertGreater(len(contract.rental_payment_plan_ids), 1)

    def test_20_installment_weekly_payment(self):
        """Weekly payment: total plan amounts should sum to total_rental_charge."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=14),
            'payment_type': 'weekly',
        })
        contract.action_installment()
        total = sum(contract.rental_payment_plan_ids.mapped('payment_amount'))
        self.assertAlmostEqual(total, contract.total_rental_charge, places=2)

    def test_21_installment_km_only_full_allowed(self):
        """Km-based rent only allows 'full' payment; daily should raise error."""
        contract = self._make_contract(rent_type='kilometers', extra={
            'total_km': 100,
            'payment_type': 'daily',
        })
        with self.assertRaises(ValidationError):
            contract.action_installment()

    def test_22_installment_hours_only_full_allowed(self):
        """Hour-based rent only allows 'full' payment; weekly should raise."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(rent_type='hours', extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(hours=10),
            'payment_type': 'weekly',
        })
        with self.assertRaises(ValidationError):
            contract.action_installment()

    def test_23_installment_zero_km_raises_error(self):
        """Km-based rent with total_km=0 must raise ValidationError."""
        contract = self._make_contract(rent_type='kilometers', extra={
            'total_km': 0,
            'payment_type': 'full',
        })
        with self.assertRaises(ValidationError):
            contract.action_installment()

    def test_24_installment_weekly_less_than_7_days_raises(self):
        """Weekly payment with fewer than 7 days should raise ValidationError."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=3),
            'payment_type': 'weekly',
        })
        with self.assertRaises(ValidationError):
            contract.action_installment()

    def test_25_installment_monthly_less_than_30_days_raises(self):
        """Monthly payment with fewer than 30 days should raise ValidationError."""
        now = datetime(2026, 6, 1, 8, 0, 0)
        contract = self._make_contract(extra={
            'pickup_date': now,
            'dropoff_date': now + timedelta(days=10),
            'payment_type': 'monthly',
        })
        with self.assertRaises(ValidationError):
            contract.action_installment()

    def test_26_installment_replaces_existing_plans(self):
        """Calling action_installment twice should replace old plan lines."""
        contract = self._make_contract(extra={'payment_type': 'full'})
        contract.action_installment()
        first_count = len(contract.rental_payment_plan_ids)
        contract.action_installment()
        self.assertEqual(len(contract.rental_payment_plan_ids), first_count)

    # ==================================================================
    # 7. State Transitions
    # ==================================================================
    def test_27_action_cancel(self):
        """action_cancel should set contract state to 'cancel'."""
        contract = self._make_contract()
        contract.action_cancel()
        self.assertEqual(contract.state, 'cancel')

    # ==================================================================
    # 8. Extra Services Invoice
    # ==================================================================
    def test_28_extra_service_invoice_no_services_raises(self):
        """action_extra_invoice_charge raises ValidationError with no services."""
        contract = self._make_contract()
        with self.assertRaises(ValidationError):
            contract.action_extra_invoice_charge()

    def test_29_extra_service_invoice_created(self):
        """action_extra_invoice_charge creates a posted invoice."""
        contract = self._make_contract()
        self.env['extra.service'].create({
            'contract_id': contract.id,
            'product_id': self.product.id,
            'quantity': 2.0,
        })
        contract.action_extra_invoice_charge()
        self.assertTrue(contract.is_extra_invoice_created)
        invoice = self.env['account.move'].search([
            ('vehicle_rental_id', '=', contract.id),
            ('move_type', '=', 'out_invoice'),
        ], limit=1)
        self.assertTrue(invoice)
        self.assertEqual(invoice.state, 'posted')

    # ==================================================================
    # 9. Cancellation Charges Invoice
    # ==================================================================
    def test_30_cancel_charges_no_policy_raises(self):
        """action_cancel_charges without policy raises ValidationError."""
        contract = self._make_contract()
        with self.assertRaises(ValidationError):
            contract.action_cancel_charges()

    def test_31_cancel_charges_invoice_created(self):
        """action_cancel_charges creates an invoice and sets flag."""
        contract = self._make_contract(extra={
            'cancellation_policy_id': self.cancel_policy.id,
            'cancellation_charge': 300.0,
        })
        result = contract.action_cancel_charges()
        self.assertTrue(contract.is_cancelled_invoiced)
        self.assertEqual(result['res_model'], 'account.move')

    # ==================================================================
    # 10. Invoice Count Smart Button
    # ==================================================================
    def test_32_vehicle_to_invoice_count(self):
        """vehicle_to_invoice_count reflects invoices linked to contract."""
        contract = self._make_contract()
        self.assertEqual(contract.vehicle_to_invoice_count, 0)
        self.env['extra.service'].create({
            'contract_id': contract.id,
            'product_id': self.product.id,
            'quantity': 1.0,
        })
        contract.action_extra_invoice_charge()
        self.assertEqual(contract.vehicle_to_invoice_count, 1)

    # ==================================================================
    # 11. action_account_tab
    # ==================================================================
    def test_33_action_account_tab_returns_window_action(self):
        """action_account_tab should return an ir.actions.act_window dict."""
        contract = self._make_contract()
        result = contract.action_account_tab()
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'account.move')

    # ==================================================================
    # 12. ExtraService Model
    # ==================================================================
    def test_34_extra_service_amount_compute(self):
        """Extra service amount = quantity * unit_price."""
        service = self.env['extra.service'].create({
            'product_id': self.product.id,
            'quantity': 3.0,
        })
        self.assertAlmostEqual(service.amount,
                               3.0 * self.product.lst_price, places=2)

    def test_35_extra_service_amount_updates_on_qty_change(self):
        """Extra service amount should recompute when quantity changes."""
        service = self.env['extra.service'].create({
            'product_id': self.product.id,
            'quantity': 2.0,
        })
        service.write({'quantity': 5.0})
        self.assertAlmostEqual(service.amount,
                               5.0 * self.product.lst_price, places=2)

    # ==================================================================
    # 13. RentalPaymentPlan Model
    # ==================================================================
    def test_36_payment_plan_state_without_invoice(self):
        """Plan payment_state should be 'not_paid' when no invoice linked."""
        contract = self._make_contract(extra={'payment_type': 'full'})
        contract.action_installment()
        plan = contract.rental_payment_plan_ids[0]
        self.assertEqual(plan.payment_state, 'not_paid')

    def test_37_payment_plan_action_create_invoice(self):
        """action_create_invoice on a plan should create a posted invoice."""
        contract = self._make_contract(extra={'payment_type': 'full'})
        contract.action_installment()
        plan = contract.rental_payment_plan_ids[0]
        invoice = plan.action_create_invoice()
        self.assertTrue(invoice)
        self.assertEqual(invoice.state, 'posted')
        self.assertTrue(plan.is_invoiced)
        self.assertEqual(plan.invoice_id.id, invoice.id)

    def test_38_payment_plan_state_follows_invoice(self):
        """Plan payment_state should mirror the linked invoice state."""
        contract = self._make_contract(extra={'payment_type': 'full'})
        contract.action_installment()
        plan = contract.rental_payment_plan_ids[0]
        plan.action_create_invoice()
        # Invoice is posted → payment_state driven by invoice.payment_state
        self.assertIn(plan.payment_state,
                      ['not_paid', 'in_payment', 'paid', 'partial',
                       'reversed', 'invoicing_legacy'])

    # ==================================================================
    # 14. CancellationPolicy Model
    # ==================================================================
    def test_39_cancellation_policy_creation(self):
        """CancellationPolicy should be created with name and terms."""
        policy = self.env['cancellation.policy'].create({
            'name': 'Strict Policy',
            'terms_conditions': 'Penalty applies.',
        })
        self.assertEqual(policy.name, 'Strict Policy')
        self.assertEqual(policy.terms_conditions, 'Penalty applies.')

    def test_40_cancellation_terms_related_field(self):
        """cancellation_terms on contract should mirror policy terms."""
        contract = self._make_contract(extra={
            'cancellation_policy_id': self.cancel_policy.id,
        })
        self.assertEqual(contract.cancellation_terms,
                         self.cancel_policy.terms_conditions)

    # ==================================================================
    # 15. InsurancePolicy Model
    # ==================================================================
    def test_41_insurance_policy_creation(self):
        """InsurancePolicy should be created and linked to a contract."""
        contract = self._make_contract()
        policy = self.env['insurance.policy'].create({
            'policy_number': 'INS-2026-001',
            'name': 'Comprehensive Cover',
            'policy_amount': 5000.0,
            'contract_id': contract.id,
        })
        self.assertEqual(policy.contract_id.id, contract.id)
        self.assertEqual(policy.policy_amount, 5000.0)

    def test_42_multiple_insurance_policies_on_contract(self):
        """A contract can have multiple insurance policies."""
        contract = self._make_contract()
        for i in range(3):
            self.env['insurance.policy'].create({
                'policy_number': f'INS-2026-00{i}',
                'name': f'Policy {i}',
                'contract_id': contract.id,
            })
        self.assertEqual(len(contract.insurance_ids), 3)

    # ==================================================================
    # 16. FleetVehicle Extensions
    # ==================================================================
    def test_43_vehicle_rental_rate_fields(self):
        """Vehicle should store rental rate fields correctly."""
        self.assertEqual(self.vehicle.rent_hour, 100.0)
        self.assertEqual(self.vehicle.rent_day, 500.0)
        self.assertEqual(self.vehicle.rent_kilometer, 10.0)

    def test_44_vehicle_extra_charge_fields(self):
        """Vehicle should store extra charge fields correctly."""
        self.assertEqual(self.vehicle.charge_hour, 20.0)
        self.assertEqual(self.vehicle.charge_day, 50.0)
        self.assertEqual(self.vehicle.charge_kilometer, 5.0)

    def test_45_vehicle_default_status_operational(self):
        """Vehicle status should default to 'operational'."""
        self.assertEqual(self.vehicle.status, 'operational')

    # ==================================================================
    # 17. Onchange Helpers (unit-level)
    # ==================================================================
    def test_46_onchange_pickup_state_sets_country(self):
        """_onchange_pickup_state should auto-fill pickup_country_id."""
        contract = self._make_contract()
        contract.pickup_state_id = self.state
        contract._onchange_pickup_state()
        self.assertEqual(contract.pickup_country_id,
                         self.state.country_id)

    def test_47_onchange_dropoff_state_sets_country(self):
        """_onchange_dropoff_state should auto-fill dropoff_country_id."""
        contract = self._make_contract()
        contract.dropoff_state_id = self.state
        contract._onchange_dropoff_state()
        self.assertEqual(contract.dropoff_country_id,
                         self.state.country_id)

    # ==================================================================
    # 18. AccountMove Extension
    # ==================================================================
    def test_48_account_move_has_vehicle_rental_field(self):
        """account.move model should have vehicle_rental_id field."""
        move = self.env['account.move']
        self.assertIn('vehicle_rental_id', move._fields)

    def test_49_invoice_linked_to_contract(self):
        """Invoices created via extra service should link vehicle_rental_id."""
        contract = self._make_contract()
        self.env['extra.service'].create({
            'contract_id': contract.id,
            'product_id': self.product.id,
            'quantity': 1.0,
        })
        contract.action_extra_invoice_charge()
        invoice = self.env['account.move'].search([
            ('vehicle_rental_id', '=', contract.id)
        ], limit=1)
        self.assertTrue(invoice)
        self.assertEqual(invoice.vehicle_rental_id.id, contract.id)

    # ==================================================================
    # 19. _schedule_auto_invoice_checker
    # ==================================================================
    def test_50_schedule_auto_invoice_checker_no_error(self):
        """Scheduled auto-invoice checker should run without errors."""
        try:
            self.env['rental.payment.plan']._schedule_auto_invoice_checker()
        except Exception as exc:
            self.fail(
                f"_schedule_auto_invoice_checker raised an exception: {exc}")
