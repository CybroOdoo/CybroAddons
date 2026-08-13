# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
import json
from odoo.tests.common import HttpCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAllInOnePurchaseKitController(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'Test User XLSX',
            'login': 'test_user_xlsx',
            'password': 'test_password',
            'groups_id': [(6, 0, cls.env.ref('base.group_user').ids)],
        })

    def test_get_report_xlsx_controller(self):
        """Test XLSX report generation via controller."""
        self.authenticate('test_user_xlsx', 'test_password')
        
        payload = {
            'model': 'dynamic.purchase.report',
            'options': json.dumps({'report_type': 'report_by_order'}),
            'output_format': 'xlsx',
            'report_data': json.dumps([
                {
                    'name': 'P00001',
                    'date_order': '2026-06-22',
                    'partner': 'Vendor A',
                    'salesman': 'Salesman A',
                    'sum': 10,
                    'amount_total': 100.0,
                }
            ]),
            'report_name': 'Test_Purchase_Report',
            'dfr_data': json.dumps({}),
        }
        
        response = self.url_open(
            '/purchase_dynamic_xlsx_reports',
            data=payload,
            timeout=15
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get('Content-Type'), 'application/vnd.ms-excel')
        self.assertTrue(response.content)
