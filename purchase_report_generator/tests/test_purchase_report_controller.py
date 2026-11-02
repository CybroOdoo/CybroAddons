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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################

import json
from unittest.mock import MagicMock

from odoo import Command
from odoo.exceptions import AccessError
from odoo.http import Response, request_var
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from ..controllers.purchase_report_generator import (
    TBXLSXReportController,
)


class MockRequest:
    """Mock Request object bound via contextvars request_var."""
    def __init__(self, env):
        self.session = MagicMock()
        self.session.uid = env.user.id
        self.env = env
        self.db = env.cr.dbname

    def make_response(self, data=None, headers=None):
        return Response(data, headers=headers)


@tagged('post_install', '-at_install')
class TestPurchaseReportController(TransactionCase):
    """Test suite covering TBXLSXReportController HTTP endpoint logic."""

    def setUp(self):
        super().setUp()
        self.controller = TBXLSXReportController()

    def test_get_report_xlsx_success(self):
        """Test successful XLSX generation via HTTP controller."""
        mock_req = MockRequest(self.env)
        token = request_var.set(mock_req)
        try:
            options = json.dumps({
                'report_type': 'report_by_order',
                'date_from': '2026-01-01 00:00:00',
                'date_to': '2026-12-31 23:59:59',
            })
            report_data = json.dumps([{
                'name': 'PO001',
                'date_order': '2026-10-25 10:00:00',
                'partner': 'Vendor A',
                'salesman': 'Rep A',
                'sum': 10.0,
                'amount_total': 1500.0,
            }])
            dfr_data = json.dumps({'orders': {}})

            response = self.controller.get_report_xlsx(
                model='dynamic.purchase.report',
                options=options,
                output_format='xlsx',
                report_data=report_data,
                report_name='Purchase Orders Report',
                dfr_data=dfr_data,
            )

            self.assertIsInstance(response, Response)
            self.assertEqual(
                response.headers.get('Content-Type'),
                'application/vnd.ms-excel'
            )
            self.assertIn(
                'Purchase%20Orders%20Report.xlsx',
                response.headers.get('Content-Disposition', '')
            )
            self.assertTrue(len(response.data) > 0)
        finally:
            request_var.reset(token)

    def test_get_report_xlsx_exception_handling(self):
        """Test error handling when controller encounters invalid model."""
        mock_req = MockRequest(self.env)
        token = request_var.set(mock_req)
        try:
            # Pass invalid JSON in options to trigger Exception in try block
            response = self.controller.get_report_xlsx(
                model='dynamic.purchase.report',
                options='INVALID_JSON_PAYLOAD',
                output_format='xlsx',
                report_data='[]',
                report_name='Error Report',
                dfr_data='{}',
            )

            self.assertIsInstance(response, Response)
            response_text = response.get_data(as_text=True)
            self.assertIn('Odoo Server Error', response_text)
        finally:
            request_var.reset(token)

    def test_get_report_xlsx_non_xlsx_format(self):
        """Test controller behavior when output_format is not xlsx."""
        mock_req = MockRequest(self.env)
        token = request_var.set(mock_req)
        try:
            response = self.controller.get_report_xlsx(
                model='dynamic.purchase.report',
                options='{}',
                output_format='pdf',
                report_data='[]',
                report_name='Non XLSX Report',
                dfr_data='{}',
            )
            self.assertIsInstance(response, Response)
            response_text = response.get_data(as_text=True)
            self.assertIn('Odoo Server Error', response_text)
        finally:
            request_var.reset(token)

    def test_get_report_xlsx_invalid_model(self):
        """Test that passing a non-report model raises AccessError."""
        mock_req = MockRequest(self.env)
        token = request_var.set(mock_req)
        try:
            with self.assertRaises(AccessError):
                self.controller.get_report_xlsx(
                    model='res.partner',
                    options='{}',
                    output_format='xlsx',
                    report_data='[]',
                    report_name='Invalid Model Report',
                    dfr_data='{}',
                )
        finally:
            request_var.reset(token)

    def test_get_report_xlsx_no_purchase_rights(self):
        """Test that user without purchase access cannot download report."""
        unauthorized_user = self.env['res.users'].create({
            'name': 'No Purchase User Controller',
            'login': 'nopurchase_ctrl',
            'email': 'nopurchase_ctrl@example.com',
            'group_ids': [Command.set([self.env.ref('base.group_user').id])],
        })
        user_env = self.env(user=unauthorized_user)
        mock_req = MockRequest(user_env)
        token = request_var.set(mock_req)
        try:
            with self.assertRaises(AccessError):
                self.controller.get_report_xlsx(
                    model='dynamic.purchase.report',
                    options='{}',
                    output_format='xlsx',
                    report_data='[]',
                    report_name='Unauthorized Report',
                    dfr_data='{}',
                )
        finally:
            request_var.reset(token)
