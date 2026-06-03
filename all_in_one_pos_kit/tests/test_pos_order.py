# -*- coding: utf-8 -*-

from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestPosOrderDashboard(TransactionCase):

    def test_set_pos_exchange_order_marks_order(self):
        order = self.env["pos.order"].new({"exchange": False})

        order.set_pos_exchange_order()

        self.assertTrue(order.exchange)

    def test_dashboard_methods_return_empty_data_shapes(self):
        pos_order = self.env["pos.order"]

        self.assertEqual(pos_order.get_department("pos_hourly_sales")[2], "HOURS")
        self.assertEqual(pos_order.get_department("pos_monthly_sales")[2], "DAYS")
        self.assertEqual(pos_order.get_department("pos_yearly_sales")[2], "MONTHS")
        self.assertIn("payment_details", pos_order.get_details())
        self.assertIn("total_sale", pos_order.get_refund_details())
        for result in (
                pos_order.get_the_top_customer(),
                pos_order.get_the_top_products(),
                pos_order.get_the_top_categories()):
            self.assertEqual(len(result), 2)
            self.assertIsInstance(result[0], list)
            self.assertIsInstance(result[1], list)

    def test_get_invoice_returns_invoice_payload_for_unknown_reference(self):
        result = self.env["pos.order"].get_invoice("UNKNOWN-POS-REF")

        self.assertIn("invoice_id", result)
        self.assertIn("base_url", result)
        self.assertIn("barcode", result)

    def test_sync_from_ui_returns_super_result_without_order_ids(self):
        base_path = "odoo.addons.point_of_sale.models.pos_order.PosOrder.sync_from_ui"
        expected = {"pos.order": []}

        with patch(base_path, return_value=expected):
            result = self.env["pos.order"].sync_from_ui([])

        self.assertEqual(result, expected)


class TestPosOrderLine(TransactionCase):

    def test_get_product_details_without_ids_returns_empty_list(self):
        self.assertEqual(
            self.env["pos.order.line"].get_product_details([]),
            [],
        )
