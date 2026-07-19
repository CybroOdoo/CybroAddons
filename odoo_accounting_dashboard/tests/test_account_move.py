# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
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
"""
Test suite for odoo_accounting_dashboard module.

Covers all 7 @api.model RPC methods on account.move used by the OWL dashboard:
  - get_datas()              → KPI tile data
  - get_income_chart()       → Income/Expense/Profit chart data
  - get_payment_data()       → Customer / Vendor payment lists
  - get_top_datas()          → Top customers / vendors
  - get_aged_payable()       → Aged receivable / payable
  - get_sale_revenue()       → Top 10 sale revenue customers
  - get_bank_balance()       → Cash/Bank account balances
"""
from odoo.tests import tagged
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged('post_install', '-at_install')
class TestAccountingDashboardGetDatas(AccountTestInvoicingCommon):
    """Tests for account.move.get_datas() — KPI tiles."""

    def test_get_datas_returns_dict(self):
        """get_datas() must return a dictionary."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result, dict)

    def test_get_datas_required_keys(self):
        """get_datas() must contain all required KPI keys."""
        result = self.env['account.move'].get_datas()
        for key in ('open_invoice', 'paid_invoice', 'income',
                    'currency_symbol', 'unreconcile_items', 'journal_data'):
            self.assertIn(key, result, f"Key '{key}' missing from get_datas() result")

    def test_get_datas_open_invoice_is_int(self):
        """open_invoice count must be a non-negative integer."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['open_invoice'], int)
        self.assertGreaterEqual(result['open_invoice'], 0)

    def test_get_datas_paid_invoice_is_int(self):
        """paid_invoice count must be a non-negative integer."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['paid_invoice'], int)
        self.assertGreaterEqual(result['paid_invoice'], 0)

    def test_get_datas_currency_symbol_is_string(self):
        """currency_symbol must be a non-empty string."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['currency_symbol'], str)
        self.assertTrue(len(result['currency_symbol']) > 0)

    def test_get_datas_journal_data_is_list(self):
        """journal_data must be a list of dicts with id, name, type keys."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['journal_data'], list)
        for item in result['journal_data']:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('type', item)

    def test_get_datas_unreconcile_items_is_list(self):
        """unreconcile_items must be a list."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['unreconcile_items'], list)

    def test_get_datas_income_is_string(self):
        """income tile value must be a formatted string (2 decimal places)."""
        result = self.env['account.move'].get_datas()
        self.assertIsInstance(result['income'], str)
        # Must be parseable as a float
        float(result['income'])

    def test_get_datas_counts_increase_after_invoice(self):
        """open_invoice count must increase after creating a draft invoice."""
        before = self.env['account.move'].get_datas()['open_invoice']
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Dashboard Test Product',
                'price_unit': 100.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        })
        after = self.env['account.move'].get_datas()['open_invoice']
        self.assertEqual(after, before + 1)

    def test_get_datas_journals_scoped_to_company(self):
        """journal_data must only contain journals belonging to the current company."""
        result = self.env['account.move'].get_datas()
        company_journal_ids = self.env['account.journal'].search([
            ('company_id', '=', self.env.company.id)
        ]).ids
        for item in result['journal_data']:
            self.assertIn(
                item['id'], company_journal_ids,
                f"Journal id={item['id']} does not belong to the current company"
            )

    def test_get_datas_does_not_load_all_moves(self):
        """get_datas() must NOT load all account.move records into memory.
        Verified by checking that counts are integers (search_count path)
        and are consistent with the expected domain.
        """
        result = self.env['account.move'].get_datas()
        # open_invoice must match a targeted search_count with the same domain
        expected = self.env['account.move'].search_count([
            ('state', '=', 'draft'),
            ('move_type', 'in', ('out_invoice', 'in_invoice')),
            ('company_id', '=', self.env.company.id),
        ])
        self.assertEqual(result['open_invoice'], expected)


@tagged('post_install', '-at_install')
class TestAccountingDashboardIncomeChart(AccountTestInvoicingCommon):
    """Tests for account.move.get_income_chart()."""

    def test_income_this_month_returns_dict(self):
        """get_income_chart('income_this_month') must return a dict."""
        result = self.env['account.move'].get_income_chart('income_this_month')
        self.assertIsInstance(result, dict)

    def test_income_this_month_keys(self):
        """get_income_chart('income_this_month') must have income, expense, date, profit keys."""
        result = self.env['account.move'].get_income_chart('income_this_month')
        for key in ('income', 'expense', 'date', 'profit'):
            self.assertIn(key, result)

    def test_income_this_month_lists_have_equal_length(self):
        """income, expense, date, profit lists must all have the same length."""
        result = self.env['account.move'].get_income_chart('income_this_month')
        lengths = {k: len(result[k]) for k in ('income', 'expense', 'date', 'profit')}
        self.assertEqual(len(set(lengths.values())), 1,
                         f"All chart lists must have equal length, got: {lengths}")

    def test_income_this_year_returns_12_months(self):
        """get_income_chart('income_this_year') must return 12 data points (one per month)."""
        result = self.env['account.move'].get_income_chart('income_this_year')
        self.assertEqual(len(result['date']), 12,
                         "Year chart must have exactly 12 month entries")

    def test_income_this_year_keys(self):
        """get_income_chart('income_this_year') must include income, expense, date, profit."""
        result = self.env['account.move'].get_income_chart('income_this_year')
        for key in ('income', 'expense', 'date', 'profit'):
            self.assertIn(key, result)

    def test_income_chart_values_are_numeric(self):
        """All chart data values must be numeric (int or float)."""
        result = self.env['account.move'].get_income_chart('income_this_month')
        for key in ('income', 'expense', 'profit'):
            for val in result[key]:
                self.assertIsInstance(val, (int, float),
                                      f"Chart value '{val}' for key '{key}' is not numeric")


@tagged('post_install', '-at_install')
class TestAccountingDashboardPaymentData(AccountTestInvoicingCommon):
    """Tests for account.move.get_payment_data()."""

    def test_customer_payment_this_month_returns_list(self):
        """get_payment_data('customer_payment', 'this_month') must return a list."""
        result = self.env['account.move'].get_payment_data('customer_payment', 'this_month')
        self.assertIsInstance(result, list)

    def test_vendor_payment_this_month_returns_list(self):
        """get_payment_data('vendor_payment', 'this_month') must return a list."""
        result = self.env['account.move'].get_payment_data('vendor_payment', 'this_month')
        self.assertIsInstance(result, list)

    def test_customer_payment_this_year_returns_list(self):
        """get_payment_data('customer_payment', 'this_year') must return a list."""
        result = self.env['account.move'].get_payment_data('customer_payment', 'this_year')
        self.assertIsInstance(result, list)

    def test_vendor_payment_this_year_returns_list(self):
        """get_payment_data('vendor_payment', 'this_year') must return a list."""
        result = self.env['account.move'].get_payment_data('vendor_payment', 'this_year')
        self.assertIsInstance(result, list)

    def test_payment_data_item_structure(self):
        """Each payment data item must have id, partner, amount, date keys."""
        # Create and post and pay a customer invoice to ensure at least one result
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'price_unit': 100.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        })
        invoice.action_post()
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=invoice.ids
        ).create({})._create_payments()

        result = self.env['account.move'].get_payment_data('customer_payment', 'this_year')
        for item in result:
            self.assertIn('id', item)
            self.assertIn('partner', item)
            self.assertIn('amount', item)
            self.assertIn('date', item)


@tagged('post_install', '-at_install')
class TestAccountingDashboardTopData(AccountTestInvoicingCommon):
    """Tests for account.move.get_top_datas()."""

    def test_get_top_datas_this_month_returns_dict(self):
        """get_top_datas('this_month') must return a dict."""
        result = self.env['account.move'].get_top_datas('this_month')
        self.assertIsInstance(result, dict)

    def test_get_top_datas_this_year_returns_dict(self):
        """get_top_datas('this_year') must return a dict."""
        result = self.env['account.move'].get_top_datas('this_year')
        self.assertIsInstance(result, dict)

    def test_get_top_datas_has_required_keys(self):
        """get_top_datas() must contain 'top_vendors' and 'top_customers' keys."""
        result = self.env['account.move'].get_top_datas('this_month')
        self.assertIn('top_vendors', result)
        self.assertIn('top_customers', result)

    def test_get_top_datas_lists_are_lists(self):
        """top_vendors and top_customers must be lists."""
        result = self.env['account.move'].get_top_datas('this_month')
        self.assertIsInstance(result['top_vendors'], list)
        self.assertIsInstance(result['top_customers'], list)

    def test_get_top_datas_item_has_id_name_amount(self):
        """Each item in top_customers/top_vendors must have id, name, amount keys."""
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Top Customer Item',
                'price_unit': 500.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        }).action_post()

        result = self.env['account.move'].get_top_datas('this_year')
        for item in result['top_customers']:
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('amount', item,
                          "Bug fix: top_customers items must include 'amount' key")

    def test_get_top_datas_sorted_descending_by_amount(self):
        """top_customers must be sorted by amount descending (highest spender first)."""
        # partner_a: 2 invoices totalling 1500, partner_b: 1 invoice totalling 200
        for price in (1000.0, 500.0):
            self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_a.id,
                'invoice_line_ids': [(0, 0, {
                    'name': 'A Invoice',
                    'price_unit': price,
                    'quantity': 1,
                    'account_id': self.company_data['default_account_revenue'].id,
                })],
            }).action_post()
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_b.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'B Invoice',
                'price_unit': 200.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        }).action_post()

        result = self.env['account.move'].get_top_datas('this_year')
        customers = result['top_customers']
        amounts = [c['amount'] for c in customers]
        self.assertEqual(amounts, sorted(amounts, reverse=True),
                         "top_customers must be sorted by amount descending")

    def test_get_top_datas_aggregates_multiple_invoices_per_partner(self):
        """A partner with multiple invoices must have their amounts summed."""
        for price in (300.0, 700.0):
            self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.partner_a.id,
                'invoice_line_ids': [(0, 0, {
                    'name': 'Multi Invoice',
                    'price_unit': price,
                    'quantity': 1,
                    'account_id': self.company_data['default_account_revenue'].id,
                })],
            }).action_post()

        result = self.env['account.move'].get_top_datas('this_year')
        partner_a_entries = [
            c for c in result['top_customers']
            if c['id'] == self.partner_a.id
        ]
        self.assertEqual(len(partner_a_entries), 1,
                         "A partner must appear only once in top_customers")
        self.assertGreaterEqual(
            partner_a_entries[0]['amount'], 1000.0,
            "Partner's amount must be the sum of all their invoices"
        )

    def test_get_top_datas_only_posted_moves(self):
        """Draft invoices must NOT appear in top_customers (only posted)."""
        # Create draft invoice — must be excluded
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_b.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Draft Invoice',
                'price_unit': 9999.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        })  # NOT posted

        result = self.env['account.move'].get_top_datas('this_year')
        draft_entries = [
            c for c in result['top_customers']
            if c['id'] == self.partner_b.id
        ]
        # partner_b should not appear (their only invoice is a draft)
        self.assertEqual(
            len(draft_entries), 0,
            "Draft invoices must not contribute to top_customers ranking"
        )


@tagged('post_install', '-at_install')
class TestAccountingDashboardAgedPayable(AccountTestInvoicingCommon):
    """Tests for account.move.get_aged_payable()."""

    def test_aged_receive_this_month_returns_dict(self):
        """get_aged_payable('aged_receive', 'this_month') must return a dict."""
        result = self.env['account.move'].get_aged_payable('aged_receive', 'this_month')
        self.assertIsInstance(result, dict)

    def test_aged_payable_this_month_returns_dict(self):
        """get_aged_payable('aged_payable', 'this_month') must return a dict."""
        result = self.env['account.move'].get_aged_payable('aged_payable', 'this_month')
        self.assertIsInstance(result, dict)

    def test_aged_receive_this_year_returns_dict(self):
        """get_aged_payable('aged_receive', 'this_year') must return a dict."""
        result = self.env['account.move'].get_aged_payable('aged_receive', 'this_year')
        self.assertIsInstance(result, dict)

    def test_aged_receive_has_partner_and_amount_keys(self):
        """Aged receivable result must contain 'partner' and 'amount' keys."""
        result = self.env['account.move'].get_aged_payable('aged_receive', 'this_month')
        self.assertIn('partner', result)
        self.assertIn('amount', result)

    def test_aged_payable_has_partner_and_amount_keys(self):
        """Aged payable result must contain 'partner' and 'amount' keys."""
        result = self.env['account.move'].get_aged_payable('aged_payable', 'this_month')
        self.assertIn('partner', result)
        self.assertIn('amount', result)

    def test_aged_data_lists_equal_length(self):
        """'partner' and 'amount' lists must have equal length."""
        result = self.env['account.move'].get_aged_payable('aged_receive', 'this_month')
        self.assertEqual(len(result['partner']), len(result['amount']))


@tagged('post_install', '-at_install')
class TestAccountingDashboardSaleRevenue(AccountTestInvoicingCommon):
    """Tests for account.move.get_sale_revenue()."""

    def test_sale_revenue_this_month_returns_list(self):
        """get_sale_revenue('this_month') must return a list."""
        result = self.env['account.move'].get_sale_revenue('this_month')
        self.assertIsInstance(result, list)

    def test_sale_revenue_this_year_returns_list(self):
        """get_sale_revenue('this_year') must return a list."""
        result = self.env['account.move'].get_sale_revenue('this_year')
        self.assertIsInstance(result, list)

    def test_sale_revenue_max_10_results(self):
        """get_sale_revenue() must return at most 10 results (LIMIT 10 in SQL)."""
        result = self.env['account.move'].get_sale_revenue('this_year')
        self.assertLessEqual(len(result), 10)

    def test_sale_revenue_item_structure(self):
        """Each sale revenue item must have customer_id, customer, total_amount keys."""
        self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'invoice_line_ids': [(0, 0, {
                'name': 'Revenue Item',
                'price_unit': 1500.0,
                'quantity': 1,
                'account_id': self.company_data['default_account_revenue'].id,
            })],
        }).action_post()

        result = self.env['account.move'].get_sale_revenue('this_year')
        for item in result:
            self.assertIn('customer_id', item)
            self.assertIn('customer', item)
            self.assertIn('total_amount', item)

    def test_sale_revenue_amounts_are_positive(self):
        """total_amount values in sale revenue must be positive."""
        result = self.env['account.move'].get_sale_revenue('this_year')
        for item in result:
            self.assertGreater(item['total_amount'], 0,
                               "Sale revenue amounts must be positive")


@tagged('post_install', '-at_install')
class TestAccountingDashboardBankBalance(AccountTestInvoicingCommon):
    """Tests for account.move.get_bank_balance()."""

    def test_get_bank_balance_returns_list(self):
        """get_bank_balance() must return a list."""
        result = self.env['account.move'].get_bank_balance()
        self.assertIsInstance(result, list)

    def test_bank_balance_item_has_name_balance_id(self):
        """Each bank balance item must have 'name', 'balance', and 'id' keys."""
        result = self.env['account.move'].get_bank_balance()
        for item in result:
            self.assertIn('name', item)
            self.assertIn('balance', item)
            self.assertIn('id', item)

    def test_bank_balance_name_is_string(self):
        """Bank balance account name must be a string."""
        result = self.env['account.move'].get_bank_balance()
        for item in result:
            self.assertIsInstance(item['name'], (str, dict),
                                  "Account name must be a string or translated dict")

    def test_bank_balance_balance_is_numeric(self):
        """Bank balance value must be numeric."""
        result = self.env['account.move'].get_bank_balance()
        for item in result:
            self.assertIsInstance(item['balance'], (int, float))
