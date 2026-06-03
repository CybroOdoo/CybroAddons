# -*- coding: utf-8 -*-

from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase

from odoo.addons.all_in_one_pos_kit.controllers import xlsx_report


class TestXlsxReportController(TransactionCase):

    def test_get_report_xlsx_returns_response_with_file_token(self):
        controller = xlsx_report.TBXLSXReportController()
        report = self.env["pos.report"].create({
            "report_type": "report_by_order",
        })
        cookies = {}

        class FakeResponse:
            stream = SimpleNamespace(write=lambda data: None)

            def set_cookie(self, key, value):
                cookies[key] = value

        def _make_response(body, headers=None):
            return FakeResponse()

        with patch.object(xlsx_report, "request", SimpleNamespace(
            session=SimpleNamespace(uid=self.env.uid),
            env=self.env,
            make_response=_make_response,
        )):
            response = controller.get_report_xlsx.__wrapped__(
                controller,
                "pos.report",
                '{"report_type": "report_by_order"}',
                "xlsx",
                "[]",
                "POS Report",
            )

        self.assertIsInstance(response, FakeResponse)
        self.assertEqual(cookies["fileToken"], "dummy-because-api-expects-one")
