import io
import json
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from odoo.addons.psql_query_execute.controllers.psql_query_execute import (
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
            raise ValueError('Controller export failure')
        self.called_with = (options, response)
        response.stream.write(b'xlsx-content')


class FakeRequest:

    def __init__(self, report_model):
        self.session = type('Session', (), {'uid': 42})()
        self.report_model = report_model
        self.env = {'psql.query': report_model}

    def make_response(self, body, headers=None):
        return FakeResponse(body=body, headers=headers)


@tagged('post_install', '-at_install')
class TestXLSXReportController(TransactionCase):

    def _call_controller(self, controller, *args):
        endpoint = getattr(controller.get_report_xlsx, 'original_endpoint',
                           None)
        if endpoint:
            return endpoint(controller, *args)
        return controller.get_report_xlsx(*args)

    def test_get_report_xlsx_returns_xlsx_response(self):
        report_model = FakeReportModel()
        controller = XLSXReportController()
        options = {'header': ['name'], 'form': [['Alpha']]}

        with patch(
                'odoo.addons.psql_query_execute.controllers.'
                'psql_query_execute.request',
                FakeRequest(report_model),
        ):
            response = self._call_controller(
                controller,
                'psql.query',
                json.dumps(options),
                'xlsx',
                'Query Report',
            )

        self.assertEqual(response.cookies['fileToken'],
                         'dummy-because-api-expects-one')
        self.assertIn(
            ('Content-Type', 'application/vnd.ms-excel'),
            response.headers,
        )
        disposition = dict(response.headers)['Content-Disposition']
        self.assertIn('attachment;', disposition)
        self.assertIn('Query%20Report.xlsx', disposition)
        self.assertEqual(report_model.uid, 42)
        self.assertEqual(report_model.called_with[0], options)
        self.assertEqual(response.stream.getvalue(), b'xlsx-content')

    def test_get_report_xlsx_returns_serialized_error_response(self):
        controller = XLSXReportController()

        with patch(
                'odoo.addons.psql_query_execute.controllers.'
                'psql_query_execute.request',
                FakeRequest(FakeReportModel(fail=True)),
        ):
            response = self._call_controller(
                controller,
                'psql.query',
                json.dumps({'header': []}),
                'xlsx',
                'Query Report',
            )

        self.assertIn('Odoo Server Error', response.body)
        self.assertIn('Controller export failure', response.body)
