# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
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
from datetime import datetime

class TestDynamicInventoryReport(TransactionCase):
    """Test cases for Dynamic Inventory Report"""

    def setUp(self):
        super(TestDynamicInventoryReport, self).setUp()
        self.report_model = self.env['dynamic.inventory.report']
        
        self.report_transfer = self.report_model.create({
            'report_type': 'report_by_transfers'
        })
        self.report_category = self.report_model.create({
            'report_type': 'report_by_categories'
        })
        self.report_warehouse = self.report_model.create({
            'report_type': 'report_by_warehouse'
        })
        self.report_location = self.report_model.create({
            'report_type': 'report_by_location'
        })

    def test_01_inventory_report_transfers(self):
        """Test report by transfers"""
        option = [self.report_transfer.id]
        result = self.report_model.inventory_report(option)
        self.assertEqual(result.get('type'), 'ir.actions.client')
        self.assertEqual(result.get('name'), 'Inventory Orders')
        self.assertEqual(result['filters'].get('report_type'), 'Report By Transfers')
        self.assertIn('report_lines', result)

    def test_02_inventory_report_categories(self):
        """Test report by categories"""
        option = [self.report_category.id]
        result = self.report_model.inventory_report(option)
        self.assertEqual(result['filters'].get('report_type'), 'Report By Categories')
        self.assertIn('report_lines', result)

    def test_03_inventory_report_warehouse(self):
        """Test report by warehouse"""
        option = [self.report_warehouse.id]
        result = self.report_model.inventory_report(option)
        self.assertEqual(result['filters'].get('report_type'), 'Report By Warehouse')
        self.assertIn('report_lines', result)

    def test_04_inventory_report_location(self):
        """Test report by location"""
        option = [self.report_location.id]
        result = self.report_model.inventory_report(option)
        self.assertEqual(result['filters'].get('report_type'), 'Report By Location')
        self.assertIn('report_lines', result)
        
    def test_05_get_filter_data(self):
        """Test get_filter_data method"""
        option = [self.report_transfer.id]
        filter_data = self.report_model.get_filter_data(option)
        self.assertEqual(filter_data.get('report_type'), 'report_by_transfers')
        
    def test_06_with_dates(self):
        """Test inventory report with dates filter"""
        report_with_dates = self.report_model.create({
            'report_type': 'report_by_transfers',
            'date_from': datetime(2023, 1, 1),
            'date_to': datetime(2023, 12, 31)
        })
        option = [report_with_dates.id]
        result = self.report_model.inventory_report(option)
        self.assertIn('date_from', result['orders'])
        self.assertIn('date_to', result['orders'])
        
    def test_07_invalid_report_type(self):
        """Test inventory report with an undefined/fallback report type"""
        report_invalid = self.report_model.create({
            'report_type': 'invalid_type'
        })
        option = [report_invalid.id]
        result = self.report_model.inventory_report(option)
        self.assertEqual(result['filters'].get('report_type'), 'report_by_transfers')
