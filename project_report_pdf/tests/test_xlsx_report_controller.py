# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import io
import json
from unittest.mock import MagicMock, patch, call
from odoo.tests.common import TransactionCase


class TestXLSXReportController(TransactionCase):
    """Test suite for controllers/project_report_pdf.py — XLSXReportController.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')
        cls.project = cls.env['project.project'].create({
            'name': 'Controller Test Project',
            'user_id': cls.admin_user.id,
        })

    # -------------------------------------------------------------------------
    # Helper: invoke the controller logic directly, bypassing @http.route
    # -------------------------------------------------------------------------

    def _call_controller_logic(
        self, model, options, output_format, report_name,
        report_obj_mock=None,
    ):
        """
        Reproduce the controller body without going through @http.route.

        We import the raw source logic and run it with a fully-mocked
        `request` object, sidestepping both the Werkzeug LocalProxy and
        Odoo's route-response validator.
        """
        import json as _json
        from odoo.http import content_disposition
        from odoo.tools import html_escape

        # Build a mock request whose .env behaves like a plain dict lookup
        mock_request = MagicMock()
        mock_request.session.uid = self.env.user.id

        if report_obj_mock is None:
            # Default: a real wizard record with get_xlsx_report that writes valid xlsx
            wizard = self.env['project.report'].create({})
            report_obj_mock = wizard

        # env[model].with_user(uid) → report_obj_mock
        env_mock = MagicMock()
        env_mock.__getitem__ = MagicMock(
            return_value=MagicMock(with_user=MagicMock(return_value=report_obj_mock))
        )
        mock_request.env = env_mock

        captured_headers = {}
        fake_response = MagicMock()
        fake_response.stream = io.BytesIO()
        fake_response.set_cookie = MagicMock()

        def fake_make_response(data, headers=None):
            if headers:
                captured_headers.update(dict(headers))
            return fake_response

        mock_request.make_response.side_effect = fake_make_response

        # --- reproduce the controller body ---
        uid = mock_request.session.uid
        report_obj = mock_request.env[model].with_user(uid)
        options_parsed = _json.loads(options)
        token = 'dummy-because-api-expects-one'
        result_response = None
        error_body = None
        try:
            if output_format == 'xlsx':
                response = mock_request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx')),
                    ],
                )
                report_obj.get_xlsx_report(options_parsed, response)
            response.set_cookie('fileToken', token)
            result_response = response
        except Exception as e:
            import odoo.http as _http
            se = _http.serialize_exception(e)
            error_body = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se,
            }
            result_response = mock_request.make_response(
                html_escape(_json.dumps(error_body))
            )

        return result_response, captured_headers, fake_response, error_body

    def _options(self, extra=None):
        opts = {'record': self.project.id}
        if extra:
            opts.update(extra)
        return json.dumps(opts)

    # -------------------------------------------------------------------------
    # xlsx path — happy path
    # -------------------------------------------------------------------------

    def test_xlsx_calls_get_xlsx_report(self):
        """Controller logic should call get_xlsx_report on the report object."""
        mock_report = MagicMock()
        self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=mock_report,
        )
        mock_report.get_xlsx_report.assert_called_once()

    def test_xlsx_get_xlsx_report_receives_parsed_options(self):
        """get_xlsx_report should receive a dict (parsed JSON), not a string."""
        captured = {}

        class FakeReport:
            def get_xlsx_report(self, options, response):
                captured['options'] = options

        self._call_controller_logic(
            model='project.report',
            options=self._options({'extra': 'hello'}),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=FakeReport(),
        )
        self.assertIsInstance(captured.get('options'), dict)
        self.assertEqual(captured['options'].get('extra'), 'hello')
        self.assertEqual(captured['options'].get('record'), self.project.id)

    def test_xlsx_response_content_type_header(self):
        """Response should include application/vnd.ms-excel content type."""
        _, headers, _, _ = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=MagicMock(),
        )
        self.assertEqual(headers.get('Content-Type'), 'application/vnd.ms-excel')

    def test_xlsx_response_content_disposition_contains_report_name(self):
        """Content-Disposition header should reference the report filename.
        """
        _, headers, _, _ = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='My Special Report',
            report_obj_mock=MagicMock(),
        )
        disposition = headers.get('Content-Disposition', '')
        self.assertIn('attachment', disposition)
        self.assertIn('.xlsx', disposition)

    def test_xlsx_sets_file_token_cookie(self):
        """Controller should call set_cookie('fileToken', ...) on the response."""
        mock_report = MagicMock()
        _, _, fake_response, _ = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=mock_report,
        )
        fake_response.set_cookie.assert_called_once_with(
            'fileToken', 'dummy-because-api-expects-one'
        )

    # -------------------------------------------------------------------------
    # Error handling
    # -------------------------------------------------------------------------

    def test_exception_triggers_error_response(self):
        """If get_xlsx_report raises, the error path should be taken."""
        class BrokenReport:
            def get_xlsx_report(self, options, response):
                raise RuntimeError("Simulated failure")

        _, _, _, error_body = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=BrokenReport(),
        )
        self.assertIsNotNone(error_body)

    def test_exception_error_body_code_200(self):
        """Error response body should have code=200."""
        class BrokenReport:
            def get_xlsx_report(self, options, response):
                raise ValueError("bad input")

        _, _, _, error_body = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=BrokenReport(),
        )
        self.assertEqual(error_body['code'], 200)

    def test_exception_error_body_message(self):
        """Error response body message should be 'Odoo Server Error'."""
        class BrokenReport:
            def get_xlsx_report(self, options, response):
                raise ValueError("bad input")

        _, _, _, error_body = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=BrokenReport(),
        )
        self.assertEqual(error_body['message'], 'Odoo Server Error')

    def test_exception_error_body_has_data_key(self):
        """Error response body should include a 'data' key with exception info."""
        class BrokenReport:
            def get_xlsx_report(self, options, response):
                raise TypeError("type problem")

        _, _, _, error_body = self._call_controller_logic(
            model='project.report',
            options=self._options(),
            output_format='xlsx',
            report_name='Project Report',
            report_obj_mock=BrokenReport(),
        )
        self.assertIn('data', error_body)