# -*- coding: utf-8 -*-

from odoo.tests.common import TransactionCase


class TestAllInOnePosKitReport(TransactionCase):

    def test_get_report_values_without_context_returns_default_payload(self):
        report = self.env["report.all_in_one_pos_kit.pos_order_report"]

        values = report._get_report_values([], {"model": "pos.order"})

        self.assertEqual(values["doc_ids"], [])
        self.assertEqual(values["doc_model"], "pos.order")
        self.assertEqual(values["report_main_line_data"], [])
        self.assertEqual(values["Filters"], {})

    def test_get_report_values_with_context_uses_report_data(self):
        report = self.env["report.all_in_one_pos_kit.pos_order_report"].with_context(
            pos_order_report=True,
        )

        values = report._get_report_values([], {
            "model": "pos.order",
            "report_data": {
                "report_lines": [{"name": "Order"}],
                "filters": {"report_type": "Report By Order"},
            },
        })

        self.assertEqual(values["report_main_line_data"], [{"name": "Order"}])
        self.assertEqual(values["Filters"], {"report_type": "Report By Order"})
