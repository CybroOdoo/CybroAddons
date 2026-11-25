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
#############################################################################
import calendar
from odoo import Command, fields
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):
    """Unit test cases for account.move dashboard methods in odoo_accounting_dashboard."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.Move = cls.env['account.move']

        # Setup Customer & Vendor partners
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Test Dashboard Customer',
        })
        cls.partner_vendor = cls.env['res.partner'].create({
            'name': 'Test Dashboard Vendor',
        })

        # Helper to find or create accounts compatible with Odoo 20 (where account.account uses company_ids)
        def _get_or_create_account(types, code, name, reconcile=False):
            account = cls.env['account.account'].search([
                ('account_type', 'in', types),
                ('company_ids', 'in', cls.company.id),
            ], limit=1)
            if not account:
                account = cls.env['account.account'].search([
                    ('account_type', 'in', types),
                ], limit=1)
                if account:
                    if cls.company.id not in account.company_ids.ids:
                        account.company_ids = [Command.link(cls.company.id)]
                else:
                    account = cls.env['account.account'].create({
                        'name': name,
                        'code': code,
                        'account_type': types[0],
                        'reconcile': reconcile,
                        'company_ids': [Command.link(cls.company.id)],
                    })
            return account

        cls.account_income = _get_or_create_account(('income', 'income_other'), 'INC_DASH_TEST', 'Test Income Account')
        cls.account_expense = _get_or_create_account(('expense',), 'EXP_DASH_TEST', 'Test Expense Account')
        cls.account_receivable = _get_or_create_account(('asset_receivable',), 'REC_DASH_TEST', 'Test Receivable Account', reconcile=True)
        cls.account_payable = _get_or_create_account(('liability_payable',), 'PAY_DASH_TEST', 'Test Payable Account', reconcile=True)

        # Find or create sales, purchase, and bank journals
        cls.journal_sale = cls.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_sale:
            cls.journal_sale = cls.env['account.journal'].create({
                'name': 'Customer Invoices Test',
                'code': 'TJINV',
                'type': 'sale',
                'company_id': cls.company.id,
            })

        cls.journal_purchase = cls.env['account.journal'].search([
            ('type', '=', 'purchase'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_purchase:
            cls.journal_purchase = cls.env['account.journal'].create({
                'name': 'Vendor Bills Test',
                'code': 'TJBILL',
                'type': 'purchase',
                'company_id': cls.company.id,
            })

        cls.journal_bank = cls.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', cls.company.id),
        ], limit=1)
        if not cls.journal_bank:
            cls.journal_bank = cls.env['account.journal'].create({
                'name': 'Bank Test',
                'code': 'TBNK',
                'type': 'bank',
                'company_id': cls.company.id,
            })

    def _create_test_invoice(self, move_type='out_invoice', state='draft', payment_state='not_paid', amount=100.0, partner=None):
        """Helper to create an account.move for testing."""
        today = fields.Date.today()
        is_sale = move_type in ('out_invoice', 'out_refund')
        partner = partner or (self.partner_customer if is_sale else self.partner_vendor)
        journal = self.journal_sale if is_sale else self.journal_purchase
        line_account = self.account_income if is_sale else self.account_expense

        move = self.Move.create({
            'move_type': move_type,
            'partner_id': partner.id,
            'invoice_date': today,
            'invoice_date_due': today,
            'journal_id': journal.id,
            'company_id': self.company.id,
            'invoice_line_ids': [
                (0, 0, {
                    'name': 'Test Line Item',
                    'quantity': 1.0,
                    'price_unit': amount,
                    'account_id': line_account.id,
                })
            ],
        })
        if state == 'posted':
            try:
                move.action_post()
            except Exception:
                self.env.cr.execute(
                    "UPDATE account_move SET state = 'posted' WHERE id = %s",
                    [move.id]
                )
                move.invalidate_recordset(['state'])
        if payment_state == 'paid':
            self.env.cr.execute(
                "UPDATE account_move SET payment_state = 'paid' WHERE id = %s",
                [move.id]
            )
            move.invalidate_recordset(['payment_state'])
        return move

    def test_get_datas(self):
        """Test get_datas: returns correct tile counts, income, unreconciled items and journals."""
        initial_data = self.Move.get_datas()
        expected_keys = {
            'open_invoice',
            'paid_invoice',
            'income',
            'currency_symbol',
            'unreconcile_items',
            'journal_data',
        }
        self.assertTrue(expected_keys.issubset(initial_data.keys()),
                        f"get_datas() missing keys: {expected_keys - initial_data.keys()}")

        self.assertIsInstance(initial_data['open_invoice'], int)
        self.assertIsInstance(initial_data['paid_invoice'], int)
        self.assertIsInstance(initial_data['income'], str)
        self.assertEqual(initial_data['currency_symbol'], self.company.currency_id.symbol)
        self.assertIsInstance(initial_data['unreconcile_items'], list)
        self.assertIsInstance(initial_data['journal_data'], list)

        # Create a draft invoice and verify open_invoice count increases by 1
        open_count_before = initial_data['open_invoice']
        self._create_test_invoice(move_type='out_invoice', state='draft')
        updated_data = self.Move.get_datas()
        self.assertEqual(updated_data['open_invoice'], open_count_before + 1,
                         "Draft invoice should increment open_invoice count")

        # Verify journal_data structure
        if updated_data['journal_data']:
            journal_entry = updated_data['journal_data'][0]
            self.assertIn('id', journal_entry)
            self.assertIn('name', journal_entry)
            self.assertIn('type', journal_entry)

    def test_get_income_chart(self):
        """Test get_income_chart: validates data structure and calculations for both month and year periods."""
        # Test 'income_this_month'
        month_chart = self.Move.get_income_chart('income_this_month')
        expected_keys = {'income', 'expense', 'date', 'profit'}
        self.assertTrue(expected_keys.issubset(month_chart.keys()),
                        f"get_income_chart('income_this_month') missing keys: {expected_keys - month_chart.keys()}")

        now = fields.Date.today()
        days_in_month = calendar.monthrange(now.year, now.month)[1]
        self.assertEqual(len(month_chart['date']), days_in_month,
                         f"Date list for this month should contain {days_in_month} days")
        self.assertEqual(len(month_chart['income']), days_in_month)
        self.assertEqual(len(month_chart['expense']), days_in_month)
        self.assertEqual(len(month_chart['profit']), days_in_month)

        # Validate profit calculation consistency for every day
        for inc, exp, prof in zip(month_chart['income'], month_chart['expense'], month_chart['profit']):
            self.assertAlmostEqual(prof, inc - exp, places=2,
                                   msg="Profit must equal income minus expense")

        # Test 'income_this_year'
        year_chart = self.Move.get_income_chart('income_this_year')
        self.assertTrue(expected_keys.issubset(year_chart.keys()),
                        f"get_income_chart('income_this_year') missing keys: {expected_keys - year_chart.keys()}")

        self.assertEqual(len(year_chart['date']), 12, "Date list for year should contain 12 months")
        self.assertEqual(len(year_chart['income']), 12)
        self.assertEqual(len(year_chart['expense']), 12)
        self.assertEqual(len(year_chart['profit']), 12)

        for inc, exp, prof in zip(year_chart['income'], year_chart['expense'], year_chart['profit']):
            self.assertAlmostEqual(prof, inc - exp, places=2,
                                   msg="Profit must equal income minus expense")

    def test_get_payment_data(self):
        """Test get_payment_data: returns customer and vendor payments for this_month and this_year."""
        # Create a paid customer invoice
        paid_inv = self._create_test_invoice(
            move_type='out_invoice',
            state='posted',
            payment_state='paid',
            amount=250.0,
            partner=self.partner_customer
        )

        # Create a paid vendor bill
        paid_bill = self._create_test_invoice(
            move_type='in_invoice',
            state='posted',
            payment_state='paid',
            amount=150.0,
            partner=self.partner_vendor
        )

        filters = [
            ('customer_payment', 'this_month'),
            ('customer_payment', 'this_year'),
            ('vendor_payment', 'this_month'),
            ('vendor_payment', 'this_year'),
        ]
        for list_filter, data_filter in filters:
            with self.subTest(list_filter=list_filter, data_filter=data_filter):
                result = self.Move.get_payment_data(list_filter, data_filter)
                self.assertIsInstance(result, list, f"Result for {list_filter} / {data_filter} must be a list")
                for entry in result:
                    self.assertIn('id', entry)
                    self.assertIn('partner', entry)
                    self.assertIn('amount', entry)
                    self.assertIn('date', entry)

        # Check customer payment presence
        cust_payments = self.Move.get_payment_data('customer_payment', 'this_month')
        cust_ids = [p['id'] for p in cust_payments]
        self.assertIn(paid_inv.id, cust_ids, "Paid customer invoice should appear in customer payments")

        # Check vendor payment presence
        vendor_payments = self.Move.get_payment_data('vendor_payment', 'this_month')
        vendor_ids = [p['id'] for p in vendor_payments]
        self.assertIn(paid_bill.id, vendor_ids, "Paid vendor bill should appear in vendor payments")

    def test_get_top_datas(self):
        """Test get_top_datas: aggregates and ranks top customers and vendors descending by total amount."""
        # Create posted bills and invoices with varying amounts
        self._create_test_invoice(move_type='out_invoice', state='posted', amount=500.0, partner=self.partner_customer)
        self._create_test_invoice(move_type='in_invoice', state='posted', amount=300.0, partner=self.partner_vendor)

        for top_filter in ('this_month', 'this_year'):
            with self.subTest(top_filter=top_filter):
                data = self.Move.get_top_datas(top_filter)
                self.assertIn('top_vendors', data)
                self.assertIn('top_customers', data)
                self.assertIsInstance(data['top_vendors'], list)
                self.assertIsInstance(data['top_customers'], list)

                # Validate top_customers entries & descending order
                cust_amounts = [c['amount'] for c in data['top_customers']]
                self.assertEqual(cust_amounts, sorted(cust_amounts, reverse=True),
                                 "Top customers must be sorted in descending order of amount")
                for c in data['top_customers']:
                    self.assertIn('id', c)
                    self.assertIn('name', c)
                    self.assertIn('amount', c)

                # Validate top_vendors entries & descending order
                vendor_amounts = [v['amount'] for v in data['top_vendors']]
                self.assertEqual(vendor_amounts, sorted(vendor_amounts, reverse=True),
                                 "Top vendors must be sorted in descending order of amount")
                for v in data['top_vendors']:
                    self.assertIn('id', v)
                    self.assertIn('name', v)
                    self.assertIn('amount', v)

    def test_get_aged_payable(self):
        """Test get_aged_payable: returns partner and amount lists for aged receivables and aged payables."""
        # Create unpaid posted invoice and bill
        self._create_test_invoice(move_type='out_invoice', state='posted', payment_state='not_paid', amount=400.0, partner=self.partner_customer)
        self._create_test_invoice(move_type='in_invoice', state='posted', payment_state='not_paid', amount=200.0, partner=self.partner_vendor)

        filters = [
            ('aged_receive', 'this_month'),
            ('aged_receive', 'this_year'),
            ('aged_payable', 'this_month'),
            ('aged_payable', 'this_year'),
        ]
        for aged_filter, aged_payable_filter in filters:
            with self.subTest(aged_filter=aged_filter, aged_payable_filter=aged_payable_filter):
                result = self.Move.get_aged_payable(aged_filter, aged_payable_filter)
                self.assertIn('partner', result)
                self.assertIn('amount', result)
                self.assertIsInstance(result['partner'], list)
                self.assertIsInstance(result['amount'], list)
                self.assertEqual(len(result['partner']), len(result['amount']),
                                 "Partner list and amount list must be equal in length")

    def test_get_sale_revenue(self):
        """Test get_sale_revenue: returns top 10 sale revenue customers for month and year."""
        # Create posted customer invoice with revenue
        self._create_test_invoice(move_type='out_invoice', state='posted', amount=600.0, partner=self.partner_customer)

        for period_filter in ('this_month', 'this_year'):
            with self.subTest(period_filter=period_filter):
                result = self.Move.get_sale_revenue(period_filter)
                self.assertIsInstance(result, list)
                self.assertLessEqual(len(result), 10, "Result should have at most 10 records")

                # Validate structure and sort order
                amounts = [r['total_amount'] for r in result]
                self.assertEqual(amounts, sorted(amounts, reverse=True),
                                 "Sale revenue must be sorted descending by total_amount")
                for item in result:
                    self.assertIn('customer_id', item)
                    self.assertIn('customer', item)
                    self.assertIn('total_amount', item)
                    self.assertIsInstance(item['total_amount'], (int, float))

    def test_get_bank_balance(self):
        """Test get_bank_balance: returns bank and cash journal balances with name, balance, and id."""
        result = self.Move.get_bank_balance()
        self.assertIsInstance(result, list, "get_bank_balance() must return a list")

        for item in result:
            self.assertIn('name', item)
            self.assertIn('balance', item)
            self.assertIn('id', item)
            self.assertIsInstance(item['balance'], (int, float))
            self.assertIsInstance(item['name'], str)
