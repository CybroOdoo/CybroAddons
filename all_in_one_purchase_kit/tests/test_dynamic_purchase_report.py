# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import MagicMock
import json

class TestDynamicPurchaseReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.report = cls.env['dynamic.purchase.report'].create({
            'report_type': 'report_by_order'
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Vendor',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })



    def test_get_filter(self):
        """Test get_filter method"""
        filters = self.report.get_filter([self.report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Order')

    def test_get_filter_data(self):
        """Test get_filter_data method"""
        filter_data = self.report.get_filter_data([self.report.id])
        self.assertEqual(filter_data.get('report_type'), 'report_by_order')



    def test_get_purchase_xlsx_report(self):
        """Test get_purchase_xlsx_report writes to response stream"""
        response_mock = MagicMock()
        data = json.dumps({'report_type': 'report_by_order'})
        report_data_main = [{
            'name': 'PO001',
            'date_order': '2026-07-08',
            'partner': 'Test Vendor',
            'salesman': 'Admin',
            'sum': 10,
            'amount_total': 100.0,
        }]
        report_data = json.dumps(report_data_main)
        
        self.report.get_purchase_xlsx_report(data, response_mock, report_data, None)
        self.assertTrue(response_mock.stream.write.called, "Should write to stream")
