import io
import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.account_day_book.controllers.account_day_book import (
    XLSXReportController,
)


class FakeResponse:

    def __init__(self, body=None, headers=None):
        self.body = body
        self.headers = headers or []
        self.cookies = {}
        self.stream = io.BytesIO()

    def set_cookie(self, key, value):
        self.cookies[key] = value


class FakeReportModel:

    def __init__(self, fail=False):
        self.fail = fail
        self.called_with = None

    def with_user(self, uid):
        self.uid = uid
        return self

    def get_xlsx_report(self, options, response):
        if self.fail:
            raise ValueError('Controller test failure')
        self.called_with = (options, response)
        response.stream.write(b'test-xlsx-content')


class FakeRequest:

    def __init__(self, report_model):
        self.session = type('Session', (), {'uid': 42})()
        self.report_model = report_model
        self.env = {'account.day.book.report': report_model}

    def make_response(self, body, headers=None):
        return FakeResponse(body=body, headers=headers)


@tagged('post_install', '-at_install')
class TestXLSXReportController(TransactionCase):

    def _call_controller(self, controller, *args):
        return controller.get_report_xlsx.original_endpoint(
            controller, *args
        )

    def test_get_report_xlsx_returns_xlsx_response(self):
        report_model = FakeReportModel()
        fake_request = FakeRequest(report_model)
        controller = XLSXReportController()
        options = {'form': {'target_move': 'all'}}

        with patch(
                'odoo.addons.account_day_book.controllers.account_day_book.request',
                fake_request,
        ):
            response = self._call_controller(
                controller,
                'account.day.book.report',
                json.dumps(options),
                'xlsx',
                'Day Book',
            )

        self.assertEqual(response.cookies['fileToken'],
                         'dummy-because-api-expects-one')
        self.assertIn(
            ('Content-Type', 'application/vnd.ms-excel'),
            response.headers,
        )
        self.assertEqual(report_model.called_with[0], options)
        self.assertEqual(response.stream.getvalue(), b'test-xlsx-content')

    def test_get_report_xlsx_returns_serialized_error_response(self):
        fake_request = FakeRequest(FakeReportModel(fail=True))
        controller = XLSXReportController()

        with patch(
                'odoo.addons.account_day_book.controllers.account_day_book.request',
                fake_request,
        ):
            response = self._call_controller(
                controller,
                'account.day.book.report',
                json.dumps({'form': {}}),
                'xlsx',
                'Day Book',
            )

        self.assertIn('Odoo Server Error', response.body)
        self.assertIn('Controller test failure', response.body)
