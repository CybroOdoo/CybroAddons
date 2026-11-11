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
#############################################################################
from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCarRentalContract(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
            'email': 'customer@test.com',
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({
            'model_id': cls.model.id,
            'license_plate': 'TEST-CONTRACT-001',
        })

        # We need a journal and an account
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })

        cls.account = cls.env['account.account'].create({
            'name': 'Test Account',
            'code': 'TESTACC',
            'account_type': 'asset_receivable',
        })

        cls.income_account = cls.env['account.account'].create({
            'name': 'Income Account',
            'code': 'INCACC',
            'account_type': 'income',
        })

        cls.bank_journal = cls.env['account.journal'].search(
            [('type', '=', 'bank'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'Bank',
                'code': 'BNK',
                'type': 'bank',
                'company_id': cls.env.company.id,
            })

        # Get or create fleet_service_product
        product_template = cls.env.ref('fleet_rental.fleet_service_product', raise_if_not_found=False)
        if product_template:
            cls.product = product_template.product_variant_id or cls.env['product.product'].search(
                [('product_tmpl_id', '=', product_template.id)], limit=1)
            cls.product.property_account_income_id = cls.income_account.id
            product_template.property_account_income_id = cls.income_account.id
        else:
            cls.product = cls.env['product.product'].create({
                'name': 'Car Rental Service',
                'type': 'service',
                'property_account_income_id': cls.income_account.id,
            })
            cls.env['ir.model.data'].create({
                'name': 'fleet_service_product',
                'module': 'fleet_rental',
                'model': 'product.template',
                'res_id': cls.product.product_tmpl_id.id,
            })

    def test_validate_dates(self):
        """ Test that end date cannot be before start date """
        with self.assertRaises(UserError):
            self.env['car.rental.contract'].create({
                'customer_id': self.customer.id,
                'vehicle_id': self.vehicle.id,
                'cost': 100.0,
                'rent_start_date': date.today(),
                'rent_end_date': date.today() - timedelta(days=1),
                'cost_frequency': 'no',
                'first_payment': 100.0,
            })

    def test_validate_time(self):
        """ Test validate time for rent by hour """
        with self.assertRaises(ValidationError):
            self.env['car.rental.contract'].create({
                'customer_id': self.customer.id,
                'vehicle_id': self.vehicle.id,
                'cost': 100.0,
                'rent_start_date': date.today(),
                'rent_end_date': date.today(),
                'rent_by_hour': True,
                'start_time': '12:00',
                'end_time': '10:00',
                'cost_frequency': 'no',
                'first_payment': 100.0,
            })

    def test_action_run(self):
        """ Test action run changes state """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_run()
        self.assertEqual(contract.state, 'running')
        # Check that vehicle state updated
        self.assertEqual(contract.vehicle_id.state_id.id, self.env.ref('fleet_rental.vehicle_state_rent').id)

    def test_action_cancel(self):
        """ Test action cancel changes state """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_cancel()
        self.assertEqual(contract.state, 'cancel')
        self.assertTrue(contract.vehicle_id.rental_check_availability)
        self.assertEqual(contract.vehicle_id.state_id.id, self.env.ref('fleet_rental.vehicle_state_active').id)

    def test_action_confirm(self):
        """ Test action confirm """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_confirm()
        self.assertEqual(contract.state, 'reserved')
        self.assertFalse(contract.vehicle_id.rental_check_availability)
        self.assertTrue(contract.reserved_fleet_id)

    def test_extend_rent(self):
        """ Test extend rent operations """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_confirm()

        contract.action_extend_rent()
        self.assertTrue(contract.read_only)

        contract.rent_end_date = date.today() + timedelta(days=5)
        contract.action_confirm_extend_rent()
        self.assertFalse(contract.read_only)
        self.assertEqual(contract.vehicle_id.rental_reserved_time.date_to, date.today() + timedelta(days=5))

    def test_action_invoice_create(self):
        """ Test invoice creation """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        result = contract.action_invoice_create()
        self.assertTrue(contract.first_invoice_created)
        self.assertTrue(contract.first_payment_inv)
        self.assertEqual(result['res_model'], 'account.move')

    def test_set_to_done(self):
        """ Test setting contract to done when invoices are paid vs unpaid """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        contract.set_to_done()
        self.assertEqual(contract.state, 'done')

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'fleet_rent_id': contract.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'price_unit': 100.0,
                'quantity': 1,
                'account_id': self.income_account.id,
            })],
        })
        with self.assertRaises(UserError):
            contract.set_to_done()

        invoice.action_post()
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({
            'journal_id': self.bank_journal.id,
        })._create_payments()
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))
        contract.set_to_done()
        self.assertEqual(contract.state, 'done')

    def test_force_checking(self):
        """ Test force checking payment status """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'running',
        })
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'fleet_rent_id': contract.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'price_unit': 100.0,
                'quantity': 1,
                'account_id': self.income_account.id,
            })],
        })
        with self.assertRaises(UserError):
            contract.force_checking()

        invoice.action_post()
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids,
        ).create({
            'journal_id': self.bank_journal.id,
        })._create_payments()
        self.assertIn(invoice.payment_state, ('paid', 'in_payment'))
        contract.force_checking()
        self.assertEqual(contract.state, 'checking')

    def test_action_view_invoice(self):
        """ Test invoice smart button action """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        inv1 = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'fleet_rent_id': contract.id,
        })
        contract._compute_invoice_count()
        self.assertEqual(contract.invoice_count, 1)
        res_single = contract.action_view_invoice()
        self.assertEqual(res_single['res_id'], inv1.id)
        self.assertNotIn('view_type', res_single)

        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'fleet_rent_id': contract.id,
        })
        contract._compute_invoice_count()
        self.assertEqual(contract.invoice_count, 2)
        res_multi = contract.action_view_invoice()
        self.assertIn('fleet_rent_id', str(res_multi['domain']))
        self.assertNotIn('view_type', res_multi)

    def test_checklist_and_damage_total(self):
        """ Test checklist lines and cost updates """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        tool = self.env['car.tools'].create({'name': 'Spare Wheel', 'price': 40.0})
        checklist_item = self.env['car.rental.checklist'].create({
            'name': tool.id,
            'price': 40.0,
            'checklist_number': contract.id,
            'checklist_active': False,
        })
        contract.damage_cost = 50.0
        contract._compute_totals()
        self.assertEqual(contract.tools_missing_cost, 40.0)
        self.assertEqual(contract.total_cost, 90.0)

        checklist_item.checklist_active = True
        contract._compute_totals()
        self.assertEqual(contract.tools_missing_cost, 0.0)
        self.assertEqual(contract.total_cost, 50.0)

    def test_action_verify(self):
        """ Test verifying damages and generating invoice """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        contract.action_confirm()
        contract.damage_cost = 60.0
        contract._compute_totals()
        res = contract.action_verify()
        self.assertEqual(contract.state, 'invoice')
        self.assertTrue(contract.vehicle_id.rental_check_availability)
        self.assertFalse(contract.reserved_fleet_id)
        damage_inv = self.env['account.move'].search([('fleet_rent_id', '=', contract.id)])
        self.assertTrue(damage_inv)
        self.assertEqual(res['type'], 'ir.actions.act_window')
        self.assertEqual(res['res_id'], damage_inv.id)

    def test_action_verify_zero_cost(self):
        """ Test verifying damages when total cost is zero sets contract to done directly """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'checking',
        })
        contract._compute_totals()
        res = contract.action_verify()
        self.assertFalse(res)
        self.assertEqual(contract.state, 'done')
        self.assertTrue(contract.vehicle_id.rental_check_availability)

    def test_set_to_done_from_checking(self):
        """ Test set_to_done from checking state """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'checking',
        })
        contract.damage_cost = 50.0
        contract._compute_totals()
        with self.assertRaises(UserError):
            contract.set_to_done()

        contract.damage_cost = 0.0
        contract._compute_totals()
        contract.set_to_done()
        self.assertEqual(contract.state, 'done')

    def test_fleet_scheduler1(self):
        """ Test fleet_scheduler1 single run """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'daily',
            'cost_generated': 50.0,
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'running',
        })
        contract.fleet_scheduler1(date.today())
        rec_lines = self.env['fleet.rental.line'].search([('rental_number', '=', contract.id)])
        self.assertTrue(rec_lines)
        self.assertEqual(rec_lines[0].recurring_amount, 50.0)

    def test_fleet_scheduler_cron(self):
        """ Test fleet_scheduler automated cron job execution """
        self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today() - timedelta(days=2),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'daily',
            'cost_generated': 50.0,
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'running',
        })
        self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today() - timedelta(days=7),
            'rent_end_date': date.today() + timedelta(days=7),
            'cost_frequency': 'weekly',
            'cost_generated': 60.0,
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'running',
        })
        c_expired = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today() - timedelta(days=10),
            'rent_end_date': date.today() - timedelta(days=1),
            'cost_frequency': 'daily',
            'cost_generated': 50.0,
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
            'state': 'running',
        })
        self.env['car.rental.contract'].fleet_scheduler()
        self.assertEqual(c_expired.state, 'checking')

    def test_action_discard_extend_and_validation(self):
        """ Test discard extend and validation when rent_end_date is not extended """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        })
        contract.action_confirm()
        contract.action_extend_rent()
        self.assertTrue(contract.read_only)

        with self.assertRaises(ValidationError):
            contract.rent_end_date = date.today() + timedelta(days=1)
            contract.validate_on_read_only()

        contract.action_discard_extend()
        self.assertFalse(contract.read_only)
        self.assertEqual(contract.rent_end_date, contract.vehicle_id.rental_reserved_time.date_to)

    def test_action_invoice_create_with_recurrence(self):
        """ Test action_invoice_create with past start date and recurring frequency """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today() - timedelta(days=3),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'daily',
            'cost_generated': 40.0,
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        res = contract.action_invoice_create()
        self.assertTrue(contract.first_invoice_created)
        self.assertEqual(res['res_model'], 'account.move')

    def test_contract_unlink_restores_vehicle_availability(self):
        """ Test that deleting a rental contract unlinks reservations and restores vehicle availability """
        contract = self.env['car.rental.contract'].create({
            'customer_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today() + timedelta(days=2),
            'cost_frequency': 'daily',
            'first_payment': 100.0,
            'journal_type': self.journal.id,
            'account_type': self.account.id,
        })
        contract.action_confirm()
        self.assertFalse(self.vehicle.rental_check_availability)
        self.assertTrue(contract.reserved_fleet_id)
        reserved_record = contract.reserved_fleet_id

        # Delete contract
        contract.unlink()
        self.assertTrue(self.vehicle.rental_check_availability)
        self.assertFalse(reserved_record.exists())
