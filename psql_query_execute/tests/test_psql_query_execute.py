# -*- coding: utf-8 -*-
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
import io
import json
import os

from odoo.exceptions import ValidationError
from odoo.modules.module import get_manifest, get_module_path
from odoo.tests.common import HttpCase, TransactionCase, tagged
from odoo.tools import json_default


class MockResponseStream:
    """Mock stream object capturing binary output written by xlsxwriter."""

    def __init__(self):
        self.buffer = io.BytesIO()

    def write(self, data):
        self.buffer.write(data)

    def getvalue(self):
        return self.buffer.getvalue()


class MockResponse:
    """Mock response providing a stream attribute."""

    def __init__(self):
        self.stream = MockResponseStream()


@tagged('post_install', '-at_install')
class TestPsqlQueryExecuteModel(TransactionCase):
    """Test suite for the psql.query model operations, query execution,
    and report generation."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.module_name = 'psql_query_execute'
        cls.mod_path = get_module_path(cls.module_name)

        cls.valid_query = cls.env['psql.query'].create({
            'name': 'Test User Query',
            'query_name': 'SELECT 1 AS num_col, \'hello\' AS text_col',
        })
        cls.empty_result_query = cls.env['psql.query'].create({
            'name': 'Empty Result Query',
            'query_name': 'SELECT id, login FROM res_users WHERE 1 = 0',
        })
        cls.invalid_query = cls.env['psql.query'].create({
            'name': 'Syntax Error Query',
            'query_name': 'SELECT * FROM nonexistent_table_sample_xyz_123',
        })

    def test_01_module_installation_and_manifest(self):
        """Verify module installation state, manifest declarations, and security access."""
        module = self.env['ir.module.module'].search([
            ('name', '=', self.module_name),
        ], limit=1)
        self.assertTrue(module, "psql_query_execute module record should exist.")
        self.assertEqual(
            module.state, 'installed',
            "psql_query_execute should be in 'installed' state.",
        )

        manifest = get_manifest(self.module_name)
        self.assertIn('mail', manifest.get('depends', []))

        # Check declared backend asset file
        backend_assets = manifest.get('assets', {}).get('web.assets_backend', [])
        expected_asset = 'psql_query_execute/static/src/js/action_manager.js'
        self.assertIn(
            expected_asset, backend_assets,
            f"Asset {expected_asset} should be declared in web.assets_backend.",
        )

        # Check physical existence of the asset
        full_asset_path = os.path.join(
            self.mod_path, 'static/src/js/action_manager.js',
        )
        self.assertTrue(
            os.path.exists(full_asset_path),
            f"Static JS file {full_asset_path} must exist.",
        )
        self.assertGreater(os.path.getsize(full_asset_path), 0)

        # Check access rights for base.group_user
        access = self.env.ref('psql_query_execute.access_psql_query', raise_if_not_found=False)
        self.assertTrue(access, "Access rule access_psql_query should exist.")
        self.assertEqual(access.model_id.model, 'psql.query')
        self.assertEqual(access.group_id, self.env.ref('base.group_user'))

    def test_02_record_creation_and_defaults(self):
        """Verify record creation, initial values, and chatter inheritance."""
        record = self.env['psql.query'].create({
            'name': 'Custom Query',
            'query_name': 'SELECT 100 AS score',
        })
        self.assertEqual(record.name, 'Custom Query')
        self.assertEqual(record.query_name, 'SELECT 100 AS score')
        self.assertFalse(record.query_result)

        # Verify mail.thread message posting works
        msg = record.message_post(body='Testing query tracking note')
        self.assertTrue(msg)
        self.assertIn(msg, record.message_ids)

    def test_03_action_execute_query_success(self):
        """Execute a valid query and verify formatted HTML table output."""
        self.valid_query.action_execute_query()
        result_html = self.valid_query.query_result
        self.assertTrue(result_html, "query_result should not be empty after execution.")
        self.assertIn('<table', result_html)
        self.assertIn('num_col', result_html)
        self.assertIn('text_col', result_html)
        self.assertIn('1', result_html)
        self.assertIn('hello', result_html)
        self.assertIn('table-border', result_html)
        self.assertIn('lightblue', result_html)

    def test_04_action_execute_query_multiple_rows(self):
        """Execute query returning multiple rows and verify table row generation."""
        multi_row_query = self.env['psql.query'].create({
            'name': 'Multi Row Query',
            'query_name': "SELECT 'A' AS tag UNION ALL SELECT 'B' AS tag UNION ALL SELECT 'C' AS tag",
        })
        multi_row_query.action_execute_query()
        result_html = multi_row_query.query_result
        self.assertIn('tag', result_html)
        self.assertIn('>A</td>', result_html)
        self.assertIn('>B</td>', result_html)
        self.assertIn('>C</td>', result_html)

    def test_05_action_execute_query_empty_result(self):
        """Execute query matching 0 records and verify table headers with empty rows."""
        self.empty_result_query.action_execute_query()
        result_html = self.empty_result_query.query_result
        self.assertTrue(result_html)
        self.assertIn('login', result_html)
        self.assertIn('<tbody>', result_html)

    def test_06_action_execute_query_syntax_error(self):
        """Executing an invalid query must raise a ValidationError."""
        with self.assertRaises(ValidationError) as error_ctx:
            self.invalid_query.action_execute_query()
        self.assertIn(
            'Error executing SQL query', str(error_ctx.exception),
            "ValidationError should contain SQL execution error description.",
        )

    def test_07_get_report_data_success(self):
        """Verify _get_report_data returns structured dictionary for reporting."""
        data = self.valid_query._get_report_data()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get('model'), 'psql.query')
        self.assertEqual(data.get('ids'), self.valid_query)
        self.assertFalse(data.get('no_value'))
        self.assertEqual(data.get('header'), ['num_col', 'text_col'])
        self.assertEqual(data.get('form'), [(1, 'hello')])
        self.assertTrue(data.get('date'))

    def test_08_get_report_data_error(self):
        """_get_report_data on an invalid query raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.invalid_query._get_report_data()

    def test_09_action_print_query_result_xlsx(self):
        """Verify action_print_query_result_xlsx returns an ir.actions.report dictionary."""
        action = self.valid_query.action_print_query_result_xlsx()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')

        action_data = action.get('data', {})
        self.assertEqual(action_data.get('model'), 'psql.query')
        self.assertEqual(action_data.get('output_format'), 'xlsx')
        self.assertEqual(action_data.get('report_name'), 'Query Report')

        # Verify options is valid JSON
        options_raw = action_data.get('options')
        decoded_options = json.loads(options_raw)
        self.assertEqual(decoded_options.get('model'), 'psql.query')
        self.assertEqual(decoded_options.get('header'), ['num_col', 'text_col'])

    def test_10_get_xlsx_report_generation(self):
        """Verify get_xlsx_report generates valid XLSX workbook with diverse data types."""
        mock_response = MockResponse()
        test_data = {
            'header': ['Col_Str', 'Col_Num', 'Col_Dict', 'Col_None'],
            'form': [
                ['Sample Text', 12345, {'key': 'val'}, None],
                ['Second Row', 67890, {'active': True}, None],
            ],
            'date': '2026-10-29',
        }
        self.valid_query.get_xlsx_report(test_data, mock_response)
        xlsx_bytes = mock_response.stream.getvalue()

        # XLSX files are ZIP archives beginning with the PK magic header
        self.assertTrue(
            xlsx_bytes.startswith(b'PK\x03\x04'),
            "Generated report must be a valid XLSX (ZIP) binary stream.",
        )
        self.assertGreater(
            len(xlsx_bytes), 1000,
            "Generated XLSX report should contain workbook data.",
        )


@tagged('post_install', '-at_install')
class TestPsqlQueryExecuteHttp(HttpCase):
    """HTTP integration tests for the /xlsx_reports endpoint."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_admin = cls.env.ref('base.user_admin')
        cls.query_record = cls.env['psql.query'].create({
            'name': 'HTTP Test Query',
            'query_name': 'SELECT 99 AS val, \'odoo\' AS name_val',
        })

    def test_11_controller_xlsx_reports_download(self):
        """POST to /xlsx_reports generates and downloads the XLSX query report."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        report_data = self.query_record._get_report_data()
        options = json.dumps(report_data, default=json_default)
        report_filename = 'Test_Query_Output'

        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'psql.query',
                'options': options,
                'output_format': 'xlsx',
                'report_name': report_filename,
            },
        )
        self.assertEqual(
            response.status_code, 200,
            "/xlsx_reports endpoint should respond with 200 OK.",
        )
        self.assertEqual(
            response.headers.get('Content-Type'),
            'application/vnd.ms-excel',
            "Content-Type should be application/vnd.ms-excel.",
        )
        disposition = response.headers.get('Content-Disposition', '')
        self.assertIn(
            f"{report_filename}.xlsx", disposition,
            "Content-Disposition should specify the expected filename.",
        )
        # Check binary file integrity
        self.assertTrue(
            response.content.startswith(b'PK\x03\x04'),
            "Downloaded file content must be a valid XLSX document.",
        )
        # Check fileToken cookie
        self.assertIn('fileToken', response.cookies)

    def test_12_controller_xlsx_reports_error_handling(self):
        """POST with invalid parameters returns graceful JSON error response."""
        self.authenticate(self.user_admin.login, self.user_admin.login)

        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'psql.query',
                'options': json.dumps({'header': 123}),
                'output_format': 'xlsx',
                'report_name': 'Error_Report',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Odoo Server Error', response.text)
