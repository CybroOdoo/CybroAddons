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
from odoo.fields import Command
from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestManufacturingReports(HttpCase):
    """Test cases for 'XLSXReportController' in manufacturing_reports."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'MRP Report Test User',
            'login': 'mrp_test_user',
            'password': 'test_password',
            'group_ids': [
                Command.link(cls.env.ref('base.group_user').id),
            ],
        })

    def test_get_report_xlsx(self):
        """Test get_report_xlsx controller endpoint returns xlsx binary file."""
        self.authenticate(self.test_user.login, 'test_password')
        data = {
            'date_from': '2026-01-01',
            'state': 'Draft',
            'mrp': [{
                'name': 'MO/00001',
                'product': 'Test Controller Product',
                'quantity': 3.0,
                'unit': 'Units',
                'responsible': 'Administrator',
                'start_date': '2026-01-01',
                'state': 'Draft',
            }],
        }
        res = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'mrp.report.wizard',
                'options': json.dumps(data),
                'output_format': 'xlsx',
                'report_name': 'Manufacturing Report',
            },
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get('Content-Type'), 'application/vnd.ms-excel')
        self.assertIn('Manufacturing', res.headers.get('Content-Disposition', ''))
        self.assertIn('.xlsx', res.headers.get('Content-Disposition', ''))
        self.assertGreater(len(res.content), 0)

    def test_get_report_xlsx_invalid_model(self):
        """Test get_report_xlsx rejects models not in ALLOWED_MODELS whitelist."""
        self.authenticate(self.test_user.login, 'test_password')
        res = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'res.users',
                'options': json.dumps({}),
                'output_format': 'xlsx',
                'report_name': 'Hacked Report',
            },
        )
        self.assertEqual(res.status_code, 400)

