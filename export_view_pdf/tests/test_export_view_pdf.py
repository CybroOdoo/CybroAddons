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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests.common import HttpCase, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestExportViewPdf(TransactionCase):
    """Unit tests for Export View PDF module reports, paperformat, and templates."""

    def test_01_module_is_installed(self):
        """Verify export_view_pdf is installed."""
        module = self.env['ir.module.module'].search([('name', '=', 'export_view_pdf')])
        self.assertTrue(module, "Module export_view_pdf must be registered.")
        self.assertEqual(module.state, 'installed', "Module export_view_pdf should be installed.")

    def test_02_reports_and_paperformat_exist(self):
        """Verify paperformat and report actions exist."""
        paperformat = self.env.ref('export_view_pdf.paperformat_export', raise_if_not_found=False)
        self.assertTrue(paperformat, "Paperformat export_view_pdf.paperformat_export must exist.")
        self.assertEqual(paperformat.orientation, 'Landscape')

        report_ungrouped = self.env.ref('export_view_pdf.ir_exports_pdf_report', raise_if_not_found=False)
        self.assertTrue(report_ungrouped, "Report export_view_pdf.ir_exports_pdf_report must exist.")

        report_grouped = self.env.ref('export_view_pdf.ir_exports_pdf_group_by_report', raise_if_not_found=False)
        self.assertTrue(report_grouped, "Report export_view_pdf.ir_exports_pdf_group_by_report must exist.")

    def test_03_report_pdf_generation(self):
        """Verify that QWeb PDF reports generate without error."""
        sample_ungrouped = {
            'length': [0, 1],
            'record': {
                'header': ['Name', 'Email'],
                'data': [
                    ['Partner 1', 'p1@test.com'],
                    ['Partner 2', 'p2@test.com'],
                ],
            },
        }
        pdf_ungrouped, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'export_view_pdf.ir_exports_pdf_report',
            [1],
            data=sample_ungrouped,
        )
        self.assertTrue(pdf_ungrouped, "Ungrouped PDF report should be generated.")
        self.assertGreater(len(pdf_ungrouped), 1000)

        sample_grouped = {
            'length': [0, 1],
            'record': {
                'header': ['Name', 'Email'],
                'type': ['char'],
                'other': [
                    (
                        {'count': 1},
                        'Group A',
                        [[['Partner 1', 'p1@test.com']]],
                        [],
                    )
                ],
            },
        }
        pdf_grouped, _ = self.env['ir.actions.report']._render_qweb_pdf(
            'export_view_pdf.ir_exports_pdf_group_by_report',
            [1],
            data=sample_grouped,
        )
        self.assertTrue(pdf_grouped, "Grouped PDF report should be generated.")
        self.assertGreater(len(pdf_grouped), 1000)


@tagged('post_install', '-at_install')
class TestExportViewPdfHttp(HttpCase):
    """HTTP integration tests for Export View PDF controllers and assets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner Gamma',
            'email': 'gamma@example.com',
            'phone': '1234500000',
        })

    def _get_admin_user(self):
        return self.env.ref('base.user_admin', raise_if_not_found=False) or self.env['res.users'].search([
            ('share', '=', False),
            ('active', '=', True),
        ], limit=1)

    def test_01_static_assets_served(self):
        """Verify that JavaScript and XML assets are accessible via HTTP."""
        js_res = self.url_open('/export_view_pdf/static/src/js/pdf_export.js')
        self.assertEqual(js_res.status_code, 200, "pdf_export.js must be accessible.")

        dialog_js_res = self.url_open('/export_view_pdf/static/src/js/export_dialog.js')
        self.assertEqual(dialog_js_res.status_code, 200, "export_dialog.js must be accessible.")

        xml_res = self.url_open('/export_view_pdf/static/src/xml/export_dialog.xml')
        self.assertEqual(xml_res.status_code, 200, "export_dialog.xml must be accessible.")

    def test_02_jsonrpc_get_data_ungrouped(self):
        """Verify JSON-RPC /get_data endpoint works for ungrouped data."""
        user = self._get_admin_user()
        if user:
            self.authenticate(user.login, user.login)
            res = self.make_jsonrpc_request('/get_data', {
                'model': 'res.partner',
                'res_ids': [user.partner_id.id],
                'fields': [{'name': 'name', 'label': 'Name'}, {'name': 'email', 'label': 'Email'}],
                'grouped_by': [],
                'context': {},
                'domain': [],
            })
            self.assertIn('header', res)
            self.assertIn('data', res)
            self.assertEqual(res['header'], ['Name', 'Email'])
            self.assertTrue(len(res['data']) >= 1)

    def test_03_jsonrpc_get_data_grouped(self):
        """Verify JSON-RPC /get_data endpoint works for grouped data."""
        user = self._get_admin_user()
        if user:
            self.authenticate(user.login, user.login)
            res = self.make_jsonrpc_request('/get_data', {
                'model': 'res.partner',
                'res_ids': [],
                'fields': [{'name': 'name', 'label': 'Name'}, {'name': 'email', 'label': 'Email'}],
                'grouped_by': ['type'],
                'context': {},
                'domain': [('id', '=', user.partner_id.id)],
            })
            self.assertIn('header', res)
            self.assertIn('other', res)
            self.assertIn('type', res)
            self.assertTrue(len(res['other']) >= 1)

    def test_04_jsonrpc_edge_cases(self):
        """Verify JSON-RPC /get_data handles invalid models, empty fields, and empty data gracefully."""
        user = self._get_admin_user()
        if user:
            self.authenticate(user.login, user.login)

            # Invalid model
            invalid_res = self.make_jsonrpc_request('/get_data', {
                'model': 'non.existent.model',
                'fields': [{'name': 'name', 'label': 'Name'}],
                'grouped_by': [],
                'context': {},
                'domain': [],
            })
            self.assertEqual(invalid_res, {'data': [], 'header': []})

            # Empty fields
            empty_fields_res = self.make_jsonrpc_request('/get_data', {
                'model': 'res.partner',
                'fields': [],
                'res_ids': [user.partner_id.id],
                'grouped_by': [],
                'context': {},
                'domain': [],
            })
            self.assertEqual(empty_fields_res, {'data': [], 'header': []})

            # Empty search result on grouped
            empty_search_res = self.make_jsonrpc_request('/get_data', {
                'model': 'res.partner',
                'fields': [{'name': 'name', 'label': 'Name'}],
                'grouped_by': ['type'],
                'context': {},
                'domain': [('id', '=', 0)],
            })
            self.assertIn('other', empty_search_res)
            self.assertEqual(empty_search_res['other'], [])
