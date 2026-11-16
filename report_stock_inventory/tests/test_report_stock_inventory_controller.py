# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
#############################################################################
import json
from urllib.parse import unquote
from odoo.fields import Command
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestReportStockInventoryController(HttpCase):
    """Test cases for controllers/report_stock_inventory.py."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = cls.env['res.users'].create({
            'name': 'XLSX Report Test User',
            'login': 'xlsx_report_test_user',
            'password': 'xlsx_report_test_pass',
            'email': 'xlsx_report_test_user@example.com',
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.category = cls.env['product.category'].create({'name': 'Controller Test Category'})
        cls.product = cls.env['product.product'].create({
            'name': 'Controller Out Of Stock Product',
            'is_storable': True,
            'categ_id': cls.category.id,
        })

    def test_xlsx_reports_endpoint_out_of_stock(self):
        """POST /xlsx_reports streams an XLSX file for out.of.stock.report."""
        self.authenticate('xlsx_report_test_user', 'xlsx_report_test_pass')
        options = {
            'product_name': self.product.display_name,
            'company_name': self.env.company.name,
            'product_stock': [{
                'name': self.product.name,
                'complete_name': self.category.complete_name,
                'default_code': self.product.default_code or '',
                'company_name': self.env.company.name,
            }],
        }
        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'out.of.stock.report',
                'options': json.dumps(options),
                'output_format': 'xlsx',
                'report_name': 'Inventory Stock Report',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.ms-excel', response.headers.get('Content-Type', ''))
        self.assertIn(
            'Inventory Stock Report.xlsx',
            unquote(response.headers.get('Content-Disposition', '')),
        )
        self.assertEqual(response.cookies.get('fileToken'), 'dummy-because-api-expects-one')
        # XLSX files are ZIP archives starting with PK\x03\x04
        self.assertTrue(response.content.startswith(b'PK\x03\x04'))

    def test_xlsx_reports_endpoint_stock_transfer(self):
        """POST /xlsx_reports streams an XLSX file for stock.transfer.report."""
        self.authenticate('xlsx_report_test_user', 'xlsx_report_test_pass')
        options = {
            'company_name': self.env.company.name,
            'stock_picking': [{
                'picking_name': 'WH/OUT/0001',
                'product_name': self.product.name,
                'scheduled_date': '2026-01-01 00:00:00',
                'date_deadline': '',
                'date_done': '',
                'origin': 'SO001',
                'complete_name': 'WH/Stock',
                'display_name': 'Delivery Orders',
                'company_name': self.env.company.name,
                'state': 'assigned',
            }],
        }
        response = self.url_open(
            '/xlsx_reports',
            data={
                'model': 'stock.transfer.report',
                'options': json.dumps(options),
                'output_format': 'xlsx',
                'report_name': 'Inventory Stock Report',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/vnd.ms-excel', response.headers.get('Content-Type', ''))
        self.assertEqual(response.cookies.get('fileToken'), 'dummy-because-api-expects-one')
        self.assertTrue(response.content.startswith(b'PK\x03\x04'))
