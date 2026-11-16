# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrderDashboard(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.SaleOrder = cls.env["sale.order"]
        cls.SaleLine = cls.env["sale.order.line"]
        cls.AccountMove = cls.env["account.move"]

        cls.today = fields.Date.context_today(cls.env.user)

        cls.partner = cls.env["res.partner"].create({
            "name": "Dashboard Test Customer",
            "email": "dashboard.customer@example.com",
        })

        cls.category = cls.env["product.category"].create({
            "name": "Dashboard Test Category",
        })

        income_account = cls.env["account.account"].search([
            ("account_type", "in", ["income", "income_other"]),
            ("company_ids", "in", cls.env.company.id),
        ], limit=1)

        if not income_account:
            income_account = cls.env["account.account"].search([
                ("account_type", "in", ["income", "income_other"]),
            ], limit=1)

        if not income_account:
            raise UserError(
                "An income account is required to run the dashboard tests."
            )

        cls.category.property_account_income_categ_id = income_account

        cls.product_one = cls.env["product.product"].create({
            "name": "Dashboard Product One",
            "type": "consu",
            "categ_id": cls.category.id,
            "list_price": 100.0,
        })

        cls.product_two = cls.env["product.product"].create({
            "name": "Dashboard Product Two",
            "type": "consu",
            "categ_id": cls.category.id,
            "list_price": 200.0,
        })

    def _create_sale_order(
        self,
        product,
        quantity=1.0,
        date_order=None,
        confirm=True,
    ):
        """Create a sale order with one order line."""
        order = self.SaleOrder.create({
            "partner_id": self.partner.id,
            "date_order": date_order or fields.Datetime.now(),
            "order_line": [
                (0, 0, {
                    "product_id": product.id,
                    "product_uom_qty": quantity,
                    "price_unit": product.list_price,
                }),
            ],
        })

        if confirm:
            order.action_confirm()

        return order

    def _create_overdue_invoice(self, order):
        """Create and post an overdue customer invoice from a sale order."""
        invoice = order._create_invoices()

        self.assertTrue(
            invoice,
            "The sale order should generate a customer invoice.",
        )

        invoice.action_post()

        invoice.write({
            "invoice_date_due": self.today - timedelta(days=5),
        })

        return invoice

    # ---------------------------------------------------------
    # DATE RANGE TESTS
    # ---------------------------------------------------------

    def test_01_get_range_this_week(self):
        """The current week should start on Monday and end today."""
        start, end = self.SaleOrder._get_range("this_week")

        expected_start = self.today - timedelta(
            days=self.today.weekday()
        )

        self.assertEqual(start, expected_start)
        self.assertEqual(end, self.today)

    def test_02_get_range_this_month(self):
        """The month filter should start on the first day of the month."""
        start, end = self.SaleOrder._get_range("this_month")

        self.assertEqual(
            start,
            self.today.replace(day=1),
        )
        self.assertEqual(end, self.today)

    def test_03_get_range_this_year(self):
        """The year filter should start on January 1."""
        start, end = self.SaleOrder._get_range("this_year")

        self.assertEqual(
            start,
            self.today.replace(month=1, day=1),
        )
        self.assertEqual(end, self.today)

    def test_04_get_range_custom(self):
        """The custom filter should return the supplied date range."""
        start_date = self.today - timedelta(days=10)
        end_date = self.today

        start, end = self.SaleOrder._get_range(
            "custom",
            start_date,
            end_date,
        )

        self.assertEqual(start, start_date)
        self.assertEqual(end, end_date)

    def test_05_get_range_invalid_custom(self):
        """An end date earlier than the start date should raise an error."""
        start_date = self.today
        end_date = self.today - timedelta(days=1)

        with self.assertRaises(UserError):
            self.SaleOrder._get_range(
                "custom",
                start_date,
                end_date,
            )

    # ---------------------------------------------------------
    # DOMAIN TESTS
    # ---------------------------------------------------------

    def test_06_build_global_domain(self):
        """The global filter should add the correct date conditions."""
        domain = self.SaleOrder._build_global_domain(
            [("state", "=", "sale")],
            {
                "global_filter": "this_month",
            },
        )

        self.assertIn(
            ("state", "=", "sale"),
            domain,
        )

        self.assertIn(
            ("date_order", ">=", self.today.replace(day=1)),
            domain,
        )

        self.assertIn(
            ("date_order", "<=", self.today),
            domain,
        )

    def test_07_select_period_uses_section_filter(self):
        """Select Period should use the relevant section filter."""
        filters = {
            "global_filter": "select_period",
            "product_filter": "this_month",
        }

        domain = self.SaleOrder._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            filters,
            "product_filter",
        )

        self.assertIn(
            ("date_order", ">=", self.today.replace(day=1)),
            domain,
        )

    def test_08_custom_filter_uses_custom_range(self):
        """Custom date filters should be applied to the domain."""
        start_date = self.today - timedelta(days=7)
        end_date = self.today

        domain = self.SaleOrder._build_dashboard_domain(
            [("state", "in", ["sale", "done"])],
            {
                "global_filter": "custom",
                "custom_range": {
                    "from": fields.Date.to_string(start_date),
                    "to": fields.Date.to_string(end_date),
                },
            },
            "product_filter",
        )

        self.assertIn(
            ("date_order", ">=", start_date),
            domain,
        )

        self.assertIn(
            ("date_order", "<=", end_date),
            domain,
        )

    def test_09_top_and_low_product_filters_are_independent(self):
        """Top and least-selling products should use separate filters."""
        filters = {
            "global_filter": "select_period",
            "product_filter": "this_month",
            "low_product_filter": "this_year",
        }

        top_domain = self.SaleOrder._build_dashboard_domain(
            [("order_id.state", "in", ["sale", "done"])],
            filters,
            "product_filter",
            "order_id.date_order",
        )

        low_domain = self.SaleOrder._build_dashboard_domain(
            [("order_id.state", "in", ["sale", "done"])],
            filters,
            "low_product_filter",
            "order_id.date_order",
        )

        self.assertIn(
            (
                "order_id.date_order",
                ">=",
                self.today.replace(day=1),
            ),
            top_domain,
        )

        self.assertIn(
            (
                "order_id.date_order",
                ">=",
                self.today.replace(month=1, day=1),
            ),
            low_domain,
        )

    # ---------------------------------------------------------
    # PRODUCT DATA TESTS
    # ---------------------------------------------------------

    def test_10_top_products_return_quantity(self):
        """Top products should return quantity instead of qty."""
        self._create_sale_order(
            self.product_one,
            quantity=5,
        )

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        product_data = next(
            (
                item
                for item in result["top_products"]
                if item["id"] == self.product_one.id
            ),
            None,
        )

        self.assertTrue(product_data)
        self.assertIn("quantity", product_data)
        self.assertNotIn("qty", product_data)
        self.assertEqual(product_data["quantity"], 5)

    def test_11_lowest_products_return_quantity(self):
        """Least-selling products should return quantity instead of qty."""
        self._create_sale_order(
            self.product_one,
            quantity=2,
        )

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        product_data = next(
            (
                item
                for item in result["lowest_products"]
                if item["id"] == self.product_one.id
            ),
            None,
        )

        self.assertTrue(product_data)
        self.assertIn("quantity", product_data)
        self.assertNotIn("qty", product_data)
        self.assertEqual(product_data["quantity"], 2)

    def test_12_product_category_filter(self):
        """The product category filter should restrict top products."""
        self._create_sale_order(
            self.product_one,
            quantity=3,
        )

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "product_category_id": self.category.id,
            "limit": 10,
        })

        product_ids = [
            item["id"]
            for item in result["top_products"]
        ]

        self.assertIn(self.product_one.id, product_ids)

    def test_13_low_product_category_filter(self):
        """The least-selling category filter should be independent."""
        self._create_sale_order(
            self.product_one,
            quantity=4,
        )

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "low_product_category_id": self.category.id,
            "limit": 10,
        })

        product_ids = [
            item["id"]
            for item in result["lowest_products"]
        ]

        self.assertIn(self.product_one.id, product_ids)

    # ---------------------------------------------------------
    # OVERDUE INVOICE TESTS
    # ---------------------------------------------------------

    def test_14_posted_overdue_invoice_is_included(self):
        """A posted overdue invoice with an outstanding balance is included."""
        order = self._create_sale_order(
            self.product_one,
            quantity=1,
        )

        invoice = self._create_overdue_invoice(order)

        self.assertEqual(invoice.state, "posted")
        self.assertGreater(invoice.amount_residual, 0)

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        overdue_customer = next(
            (
                item
                for item in result["overdue_customers"]
                if item["id"] == self.partner.id
            ),
            None,
        )

        self.assertTrue(overdue_customer)
        self.assertAlmostEqual(
            overdue_customer["amount"],
            invoice.amount_residual,
            places=2,
        )

    def test_15_draft_invoice_is_not_included_as_overdue(self):
        """Draft invoices should not appear in overdue customers."""
        order = self._create_sale_order(
            self.product_one,
            quantity=1,
        )

        invoice = order._create_invoices()

        self.assertTrue(invoice)
        self.assertEqual(invoice.state, "draft")

        invoice.write({
            "invoice_date_due": self.today - timedelta(days=5),
        })

        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        overdue_partner_ids = [
            item["id"]
            for item in result["overdue_customers"]
        ]

        self.assertNotIn(
            self.partner.id,
            overdue_partner_ids,
        )

    # ---------------------------------------------------------
    # DASHBOARD RESPONSE TESTS
    # ---------------------------------------------------------

    def test_16_dashboard_response_contains_expected_keys(self):
        """The dashboard response should contain all required sections."""
        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        expected_keys = [
            "sales_by_team",
            "sales_by_person",
            "top_customers",
            "top_products",
            "lowest_products",
            "overdue_customers",
            "order_status",
            "invoice_status",
            "product_categories",
            "sales_info",
            "new_vs_returning",
        ]

        for key in expected_keys:
            self.assertIn(key, result)

    def test_17_sales_info_contains_expected_values(self):
        """The sales summary should contain all expected tile values."""
        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10,
        })

        sales_info = result["sales_info"]

        expected_keys = [
            "sale_orders",
            "quotation",
            "orders_to_invoice",
            "orders_fully_invoiced",
            "conversion_rate",
            "total_revenue_mtd",
            "total_revenue_ytd",
            "avg_order_value",
        ]

        for key in expected_keys:
            self.assertIn(key, sales_info)

    def test_18_invalid_limit_uses_default(self):
        """An invalid limit should not prevent the dashboard from loading."""
        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": "invalid",
        })

        self.assertIn("top_products", result)
        self.assertIn("lowest_products", result)

    def test_19_limit_is_capped(self):
        """A very large limit should be capped safely."""
        result = self.SaleOrder.get_sales_dashboard_data({
            "global_filter": "this_year",
            "limit": 10000,
        })

        self.assertIn("top_products", result)
        self.assertIn("lowest_products", result)