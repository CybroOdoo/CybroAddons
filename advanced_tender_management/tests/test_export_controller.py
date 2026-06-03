# -*- coding: utf-8 -*-
import json
from types import SimpleNamespace
from unittest.mock import patch

from odoo.addons.advanced_tender_management.controllers.export import XLSXReportController

from .common import TenderManagementTestCommon


class _DummyResponse:
    def __init__(self):
        self.stream = SimpleNamespace(write=lambda data: None)
        self.cookies = {}

    def set_cookie(self, key, value):
        self.cookies[key] = value


class TestExportController(TenderManagementTestCommon):
    """Tests for XLSX export controller."""

    def setUp(self):
        super().setUp()
        self.tender = self.create_tender()

    def test_get_report_xlsx_returns_file_response(self):
        response = _DummyResponse()
        dummy_request = SimpleNamespace(
            session=SimpleNamespace(uid=self.env.uid),
            env=self.env,
            make_response=lambda _data=None, headers=None: response,
        )
        controller = XLSXReportController()

        with patch('odoo.addons.advanced_tender_management.controllers.export.request', dummy_request):
            result = controller.get_report_xlsx(
                'tender.management',
                json.dumps({
                    'tender_product_lines': [{'product_id': 'P1', 'name': 'P1', 'quantity': 1, 'units': 'Unit'}],
                }),
                'xlsx',
                'Tender Report',
            )

        self.assertIs(result, response)
        self.assertEqual(response.cookies['fileToken'], 'dummy-because-api-expects-one')

    def test_get_report_xlsx_returns_serialized_error(self):
        class _Boom:
            def with_user(self, _uid):
                return self

            def get_xlsx_report(self, _options, _response):
                raise ValueError('boom')

        response_values = []
        dummy_request = SimpleNamespace(
            session=SimpleNamespace(uid=self.env.uid),
            env={'boom.model': _Boom()},
            make_response=lambda data=None, headers=None: response_values.append(data) or data,
        )
        controller = XLSXReportController()

        with patch('odoo.addons.advanced_tender_management.controllers.export.request', dummy_request):
            result = controller.get_report_xlsx(
                'boom.model',
                json.dumps({'tender_product_lines': []}),
                'xlsx',
                'Broken',
            )

        self.assertIn('Odoo Server Error', result)
