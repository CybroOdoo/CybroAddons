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
from types import SimpleNamespace
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from odoo.addons.all_in_one_pos_kit.controllers import xlsx_report


@tagged('post_install', '-at_install')
class TestXlsxReportController(TransactionCase):

    def test_get_report_xlsx_returns_response_with_file_token(self):
        controller = xlsx_report.TBXLSXReportController()
        self.env["pos.report"].create({
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
