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
import json

from odoo.tests.common import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestWarehouseReportControllers(HttpCase):
    """Test XLSXReportController routes and responses."""

    @classmethod
    def setUpClass(cls):
        """Set up admin user reference for HTTP testing."""
        super().setUpClass()
        cls.admin_user = cls.env.ref('base.user_admin')

    def test_xlsx_reports_route(self):
        """Test POST /xlsx_reports with valid data."""
        self.authenticate(self.admin_user.login, 'admin')

        options_data = {
            'company_name': 'Test Company',
            'stock_valuation': [
                {
                    'create_date': '2026-10-19',
                    'name': 'Valuation Product',
                    'description': 'Test Move',
                    'category_name': 'Goods',
                    'company_name': 'Test Company',
                    'quantity': 5.0,
                    'unit_cost': 20.0,
                    'value': 100.0,
                }
            ],
        }

        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'stock.valuation.report',
                'options': json.dumps(options_data),
                'output_format': 'xlsx',
                'csrf_token': self.csrf_token(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.ms-excel', response.headers.get('Content-Type', ''))
        self.assertTrue(response.content.startswith(b'PK\x03\x04'))

    def test_xlsx_reports_route_error_handling(self):
        """Test POST /xlsx_reports exception handling branch."""
        self.authenticate(self.admin_user.login, 'admin')

        # Invalid data structure in options raises exception inside get_xlsx_report
        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'stock.valuation.report',
                'options': json.dumps({
                    'company_name': 'Test Company',
                    'stock_valuation': 'not_a_list_of_dicts',
                }),
                'output_format': 'xlsx',
                'csrf_token': self.csrf_token(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('Odoo Server Error', response.text)

    def test_xlsx_reports_unauthorized_model(self):
        """Test POST /xlsx_reports rejects models not in ALLOWED_MODELS."""
        self.authenticate(self.admin_user.login, 'admin')

        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'res.users',
                'options': json.dumps({}),
                'output_format': 'xlsx',
                'csrf_token': self.csrf_token(),
            },
        )
        self.assertEqual(response.status_code, 404)
