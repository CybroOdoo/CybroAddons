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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from datetime import timedelta
from odoo import Command, fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountInterestOnOverdueInvoice(TransactionCase):
    """Test suite for Account Interest on Overdue Invoice module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Interest Customer',
        })

        cls.account_income = cls.env['account.account'].search([
            ('account_type', '=', 'income'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_income:
            cls.account_income = cls.env['account.account'].create({
                'name': 'Test Income Account',
                'code': '400099',
                'account_type': 'income',
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.account_interest = cls.env['account.account'].search([
            ('account_type', '=', 'income_other'),
            ('company_ids', 'in', cls.company.id),
        ], limit=1)
        if not cls.account_interest:
            cls.account_interest = cls.env['account.account'].create({
                'name': 'Interest Income Account',
                'code': '490099',
                'account_type': 'income_other',
                'company_ids': [Command.link(cls.company.id)],
            })

        cls.payment_term_daily = cls.env['account.payment.term'].create({
            'name': 'Immediate Daily Interest 5%',
            'interest_overdue_act': True,
            'interest_type': 'daily',
            'interest_percentage': 5.0,
            'interest_account_id': cls.account_interest.id,
        })

        cls.payment_term_weekly = cls.env['account.payment.term'].create({
            'name': 'Immediate Weekly Interest 3%',
            'interest_overdue_act': True,
            'interest_type': 'weekly',
            'interest_percentage': 3.0,
            'interest_account_id': cls.account_interest.id,
        })

        cls.payment_term_monthly = cls.env['account.payment.term'].create({
            'name': 'Immediate Monthly Interest 2%',
            'interest_overdue_act': True,
            'interest_type': 'monthly',
            'interest_percentage': 2.0,
            'interest_account_id': cls.account_interest.id,
        })

        cls.payment_term_no_interest = cls.env['account.payment.term'].create({
            'name': 'Standard Immediate No Interest',
            'interest_overdue_act': False,
            'interest_type': 'daily',
            'interest_percentage': 0.0,
        })

    def _create_invoice(self, payment_term, days_ago=10, price_unit=100.0, move_type='out_invoice'):
        """Helper to create a draft invoice with a past invoice_date."""
        today = fields.Date.today()
        invoice_date = today - timedelta(days=days_ago) if days_ago >= 0 else today + timedelta(days=abs(days_ago))
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner.id,
            'invoice_date': invoice_date,
            'invoice_payment_term_id': payment_term.id,
            'invoice_line_ids': [Command.create({
                'name': 'Test Service Line',
                'price_unit': price_unit,
                'quantity': 1,
                'account_id': self.account_income.id,
            })],
        })

    def test_01_payment_term_constraints(self):
        """Test validation constraint on interest percentage."""
        # 1. Negative percentage when interest is active must raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['account.payment.term'].create({
                'name': 'Invalid Negative Term',
                'interest_overdue_act': True,
                'interest_type': 'daily',
                'interest_percentage': -5.0,
            })

        # 2. Zero percentage when interest is active must raise ValidationError
        with self.assertRaises(ValidationError):
            self.env['account.payment.term'].create({
                'name': 'Invalid Zero Term',
                'interest_overdue_act': True,
                'interest_type': 'daily',
                'interest_percentage': 0.0,
            })

        # 3. Writing invalid percentage to existing term with active interest must raise ValidationError
        with self.assertRaises(ValidationError):
            self.payment_term_daily.write({'interest_percentage': -1.0})

        # 4. Zero percentage allowed when interest_overdue_act is False
        term_inactive = self.env['account.payment.term'].create({
            'name': 'Valid Inactive Term',
            'interest_overdue_act': False,
            'interest_percentage': 0.0,
        })
        self.assertFalse(term_inactive.interest_overdue_act)
        self.assertEqual(term_inactive.interest_percentage, 0.0)

    def test_02_daily_interest_computation(self):
        """Test daily interest computation on overdue invoice."""
        invoice = self._create_invoice(self.payment_term_daily, days_ago=10, price_unit=100.0)
        self.assertEqual(invoice.interest_overdue_act, True)
        self.assertEqual(invoice.interest_type, 'daily')
        self.assertEqual(invoice.interest_percentage, 5.0)
        self.assertEqual(invoice.interest_amount, 0.0)

        # Compute interest
        invoice.action_interest_compute()

        # Overdue by 10 days, 5% per day on 100.0 => 100.0 * 5 * 10 / 100 = 50.0
        self.assertAlmostEqual(invoice.interest_amount, 50.0, places=2)
        self.assertEqual(invoice.interest_calculated_period, '10-d')

        # Check line added
        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertTrue(interest_line)
        self.assertAlmostEqual(interest_line.price_unit, 50.0, places=2)
        self.assertEqual(interest_line.account_id, self.account_interest)

    def test_03_weekly_interest_computation(self):
        """Test weekly interest computation on overdue invoice."""
        # 10 days overdue => ceil(10 / 7) = 2 weeks
        invoice = self._create_invoice(self.payment_term_weekly, days_ago=10, price_unit=200.0)
        invoice.action_interest_compute()

        # 200.0 * 3% * 2 weeks = 12.0
        self.assertAlmostEqual(invoice.interest_amount, 12.0, places=2)
        self.assertEqual(invoice.interest_calculated_period, '2-w')

        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertTrue(interest_line)
        self.assertAlmostEqual(interest_line.price_unit, 12.0, places=2)

    def test_04_monthly_interest_computation(self):
        """Test monthly interest computation on overdue invoice."""
        # 35 days overdue => relativedelta 1 month and ~4-5 days => 1 + 1 = 2 months
        invoice = self._create_invoice(self.payment_term_monthly, days_ago=35, price_unit=500.0)
        invoice.action_interest_compute()

        # 500.0 * 2% * 2 months = 20.0
        self.assertAlmostEqual(invoice.interest_amount, 20.0, places=2)
        self.assertEqual(invoice.interest_calculated_period, '2-m')

        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertTrue(interest_line)
        self.assertAlmostEqual(interest_line.price_unit, 20.0, places=2)

    def test_05_duplicate_compute_same_period_raises_validation_error(self):
        """Test that re-computing interest within the same period raises ValidationError."""
        # Daily
        inv_daily = self._create_invoice(self.payment_term_daily, days_ago=5, price_unit=100.0)
        inv_daily.action_interest_compute()
        with self.assertRaises(ValidationError):
            inv_daily.action_interest_compute()

        # Weekly
        inv_weekly = self._create_invoice(self.payment_term_weekly, days_ago=14, price_unit=100.0)
        inv_weekly.action_interest_compute()
        with self.assertRaises(ValidationError):
            inv_weekly.action_interest_compute()

        # Monthly
        inv_monthly = self._create_invoice(self.payment_term_monthly, days_ago=40, price_unit=100.0)
        inv_monthly.action_interest_compute()
        with self.assertRaises(ValidationError):
            inv_monthly.action_interest_compute()

    def test_06_action_interest_reset(self):
        """Test resetting interest on an invoice."""
        invoice = self._create_invoice(self.payment_term_daily, days_ago=10, price_unit=100.0)
        invoice.action_interest_compute()
        self.assertAlmostEqual(invoice.interest_amount, 50.0, places=2)
        self.assertTrue(invoice.interest_calculated_period)

        # Call reset
        invoice.action_interest_reset()
        self.assertEqual(invoice.interest_amount, 0.0)
        self.assertFalse(invoice.interest_calculated_period)
        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertFalse(interest_line)

    def test_07_onchange_invoice_payment_term_id(self):
        """Test onchange removes interest lines and resets values."""
        invoice = self._create_invoice(self.payment_term_daily, days_ago=10, price_unit=100.0)
        invoice.action_interest_compute()
        self.assertAlmostEqual(invoice.interest_amount, 50.0, places=2)

        # Trigger onchange
        invoice._onchange_invoice_payment_term_id()
        self.assertEqual(invoice.interest_amount, 0.0)
        self.assertFalse(invoice.interest_calculated_period)
        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertFalse(interest_line)

    def test_08_cron_interest_check(self):
        """Test scheduled action _get_interest_check for computing overdue interest."""
        invoice = self._create_invoice(self.payment_term_weekly, days_ago=7, price_unit=100.0)
        self.assertEqual(invoice.interest_amount, 0.0)

        # Run scheduled action
        self.env['account.move']._get_interest_check()
        self.assertAlmostEqual(invoice.interest_amount, 3.0, places=2)
        self.assertEqual(invoice.interest_calculated_period, '1-w')

        # Run scheduled action a second time: should not raise or duplicate line
        self.env['account.move']._get_interest_check()
        interest_lines = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertEqual(len(interest_lines), 1)
        self.assertAlmostEqual(invoice.interest_amount, 3.0, places=2)

    def test_09_conditions_and_skips(self):
        """Test conditions where interest computation should not apply or gets reset."""
        # 1. Non-overdue invoice (in the future)
        future_inv = self._create_invoice(self.payment_term_daily, days_ago=-5, price_unit=100.0)
        future_inv.action_interest_compute()
        self.assertEqual(future_inv.interest_amount, 0.0)
        self.assertFalse(future_inv.interest_calculated_period)

        # 2. Payment term with interest_overdue_act = False
        no_interest_inv = self._create_invoice(self.payment_term_no_interest, days_ago=10, price_unit=100.0)
        no_interest_inv.action_interest_compute()
        self.assertEqual(no_interest_inv.interest_amount, 0.0)

        # 3. Vendor Bill (move_type='in_invoice')
        vendor_bill = self._create_invoice(
            self.payment_term_daily, days_ago=10, price_unit=100.0, move_type='in_invoice'
        )
        vendor_bill.action_interest_compute()
        self.assertEqual(vendor_bill.interest_amount, 0.0)

        # 4. If interest_amount > 0 and invoice is changed to not overdue, compute resets it
        inv = self._create_invoice(self.payment_term_daily, days_ago=10, price_unit=100.0)
        inv.action_interest_compute()
        self.assertAlmostEqual(inv.interest_amount, 50.0, places=2)

        # Change invoice date to tomorrow so it is no longer overdue
        inv.write({'invoice_date': fields.Date.today() + timedelta(days=1)})
        inv.action_interest_compute()
        self.assertEqual(inv.interest_amount, 0.0)
        self.assertFalse(inv.interest_calculated_period)

    def test_10_interest_without_interest_account(self):
        """Test interest computation when no interest account is configured on payment term."""
        term_no_acc = self.env['account.payment.term'].create({
            'name': 'Immediate Daily Interest No Account',
            'interest_overdue_act': True,
            'interest_type': 'daily',
            'interest_percentage': 4.0,
            'interest_account_id': False,
        })
        invoice = self._create_invoice(term_no_acc, days_ago=5, price_unit=100.0)
        invoice.action_interest_compute()
        self.assertAlmostEqual(invoice.interest_amount, 20.0, places=2)
        interest_line = invoice.invoice_line_ids.filtered(
            lambda l: l.name == 'Interest Amount for Overdue'
        )
        self.assertTrue(interest_line)
        self.assertTrue(interest_line.account_id)

    def test_11_get_period_time(self):
        """Directly test get_period_time computation logic."""
        today = fields.Date.today()
        # Daily
        inv_daily = self._create_invoice(self.payment_term_daily, days_ago=15, price_unit=100.0)
        self.assertEqual(inv_daily.get_period_time(today), 15)

        # Weekly
        inv_weekly = self._create_invoice(self.payment_term_weekly, days_ago=8, price_unit=100.0)
        self.assertEqual(inv_weekly.get_period_time(today), 2)  # ceil(8/7) = 2

        # Monthly
        inv_monthly = self._create_invoice(self.payment_term_monthly, days_ago=65, price_unit=100.0)
        # 65 days is over 2 months, so 2 months + remaining days => 3
        self.assertEqual(inv_monthly.get_period_time(today), 3)
