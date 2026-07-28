# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from datetime import date
from odoo.tests.common import TransactionCase

REPORT_MODEL = 'report.top_selling_product_report.top_selling_reports'


class TestTopSellingReport(TransactionCase):
    """Test suite for the TopSellingReport abstract model.

    Tests cover the _get_report_values() method for every supported
    date_option value, limit handling, least-selling mode, warehouse
    filtering, and the structure of the returned data.

    Two products with different sale quantities are created so that sort-order
    tests (top-selling vs. least-selling) are meaningful:
        product  → qty 10 (higher seller)
        product2 → qty  5 (lower seller)
    """

    @classmethod
    def setUpClass(cls):
        """Create shared test fixtures: two products and two confirmed sale orders."""
        super().setUpClass()

        cls.report_model = cls.env[REPORT_MODEL]
        cls.company = cls.env.ref('base.main_company')
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )

        # Common customer partner
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer TopSelling',
            'customer_rank': 1,
        })

        # --- Product 1 (high seller: qty 10) ---
        cls.product = cls.env['product.product'].create({
            'name': 'Test Top Selling Product A',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 50.0,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 10,
                'price_unit': 100.0,
            })],
        })
        cls.sale_order.action_confirm()

        # --- Product 2 (low seller: qty 5) ---
        cls.product2 = cls.env['product.product'].create({
            'name': 'Test Top Selling Product B',
            'type': 'consu',
            'list_price': 80.0,
            'standard_price': 40.0,
        })
        cls.sale_order2 = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'company_id': cls.company.id,
            'order_line': [(0, 0, {
                'product_id': cls.product2.id,
                'product_uom_qty': 5,
                'price_unit': 80.0,
            })],
        })
        cls.sale_order2.action_confirm()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_data(self, date_option='days', period='10', least=False,
                   from_date=None, to_date=None, warehouse=None):
        """Build a data dict that matches what action_print_report sends."""
        return {
            'date': date_option,
            # Empty string → limit_value = None inside _get_report_values
            'period': str(period) if period else '',
            'least': least,
            'from_date': from_date,
            'to_date': to_date,
            'company': [self.company.id],
            'warehouse': [warehouse] if warehouse else [],
        }

    def _call_report(self, data):
        """Invoke _get_report_values and return the result dict."""
        return self.report_model._get_report_values(docids=None, data=data)

    # ------------------------------------------------------------------
    # Return-value structure
    # ------------------------------------------------------------------

    def test_01_return_value_has_data_and_other_keys(self):
        """_get_report_values must return a dict with 'data' and 'other'."""
        result = self._call_report(self._base_data())
        self.assertIsInstance(result, dict, "Result must be a dict.")
        self.assertIn('data', result, "Result must contain 'data' key.")
        self.assertIn('other', result, "Result must contain 'other' key.")

    def test_02_other_dict_has_required_keys(self):
        """The 'other' sub-dict must contain all expected metadata keys."""
        result = self._call_report(self._base_data())
        other = result['other']
        for key in ('limit', 'least', 'range', 'date_selected_from',
                    'date_selected_to'):
            self.assertIn(key, other, f"'other' must contain key '{key}'.")

    def test_03_data_items_have_required_keys(self):
        """Each item in 'data' must have product_name, sold_quantity, uom.

        We use period='' (no limit) and curr_year so our confirmed orders
        are guaranteed to be within the date range, ensuring data is non-empty.
        """
        result = self._call_report(self._base_data(
            date_option='curr_year', period='',
        ))
        self.assertTrue(
            result['data'],
            "Expected at least one product in data — check that test sale "
            "orders are confirmed and within the current year.",
        )
        for item in result['data']:
            self.assertIn('product_name', item,
                          "Each item must have 'product_name'.")
            self.assertIn('sold_quantity', item,
                          "Each item must have 'sold_quantity'.")
            self.assertIn('uom', item,
                          "Each item must have 'uom'.")

    # ------------------------------------------------------------------
    # Date option: 'days'
    # ------------------------------------------------------------------

    def test_04_date_option_days(self):
        """date_option='days' sets range label to 'Last 10 Days' and leaves
        date_selected_from / date_selected_to as None."""
        result = self._call_report(self._base_data(date_option='days'))
        self.assertEqual(result['other']['range'], 'Last 10 Days')
        self.assertIsNone(result['other']['date_selected_from'])
        self.assertIsNone(result['other']['date_selected_to'])

    # ------------------------------------------------------------------
    # Date option: 'curr_month'
    # ------------------------------------------------------------------

    def test_05_date_option_curr_month(self):
        """date_option='curr_month' sets range label to 'Current Month'."""
        result = self._call_report(self._base_data(date_option='curr_month'))
        self.assertEqual(result['other']['range'], 'Current Month')
        self.assertIsNone(result['other']['date_selected_from'])
        self.assertIsNone(result['other']['date_selected_to'])

    # ------------------------------------------------------------------
    # Date option: 'last_month'
    # ------------------------------------------------------------------

    def test_06_date_option_last_month(self):
        """date_option='last_month' sets range label to 'Last Month'."""
        result = self._call_report(self._base_data(date_option='last_month'))
        self.assertEqual(result['other']['range'], 'Last Month')
        self.assertIsNone(result['other']['date_selected_from'])
        self.assertIsNone(result['other']['date_selected_to'])

    # ------------------------------------------------------------------
    # Date option: 'curr_year'
    # ------------------------------------------------------------------

    def test_07_date_option_curr_year(self):
        """date_option='curr_year' sets range label to 'Current Year'."""
        result = self._call_report(self._base_data(date_option='curr_year'))
        self.assertEqual(result['other']['range'], 'Current Year')
        self.assertIsNone(result['other']['date_selected_from'])
        self.assertIsNone(result['other']['date_selected_to'])

    # ------------------------------------------------------------------
    # Date option: 'last_year'
    # ------------------------------------------------------------------

    def test_08_date_option_last_year(self):
        """date_option='last_year' sets range label to 'Last Year'."""
        result = self._call_report(self._base_data(date_option='last_year'))
        self.assertEqual(result['other']['range'], 'Last Year')
        self.assertIsNone(result['other']['date_selected_from'])
        self.assertIsNone(result['other']['date_selected_to'])

    # ------------------------------------------------------------------
    # Date option: 'select_period'
    # ------------------------------------------------------------------

    def test_09_date_option_select_period_stores_dates(self):
        """date_option='select_period' stores from/to in 'other' metadata
        and leaves range label as None."""
        from_d = date(date.today().year, 1, 1)
        to_d = date.today()

        result = self._call_report(self._base_data(
            date_option='select_period',
            from_date=from_d,
            to_date=to_d,
        ))

        self.assertEqual(result['other']['date_selected_from'], from_d)
        self.assertEqual(result['other']['date_selected_to'], to_d)
        self.assertIsNone(result['other']['range'])

    def test_10_select_period_range_label_is_none(self):
        """'select_period' must leave the range label as None."""
        result = self._call_report(self._base_data(
            date_option='select_period',
            from_date=date(date.today().year, 1, 1),
            to_date=date.today(),
        ))

        self.assertIsNone(result['other']['range'])

    # ------------------------------------------------------------------
    # Limit / period tests
    # ------------------------------------------------------------------

    def test_11_limit_applied_to_data(self):
        """When period='1', result['data'] must have at most 1 item and
        other['limit'] must equal 1."""
        result = self._call_report(self._base_data(
            date_option='curr_year', period='1',
        ))

        self.assertEqual(result['other']['limit'], 1)
        self.assertLessEqual(
            len(result['data']), 1,
            "Data should be limited to at most 1 product.",
        )

    def test_12_no_limit_when_period_empty(self):
        """When period is '' (empty), limit should be None meaning no cap."""
        result = self._call_report(self._base_data(period=''))

        self.assertIsNone(
            result['other']['limit'],
            "limit must be None when period is empty string.",
        )

    def test_13_limit_stored_in_other(self):
        """The integer converted from period must appear in other['limit']."""
        result = self._call_report(self._base_data(period='7'))

        self.assertEqual(result['other']['limit'], 7)

    # ------------------------------------------------------------------
    # Least-selling mode
    # ------------------------------------------------------------------

    def test_14_least_flag_stored_in_other(self):
        """other['least'] must mirror the 'least' value passed in data."""
        result_top = self._call_report(self._base_data(least=False))
        result_least = self._call_report(self._base_data(least=True))

        self.assertFalse(result_top['other']['least'])
        self.assertTrue(result_least['other']['least'])

    def test_15_top_vs_least_sort_order(self):
        """Top-selling list must be descending; least-selling ascending.

        Two products are confirmed in setUpClass (qty=10 and qty=5) inside
        the current year, so both should appear when filtering by curr_year
        with no limit. With 2+ distinct quantities the sort order is testable.
        """
        data_top = self._base_data(
            date_option='curr_year', period='', least=False,
        )
        data_least = self._base_data(
            date_option='curr_year', period='', least=True,
        )

        result_top = self._call_report(data_top)
        result_least = self._call_report(data_least)

        top_qtys = [r['sold_quantity'] for r in result_top['data']]
        least_qtys = [r['sold_quantity'] for r in result_least['data']]

        # Need at least 2 products to verify ordering is non-trivial
        self.assertGreaterEqual(
            len(top_qtys), 2,
            "Expected at least 2 products to meaningfully test sort order.",
        )

        # Top-selling: descending (highest qty first)
        self.assertEqual(
            top_qtys, sorted(top_qtys, reverse=True),
            "Top-selling list must be in descending quantity order.",
        )

        # Least-selling: ascending (lowest qty first)
        self.assertEqual(
            least_qtys, sorted(least_qtys),
            "Least-selling list must be in ascending quantity order.",
        )

    # ------------------------------------------------------------------
    # Warehouse filter
    # ------------------------------------------------------------------

    def test_16_warehouse_filter_does_not_crash(self):
        """Passing a warehouse ID should not raise any exception."""
        if not self.warehouse:
            self.skipTest("No warehouse configured for main company.")

        result = self._call_report(
            self._base_data(warehouse=self.warehouse.id)
        )

        self.assertIn('data', result)
        self.assertIsInstance(result['data'], list)

    def test_17_no_warehouse_filter_returns_data_list(self):
        """When warehouse list is empty no filter is applied and a list is
        returned. Separately confirm a warehouse-filtered call also returns a
        list — both calls must succeed independently."""
        # Call without warehouse filter
        result_no_wh = self._call_report(self._base_data())
        self.assertIsInstance(result_no_wh['data'], list)

        if self.warehouse:
            # Call with explicit warehouse filter
            result_wh = self._call_report(
                self._base_data(warehouse=self.warehouse.id)
            )

            self.assertIsInstance(result_wh['data'], list)

    # ------------------------------------------------------------------
    # Company filter
    # ------------------------------------------------------------------

    def test_18_single_company_filter(self):
        """Filtering by a single company must succeed and return a list."""
        result = self._call_report(self._base_data())

        self.assertIsInstance(result['data'], list)

    def test_19_all_companies_filter(self):
        """Passing all company IDs should not raise and returns a data list."""
        all_company_ids = self.env['res.company'].search([]).ids

        data = self._base_data()
        data['company'] = all_company_ids

        result = self._call_report(data)

        self.assertIsInstance(result['data'], list)

    # ------------------------------------------------------------------
    # sold_quantity aggregation
    # ------------------------------------------------------------------

    def test_20_sold_quantity_is_positive(self):
        """All sold_quantity values in data must be strictly positive.

        We use curr_year with no limit so our test orders (confirmed today)
        are always included, making the data list non-empty.
        """
        result = self._call_report(self._base_data(
            date_option='curr_year', period='',
        ))

        self.assertTrue(
            result['data'],
            "Expected non-empty data for current year — check that test sale "
            "orders were confirmed successfully.",
        )

        for item in result['data']:
            self.assertGreater(
                item['sold_quantity'], 0,
                f"sold_quantity for '{item['product_name']}' must be > 0.",
            )
