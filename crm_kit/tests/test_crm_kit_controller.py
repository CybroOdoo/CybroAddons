# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.crm_kit.controllers import crm_kit as controller_module


class TestXlsxReportController(TransactionCase):

    def test_get_report_xlsx_returns_response_with_cookie(self):
        controller = controller_module.XLSXReportController()
        wizard = self.env["commission.report"].create({})
        cookies = {}

        class FakeResponse:
            stream = SimpleNamespace(write=lambda data: None)

            def set_cookie(self, key, value):
                cookies[key] = value

        with patch.object(controller_module, "request", SimpleNamespace(
            session=SimpleNamespace(uid=self.env.uid),
            env=self.env,
            make_response=lambda body, headers=None: FakeResponse(),
        )):
            response = controller.get_report_xlsx.__wrapped__(
                controller,
                "commission.report",
                """{
                    "date": "2026-06-02",
                    "date_from": "2026-06-01",
                    "date_to": "2026-06-30",
                    "commission_list": [],
                    "total_list": [],
                    "commission": [],
                    "commission_total": [],
                    "commission_name": [],
                    "commission_salesperson": [],
                    "commission_sales_team": [],
                    "user_commission_name": [],
                    "user_commission_salesperson": []
                }""",
                "xlsx",
                "Commission Report",
            )

        self.assertIsInstance(response, FakeResponse)
        self.assertEqual(cookies["fileToken"], "dummy-because-api-expects-one")
        self.assertTrue(wizard)
