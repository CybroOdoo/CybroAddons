# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
import json

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
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
            "date_from": False,
            "date_to": False,
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

    def test_all_report_types_with_empty_database(self):
        for report_type in (
                "report_by_order", "report_by_order_detail",
                "report_by_product", "report_by_categories",
                "report_by_salesman", "report_by_payment"):
            report = self.env["pos.report"].create({
                "report_type": report_type,
                "date_from": "2020-01-01 00:00:00",
                "date_to": "2030-01-01 00:00:00",
            })
            action = report.pos_report(report.id)
            self.assertEqual(action["tag"], "pos_r")
            self.assertEqual(
                action["orders"]["date_from"], "2020-01-01")
            self.assertTrue(report.get_filter(report.id)["report_type"])
            data = {
                "report_type": report_type,
                "model": report,
                "date_from": report.date_from,
                "date_to": report.date_to,
            }
            self.assertIn("POS", report._get_report_values(data))

    def test_xlsx_report_for_every_type(self):
        for report_type in (
                "report_by_order", "report_by_order_detail",
                "report_by_product", "report_by_categories",
                "report_by_salesman", "report_by_payment"):
            report = self.env["pos.report"].create({
                "report_type": report_type,
            })
            response = type("FakeResponse", (), {"stream": type(
                "FakeStream", (),
                {"write": lambda self, data: setattr(self, "data", data)},
            )()})()
            report.get_pos_xlsx_report(
                json.dumps({"report_type": report_type}),
                response, json.dumps([]))
            self.assertTrue(response.stream.data)

    def test_date_range_validation(self):
        with self.assertRaises(ValidationError):
            self.env["pos.report"].create({
                "report_type": "report_by_order",
                "date_from": "2025-02-01 00:00:00",
                "date_to": "2025-01-01 00:00:00",
            })
