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
from unittest.mock import MagicMock, patch
from zipfile import ZipFile

from odoo.exceptions import AccessError
from odoo.http import Response
from odoo.tests.common import TransactionCase, tagged
from ..controllers.excel import XLSXReportController


@tagged('post_install', '-at_install')
class TestOne2manyExcelModel(TransactionCase):
    """Unit tests for one2many.report.excel AbstractModel."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['one2many.report.excel']

    def test_clean_data(self):
        """Test clean_data method for string prefixes and non-string types."""
        # Prefixed strings
        self.assertEqual(self.report_model.clean_data("1. First Item"), "First Item")
        self.assertEqual(self.report_model.clean_data("12. Second Item"), "Second Item")
        self.assertEqual(self.report_model.clean_data("999. Description text"), "Description text")

        # Non-prefixed strings
        self.assertEqual(self.report_model.clean_data("Regular Name"), "Regular Name")
        self.assertEqual(self.report_model.clean_data("123"), "123")
        self.assertEqual(self.report_model.clean_data(""), "")

        # Non-string data types
        self.assertEqual(self.report_model.clean_data(42), 42)
        self.assertEqual(self.report_model.clean_data(3.14), 3.14)
        self.assertFalse(self.report_model.clean_data(False))
        self.assertIsNone(self.report_model.clean_data(None))

    def test_get_xlsx_report_basic(self):
        """Test generating XLSX report with typical dataset."""
        names = ['name', 'ref', 'partner_id', 'comment', 'amount']
        data = [
            {
                'name': '1. Test Line 1',
                'ref': 'REF001',
                'partner_id': (1, 'Customer Alpha'),
                'comment': 'This is a normal comment.',
                'amount': 100.50,
            },
            {
                'name': (
                    '2. Test Line 2 with very long description that exceeds default column length'
                ),
                'ref': 'REF002',
                'partner_id': (2, 'Customer Beta'),
                'comment': 'A' * 120,
                'amount': 0.0,
            },
        ]
        response = Response()
        self.report_model.get_xlsx_report(data, names, response)

        excel_bytes = response.get_data()
        self.assertTrue(len(excel_bytes) > 0)
        # Verify valid zip / XLSX archive
        with ZipFile(io.BytesIO(excel_bytes)) as zf:
            self.assertIn('xl/workbook.xml', zf.namelist())
            self.assertIn('xl/worksheets/sheet1.xml', zf.namelist())

    def test_get_xlsx_report_edge_cases(self):
        """Test generating report with edge cases: empty fields, nulls, dicts,
        single/empty tuples.
        """
        names = ['name', 'partner_id', 'is_active', 'lang_dict', 'null_field']
        data = [
            {
                'name': 'Edge Line 1',
                'partner_id': (10,),  # single-element tuple
                'is_active': False,
                'lang_dict': {'en_US': 'English text'},
                'null_field': None,
            },
            {
                'name': 'Edge Line 2',
                'partner_id': (),  # empty tuple
                'is_active': True,
                'lang_dict': {'fr_FR': 'French text'},
                'null_field': False,
            },
            {
                'name': False,
                'partner_id': False,
                'is_active': False,
                'lang_dict': {},
                'null_field': None,
            },
        ]
        response = Response()
        self.report_model.get_xlsx_report(data, names, response)

        excel_bytes = response.get_data()
        self.assertTrue(len(excel_bytes) > 0)
        with ZipFile(io.BytesIO(excel_bytes)) as zf:
            self.assertIn('xl/workbook.xml', zf.namelist())

    def test_get_xlsx_report_empty(self):
        """Test report generation when dataset or names are empty."""
        response_empty_data = Response()
        self.report_model.get_xlsx_report([], ['col1', 'col2'], response_empty_data)
        self.assertTrue(len(response_empty_data.get_data()) > 0)

        response_empty_names = Response()
        self.report_model.get_xlsx_report([], [], response_empty_names)
        self.assertTrue(len(response_empty_names.get_data()) > 0)


@tagged('post_install', '-at_install')
class TestOne2manyExcelController(TransactionCase):
    """Unit tests for XLSXReportController."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.controller = XLSXReportController()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Parent Company',
            'is_company': True,
        })
        cls.child_contact = cls.env['res.partner'].create({
            'name': 'Contact Person',
            'parent_id': cls.partner.id,
        })

    def _mock_request(self, env=None):
        req = MagicMock()
        req.env = env or self.env

        def make_resp(data, headers=None, status=200):
            return Response(data, headers=headers, status=status)

        req.make_response.side_effect = make_resp
        req.not_found.return_value = Response("Not Found", status=404)
        return req

    def test_controller_invalid_model(self):
        """Controller should return 404 for missing or unregistered model."""
        mock_req = self._mock_request()
        with patch('odoo.addons.one2many_excel_report.controllers.excel.request', mock_req):
            res1 = self.controller.get_report_xlsx(current_model='')
            self.assertEqual(res1.status_code, 404)

            res2 = self.controller.get_report_xlsx(current_model='nonexistent.model')
            self.assertEqual(res2.status_code, 404)

    def test_controller_access_denied(self):
        """Controller should return 403 when user does not have read access."""
        mock_req = self._mock_request()
        mock_model = MagicMock()
        mock_model.check_access.side_effect = AccessError("Forbidden")
        mock_req.env = {'res.partner': mock_model}

        with patch('odoo.addons.one2many_excel_report.controllers.excel.request', mock_req):
            res = self.controller.get_report_xlsx(current_model='res.partner')
            self.assertEqual(res.status_code, 403)
            self.assertIn(b"Access Denied", res.get_data())

    def test_controller_unsaved_record_no_data_leak(self):
        """Controller should return empty data when id is False / unsaved (no whole-table dump)."""
        mock_req = self._mock_request()
        with patch('odoo.addons.one2many_excel_report.controllers.excel.request', mock_req):
            for falsy_id in [False, 'false', '0', 'None', '', 'undefined']:
                res = self.controller.get_report_xlsx(
                    current_model='res.partner',
                    id=falsy_id,
                    field='parent_id'
                )
                self.assertEqual(res.status_code, 200)
                self.assertEqual(res.headers.get('Content-Type'), 'application/vnd.ms-excel')
                self.assertIn('excel.xlsx', res.headers.get('Content-Disposition', ''))
                self.assertTrue(len(res.get_data()) > 0)

    def test_controller_saved_record_export(self):
        """Controller should export child lines when a valid record id and field are passed."""
        mock_req = self._mock_request()
        with patch('odoo.addons.one2many_excel_report.controllers.excel.request', mock_req):
            res = self.controller.get_report_xlsx(
                report_name='partner_contacts',
                current_model='res.partner',
                id=self.partner.id,
                field='parent_id'
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get('Content-Type'), 'application/vnd.ms-excel')
            self.assertIn('partner_contacts.xlsx', res.headers.get('Content-Disposition', ''))
            excel_bytes = res.get_data()
            self.assertTrue(len(excel_bytes) > 0)
            with ZipFile(io.BytesIO(excel_bytes)) as zf:
                self.assertIn('xl/workbook.xml', zf.namelist())

    def test_controller_exception_handling(self):
        """Controller should catch exceptions and return a serialized JSON error."""
        mock_req = self._mock_request()
        mock_report_obj = MagicMock()
        mock_report_obj.get_xlsx_report.side_effect = RuntimeError("Generation failed")

        mock_env = MagicMock()
        mock_env.__contains__.side_effect = lambda key: True

        def _mock_getitem(key):
            if key == 'one2many.report.excel':
                return mock_report_obj
            return self.env[key]

        mock_env.__getitem__.side_effect = _mock_getitem
        mock_req.env = mock_env

        with patch('odoo.addons.one2many_excel_report.controllers.excel.request', mock_req):
            res = self.controller.get_report_xlsx(
                current_model='res.partner',
                id=self.partner.id,
                field='parent_id'
            )
            self.assertEqual(res.status_code, 200)
            response_data = res.get_data()
            self.assertIn(b'Odoo Server Error', response_data)
            self.assertIn(b'200', response_data)
