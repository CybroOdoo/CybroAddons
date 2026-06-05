# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

import json
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestPoFourwayMatchReportController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_password = 'test123'
        cls.user = cls.env['res.users'].create({
            'name': 'Test User',
            'login': 'test_user',
            'email': 'test@test.com',
            'password': cls.user_password,
        })

    def test_xlsx_report_route(self):
        """Test xlsx report controller."""
        self.authenticate(
            self.user.login,
            self.user_password
        )
        payload = {
            'model': 'fourway.report',
            'options': json.dumps({
                'partner_id': False,
                'order_ids': [],
            }),
            'output_format': 'xlsx',
            'report_name': 'Four Way Matching Report',
        }
        response = self.url_open(
            url='/xlsx_reports',
            data=payload
        )
        self.assertEqual(
            response.status_code,
            200
        )

    def test_invalid_output_format(self):
        """Test invalid output format."""
        self.authenticate(
            self.user.login,
            self.user_password
        )
        payload = {
            'model': 'fourway.report',
            'options': json.dumps({
                'partner_id': False,
                'order_ids': [],
            }),
            'output_format': 'pdf',
            'report_name': 'Four Way Matching Report',
        }
        response = self.url_open(
            url='/xlsx_reports',
            data=payload
        )
        self.assertEqual(
            response.status_code,
            200
        )
