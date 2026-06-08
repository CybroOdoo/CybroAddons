# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
from odoo.tests.common import TransactionCase

class TestInventoryReport(TransactionCase):
    def setUp(self):
        super(TestInventoryReport, self).setUp()
        self.report_transfers = self.env['dynamic.inventory.report'].create({
            'report_type': 'report_by_transfers'
        })
        self.report_categories = self.env['dynamic.inventory.report'].create({
            'report_type': 'report_by_categories'
        })
        self.report_warehouse = self.env['dynamic.inventory.report'].create({
            'report_type': 'report_by_warehouse'
        })
        self.report_location = self.env['dynamic.inventory.report'].create({
            'report_type': 'report_by_location'
        })

    def test_inventory_report_transfers(self):
        # test inventory_report method
        option = [self.report_transfers.id]
        res = self.env['dynamic.inventory.report'].inventory_report(option)
        self.assertEqual(res['type'], 'ir.actions.client')
        self.assertEqual(res['tag'], 's_r')
        self.assertIn('orders', res)
        self.assertEqual(res['filters']['report_type'], 'Report By Transfers')
        self.assertTrue(isinstance(res['report_lines'], list))

    def test_inventory_report_categories(self):
        option = [self.report_categories.id]
        res = self.env['dynamic.inventory.report'].inventory_report(option)
        self.assertEqual(res['filters']['report_type'], 'Report By Categories')

    def test_inventory_report_warehouse(self):
        option = [self.report_warehouse.id]
        res = self.env['dynamic.inventory.report'].inventory_report(option)
        self.assertEqual(res['filters']['report_type'], 'Report By Warehouse')

    def test_inventory_report_location(self):
        option = [self.report_location.id]
        res = self.env['dynamic.inventory.report'].inventory_report(option)
        self.assertEqual(res['filters']['report_type'], 'Report By Location')

    def test_get_filter(self):
        option = [self.report_transfers.id]
        filters = self.env['dynamic.inventory.report'].get_filter(option)
        self.assertEqual(filters['report_type'], 'Report By Transfers')

    def test_get_report_total_value(self):
        data = {'report_type': 'report_by_order'}
        total_val = self.env['dynamic.inventory.report']._get_report_total_value(data, None)
        self.assertTrue(isinstance(total_val, list))
        
        data_product = {'report_type': 'report_by_product'}
        total_product = self.env['dynamic.inventory.report']._get_report_total_value(data_product, None)
        self.assertTrue(isinstance(total_product, list))
