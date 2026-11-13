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
from odoo import fields
from odoo.tests import tagged
from odoo.addons.point_of_sale.tests.common import TestPoSCommon


@tagged("post_install", "-at_install")
class TestPosAnalysisReport(TestPoSCommon):
    """Tests for the POS analysis PDF report values."""

    def setUp(self):
        super().setUp()
        self.config = self.basic_config
        self.session = self.open_new_session()
        self.session.name = "POS Analysis Test Session"
        self.session.flush_recordset(["name"])
        self.report = self.env["report.pos_analysis_report.report_pos_analysis"]

    def _create_pos_order(self, **overrides):
        vals = {
            "name": "POS Analysis Order",
            "pos_reference": "Receipt 001",
            "session_id": self.session.id,
            "config_id": self.config.id,
            "company_id": self.env.company.id,
            "pricelist_id": self.config.pricelist_id.id,
            "partner_id": self.customer.id,
            "date_order": fields.Datetime.to_datetime("2026-01-10 10:00:00"),
            "amount_tax": 5.0,
            "amount_total": 105.0,
            "amount_paid": 105.0,
            "amount_return": 0.0,
        }
        vals.update(overrides)
        return self.env["pos.order"].create(vals)

    def test_get_report_values_filters_orders_and_computes_total(self):
        matching_order = self._create_pos_order(
            name="POS Analysis Matching Order",
            pos_reference="Receipt Matching",
            amount_tax=7.0,
            amount_total=107.0,
            amount_paid=107.0,
        )
        self._create_pos_order(
            name="POS Analysis Other Customer",
            pos_reference="Receipt Other Customer",
            partner_id=self.other_customer.id,
            amount_tax=3.0,
            amount_total=53.0,
            amount_paid=53.0,
        )
        self._create_pos_order(
            name="POS Analysis Outside Date",
            pos_reference="Receipt Outside Date",
            date_order=fields.Datetime.to_datetime("2026-02-10 10:00:00"),
            amount_tax=2.0,
            amount_total=42.0,
            amount_paid=42.0,
        )
        data = {
            "from_date": fields.Date.to_date("2026-01-01"),
            "to_date": fields.Date.to_date("2026-01-31"),
            "pos_session_id": self.session.id,
            "partner_id": self.customer.id,
        }

        values = self.report._get_report_values([matching_order.id], data)

        self.assertEqual(values["doc_ids"], [matching_order.id])
        self.assertEqual(values["data"], data)
        self.assertEqual(values["from_date"], data["from_date"])
        self.assertEqual(values["to_date"], data["to_date"])
        self.assertEqual(values["partner_id"], data["partner_id"])
        self.assertEqual(values["grant_tot"], 100.0)
        self.assertEqual(len(values["result"]), 1)
        self.assertEqual(values["result"][0]["session"], self.session.name)
        self.assertEqual(values["result"][0]["order_ref"], matching_order.name)
        self.assertEqual(values["result"][0]["receipt_ref"], "Receipt Matching")
        self.assertEqual(values["result"][0]["customer"], self.customer.name)
        self.assertEqual(values["result"][0]["sub_total"], 100.0)
        self.assertEqual(values["result"][0]["tax"], 7.0)

    def test_get_report_values_single_day_date_filter(self):
        order = self._create_pos_order(
            name="POS Same Day Order",
            pos_reference="Receipt Same Day",
            date_order=fields.Datetime.to_datetime("2026-01-17 14:30:00"),
            amount_tax=5.0,
            amount_total=105.0,
            amount_paid=105.0,
        )
        data = {
            "from_date": fields.Date.to_date("2026-01-17"),
            "to_date": fields.Date.to_date("2026-01-17"),
            "pos_session_id": False,
            "partner_id": False,
        }

        values = self.report._get_report_values([order.id], data)
        self.assertEqual(len(values["result"]), 1)
        self.assertEqual(values["result"][0]["order_ref"], order.name)
        self.assertEqual(values["result"][0]["sub_total"], 100.0)
        self.assertEqual(values["grant_tot"], 100.0)

    def test_get_report_values_from_date_only_filter(self):
        order_old = self._create_pos_order(
            name="POS Old Order",
            pos_reference="Receipt Old",
            date_order=fields.Datetime.to_datetime("2026-01-15 10:00:00"),
            amount_tax=2.0,
            amount_total=52.0,
            amount_paid=52.0,
        )
        order_new = self._create_pos_order(
            name="POS New Order",
            pos_reference="Receipt New",
            date_order=fields.Datetime.to_datetime("2026-01-18 10:00:00"),
            amount_tax=4.0,
            amount_total=104.0,
            amount_paid=104.0,
        )
        data = {
            "from_date": fields.Date.to_date("2026-01-17"),
            "to_date": False,
            "pos_session_id": False,
            "partner_id": False,
        }

        values = self.report._get_report_values([order_old.id, order_new.id], data)
        order_refs = [r["order_ref"] for r in values["result"]]
        self.assertIn(order_new.name, order_refs)
        self.assertNotIn(order_old.name, order_refs)

    def test_report_qweb_render(self):
        order = self._create_pos_order(
            name="POS Render Order",
            pos_reference="Receipt Render",
            date_order=fields.Datetime.to_datetime("2026-01-17 14:30:00"),
            amount_tax=5.0,
            amount_total=105.0,
            amount_paid=105.0,
        )
        data = {
            "from_date": fields.Date.to_date("2026-01-01"),
            "to_date": fields.Date.to_date("2026-01-31"),
            "pos_session_id": self.session.id,
            "partner_id": self.customer.id,
        }
        report = self.env["ir.actions.report"]
        html = report._render_qweb_html(
            "pos_analysis_report.action_report_pos_analysis",
            [order.id],
            data=data,
        )[0]
        html_str = html.decode("utf-8") if isinstance(html, bytes) else str(html)
        self.assertIn("POS Analysis Report", html_str)
        self.assertIn("Reporting From:", html_str)
        self.assertIn("Reporting To:", html_str)
        self.assertIn("Customer", html_str)
        self.assertIn(self.customer.name, html_str)
        self.assertIn("Receipt Render", html_str)
        self.assertIn("100.00", html_str)
