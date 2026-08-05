# -*- coding: utf-8 -*-
###############################################################################
#
# Cybrosys Technologies Pvt. Ltd.
#
# Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
# Author:  Ayana KP (odoo@cybrosys.com)
#
# You can modify it under the terms of the GNU AFFERO
# GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
# You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
# (AGPL v3) along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields
from odoo.tests import TransactionCase
import json


class TestSalesReport(TransactionCase):

    def setUp(self):
        super(TestSalesReport, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        # Reuse an existing product to avoid the NOT NULL constraint on publish_date
        self.product = self.env['product.product'].search(
            [('sale_ok', '=', True)], limit=1
        )
        if not self.product:
            self.product = self.env['product.product'].search([], limit=1)
        self.sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {
                'product_id': self.product.id,
                'product_uom_qty': 1.0,
                'price_unit': 100.0,
            })]
        })
        self.sale_order.action_confirm()

        self.report_wizard = self.env['sales.report'].create({
            'report_type': 'report_by_order',
        })

    def test_sale_report_action(self):
        """Test sale_report action returns correct client action format"""
        action = self.report_wizard.sale_report([self.report_wizard.id])
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'sales_report')
        self.assertIn('orders', action)

    def test_get_filter(self):
        """Test get_filter returns correct formatted strings"""
        filters = self.report_wizard.get_filter([self.report_wizard.id], False, False)
        self.assertEqual(filters.get('report_type'), 'Report By Order')

        report_types = {
            'report_by_order_detail': 'Report By Order Detail',
            'report_by_product': 'Report By Product',
            'report_by_categories': 'Report By Categories',
            'report_by_salesperson': 'Report By Sales Person',
            'report_by_state': 'Report By State'
        }
        for r_type, expected_str in report_types.items():
            self.report_wizard.report_type = r_type
            filters = self.report_wizard.get_filter([self.report_wizard.id], False, False)
            self.assertEqual(filters.get('report_type'), expected_str)

    def test_get_report_values(self):
        """Test getting report values executes without errors and returns expected keys"""
        data = {
            'report_type': 'report_by_order',
            'model': self.env['sales.report'],
        }
        res = self.report_wizard._get_report_values(data)
        self.assertIn('SALE', res)
        self.assertIn('sale_main', res)

    def test_report_types_queries(self):
        """Test that different report queries run without crashing"""
        report_types = [
            'report_by_order', 'report_by_order_detail', 'report_by_product',
            'report_by_categories', 'report_by_salesperson', 'report_by_state'
        ]
        for r_type in report_types:
            data = {'report_type': r_type, 'model': self.env['sales.report']}
            self.report_wizard._get_report_values(data)

    def test_get_sale_xlsx_report(self):
        """Test XLSX report generation handles different report types without crashing"""
        class DummyStream:
            def __init__(self):
                self.output = b''
            def write(self, data):
                self.output += data
                
        class DummyResponse:
            def __init__(self):
                self.stream = DummyStream()
                
        response = DummyResponse()
        
        # Test Report By Order
        data = json.dumps({'report_type': 'report_by_order'})
        report_data_main = [{
            'number': 'SO123', 'date_order': '2023-01-01', 'customer': 'John',
            'sales_man': 'Admin', 'sum': 10, 'amount_total': 100
        }]
        dfrm_data = json.dumps({'filters': {}})
        self.report_wizard.get_sale_xlsx_report(data, response, json.dumps(report_data_main), dfrm_data)
        self.assertTrue(len(response.stream.output) > 0)
