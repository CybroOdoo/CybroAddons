# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import json
from types import SimpleNamespace
from unittest.mock import Mock

from odoo.tests.common import TransactionCase

from odoo.http import Response
from odoo.addons.inventory_turnover_report_analysis.controllers import (
    inventory_turnover_report_analysis as controller_module,
)

XLSXReportController = controller_module.XLSXReportController


class TestXLSXReportController(TransactionCase):
    def test_get_report_xlsx_returns_response_and_sets_cookie(self):
        response = Response()
        response.set_cookie = Mock()
        report_model = SimpleNamespace(
            with_user=Mock(return_value=SimpleNamespace(
                get_xlsx_report=Mock()
            ))
        )
        fake_request = SimpleNamespace(
            session=SimpleNamespace(uid=7),
            env={'turnover.report': report_model},
            make_response=Mock(return_value=response),
        )
        original_request = controller_module.request
        controller_module.request = fake_request
        try:
            controller = XLSXReportController()
            result = controller.get_report_xlsx(
                model='turnover.report',
                options=json.dumps({'stock_report': []}),
                output_format='xlsx',
                report_name='Inventory Turnover Analysis Report',
            )
        finally:
            controller_module.request = original_request

        self.assertIs(result, response)
        report_model.with_user.assert_called_once_with(7)
        report_model.with_user.return_value.get_xlsx_report.assert_called_once()
        response.set_cookie.assert_called_once()

    def test_get_report_xlsx_returns_error_payload_on_exception(self):
        fake_request = SimpleNamespace(
            session=SimpleNamespace(uid=7),
            env={'turnover.report': SimpleNamespace(
                with_user=Mock(return_value=SimpleNamespace(
                    get_xlsx_report=Mock(side_effect=RuntimeError('boom'))
                ))
            )},
            make_response=Mock(return_value=Response()),
        )
        original_request = controller_module.request
        controller_module.request = fake_request
        try:
            controller = XLSXReportController()
            result = controller.get_report_xlsx(
                model='turnover.report',
                options=json.dumps({'stock_report': []}),
                output_format='xlsx',
                report_name='Inventory Turnover Analysis Report',
            )
        finally:
            controller_module.request = original_request

        self.assertIsNotNone(result)
