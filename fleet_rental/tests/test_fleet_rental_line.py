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
from datetime import date

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestFleetRentalLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })

        # Need a car rental contract, but it requires a lot of fields, we can mock or just create a minimal one.
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.model = cls.env['fleet.vehicle.model'].create({'name': 'Test Model', 'brand_id': cls.brand.id})
        cls.vehicle = cls.env['fleet.vehicle'].create({'model_id': cls.model.id, 'license_plate': 'TEST-LINE-001'})

        cls.contract = cls.env['car.rental.contract'].create({
            'customer_id': cls.customer.id,
            'vehicle_id': cls.vehicle.id,
            'cost': 100.0,
            'rent_start_date': date.today(),
            'rent_end_date': date.today(),
            'cost_frequency': 'no',
            'first_payment': 100.0,
        }) if 'car.rental.contract' in cls.env else False

        # We need an account move to test the payment info
        cls.journal = cls.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', cls.env.company.id)], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Customer Invoices',
                'code': 'INV',
                'type': 'sale',
                'company_id': cls.env.company.id,
            })
        cls.income_account = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', [cls.env.company.id]),
        ], limit=1)
        if not cls.income_account:
            cls.income_account = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': 'TEST_INC_LINE',
                'account_type': 'income',
            })
        cls.bank_journal = cls.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', cls.env.company.id),
        ], limit=1)
        if not cls.bank_journal:
            cls.bank_journal = cls.env['account.journal'].create({
                'name': 'Bank Test',
                'code': 'BNKTL',
                'type': 'bank',
                'company_id': cls.env.company.id,
            })
        cls.invoice = cls.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': cls.customer.id,
            'journal_id': cls.journal.id,
        })

    def test_compute_payment_info(self):
        """ Test compute payment info """
        line = self.env['fleet.rental.line'].create({
            'name': 'Test Line',
            'recurring_amount': 50.0,
            'invoice_number': self.invoice.id,
            'invoice_ref': self.invoice.id,
        })
        if self.contract:
            line.rental_number = self.contract.id

        line._compute_payment_info()
        self.assertEqual(line.payment_info, 'draft')

    def test_compute_payment_info_record_deleted(self):
        """ Test compute payment info when invoice does not exist """
        line = self.env['fleet.rental.line'].create({
            'name': 'Deleted Line',
            'recurring_amount': 50.0,
            'invoice_number': 99999999,
            'invoice_ref': False,
        })
        line._compute_payment_info()
        self.assertEqual(line.payment_info, 'Record Deleted')

    def test_compute_payment_info_from_invoice_number(self):
        """ Test compute payment info from invoice_number fallback """
        line = self.env['fleet.rental.line'].create({
            'name': 'Number Line',
            'recurring_amount': 50.0,
            'invoice_number': self.invoice.id,
            'invoice_ref': False,
        })
        line._compute_payment_info()
        self.assertEqual(line.payment_info, self.invoice.state)

    def test_compute_payment_info_paid(self):
        """ Test compute payment info when invoice is paid """
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.customer.id,
            'journal_id': self.journal.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test line',
                'price_unit': 50.0,
                'quantity': 1,
                'account_id': self.income_account.id,
            })],
        })
        line = self.env['fleet.rental.line'].create({
            'name': 'Paid Test Line',
            'recurring_amount': 50.0,
            'invoice_ref': invoice.id,
        })
        invoice.action_post()
        self.assertEqual(line.payment_info, 'posted')
        self.env['account.payment.register'].with_context(
            active_model='account.move',
            active_ids=invoice.ids,
        ).create({
            'journal_id': self.bank_journal.id,
        })._create_payments()
        line._compute_payment_info()
        self.assertIn(line.payment_info, ('paid', 'in_payment'))
