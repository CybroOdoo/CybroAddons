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
from odoo.tests.common import TransactionCase

class TestInventoryReport(TransactionCase):
    def setUp(self):
        super().setUp()
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
