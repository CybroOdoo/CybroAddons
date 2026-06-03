# -*- coding: utf-8 -*-

import json
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestPosReport(TransactionCase):

    def test_create_write_and_filter_helpers(self):
        report = self.env["pos.report"].create({
            "report_type": "report_by_product",
        })

        report.write({"report_type": "report_by_payment"})

        self.assertEqual(report.report_type, "report_by_payment")
        self.assertEqual(report.get_filter(report.id), {
            "report_type": "Report By Payment",
        })
        self.assertEqual(report.get_filter_data(report.id), {
            "report_type": "report_by_payment",
        })

    def test_report_value_methods_with_empty_database(self):
        report = self.env["pos.report"].create({
            "report_type": "report_by_order",
        })
        data = {"report_type": "report_by_order", "model": report}

        values = report._get_report_values(data)

        self.assertIn("POS", values)
        self.assertIn("pos_main", values)

    def test_pos_report_action_payload(self):
        report = self.env["pos.report"].create({
            "report_type": "report_by_order",
        })

        action = report.pos_report(report.id)

        self.assertEqual(action["type"], "ir.actions.client")
        self.assertEqual(action["tag"], "pos_r")
        self.assertIn("filters", action)

    def test_get_pos_xlsx_report_writes_response_stream(self):
        report = self.env["pos.report"].create({
            "report_type": "report_by_order",
        })
        response = type("FakeResponse", (), {"stream": type(
            "FakeStream",
            (),
            {"write": lambda self, data: setattr(self, "data", data)},
        )()})()

        report.get_pos_xlsx_report(
            json.dumps({"report_type": "report_by_order"}),
            response,
            json.dumps([]),
        )

        self.assertTrue(response.stream.data)
