# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#
###############################################################################

import io
import json
from datetime import datetime, timedelta
from odoo.tests import common, tagged


class MockResponse:
    """Mock response object with a stream attribute for testing XLSX report."""

    def __init__(self):
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestInventoryReport(common.TransactionCase):
    """Test suite for inventory_report_generator module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_model = cls.env['dynamic.inventory.report']
        cls.now = datetime.now()
        cls.date_from = (cls.now - timedelta(days=30)).strftime(
            '%Y-%m-%d %H:%M:%S'
        )
        cls.date_to = (cls.now + timedelta(days=30)).strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        # Create basic records for reporting
        cls.test_report = cls.report_model.create({
            'report_type': 'report_by_transfers',
            'date_from': cls.date_from,
            'date_to': cls.date_to,
        })

    def test_01_create_and_write(self):
        """Test record creation and update on dynamic.inventory.report."""
        report = self.report_model.create({
            'report_type': 'report_by_categories',
            'date_from': self.date_from,
            'date_to': self.date_to,
        })
        self.assertTrue(self.report_model._transient)
        self.assertTrue(report.id)
        self.assertEqual(report.report_type, 'report_by_categories')

        # Test write method
        res = report.write({'report_type': 'report_by_warehouse'})
        self.assertTrue(res)
        self.assertEqual(report.report_type, 'report_by_warehouse')

    def test_02_get_filter_and_data(self):
        """Test filter extraction for all report types and fallback."""
        report = self.test_report

        # report_by_transfers
        report.write({'report_type': 'report_by_transfers'})
        filters = report.get_filter([report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Transfers')

        # report_by_categories
        report.write({'report_type': 'report_by_categories'})
        filters = report.get_filter([report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Categories')

        # report_by_warehouse
        report.write({'report_type': 'report_by_warehouse'})
        filters = report.get_filter([report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Warehouse')

        # report_by_location
        report.write({'report_type': 'report_by_location'})
        filters = report.get_filter([report.id])
        self.assertEqual(filters.get('report_type'), 'Report By Location')

        # fallback
        filter_dict = report.get_filter_data([report.id])
        self.assertIn('report_type', filter_dict)

    def test_03_get_report_sub_lines_all_types(self):
        """Test _get_report_sub_lines with and without date filters."""
        report = self.test_report

        for r_type in [
            'report_by_transfers',
            'report_by_categories',
            'report_by_warehouse',
            'report_by_location',
        ]:
            # With dates
            data_with_dates = {
                'report_type': r_type,
                'date_from': self.date_from,
                'date_to': self.date_to,
                'model': report,
            }
            sub_lines = report._get_report_sub_lines(
                data_with_dates, [r_type], self.date_from, self.date_to
            )
            self.assertIsInstance(sub_lines, list)

            # Without dates
            data_no_dates = {
                'report_type': r_type,
                'model': report,
            }
            sub_lines_no_dates = report._get_report_sub_lines(
                data_no_dates, [r_type], False, False
            )
            self.assertIsInstance(sub_lines_no_dates, list)

    def test_04_get_report_values_and_inventory_report(self):
        """Test _get_report_values and inventory_report client action."""
        report = self.test_report

        # Test _get_report_values
        data = {
            'report_type': 'report_by_transfers',
            'model': report,
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        res = report._get_report_values(data)
        self.assertIn('INVENTORY', res)
        self.assertIn('docs', res)

        # Test fallback report type in _get_report_values
        data_other = {
            'report_type': 'custom_type',
            'model': report,
        }
        res_other = report._get_report_values(data_other)
        self.assertIn('INVENTORY', res_other)

        # Test when report_type is empty
        data_empty = {
            'report_type': False,
            'model': report,
        }
        res_empty = report._get_report_values(data_empty)
        self.assertIn('INVENTORY', res_empty)

        # Test inventory_report client action call
        action = self.report_model.inventory_report([report.id])
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('type'), 'ir.actions.client')
        self.assertEqual(action.get('tag'), 'inv_r')
        self.assertIn('filters', action)
        self.assertIn('orders', action)
        self.assertIn('report_lines', action)

        # Test inventory_report with report without dates
        report_no_dates = self.report_model.create({
            'report_type': 'report_by_warehouse',
        })
        action_no_dates = self.report_model.inventory_report(
            [report_no_dates.id]
        )
        self.assertEqual(action_no_dates.get('tag'), 'inv_r')

    def test_05_get_inventory_xlsx_report_all_types(self):
        """Test XLSX report generation across all report types."""
        report = self.test_report

        # 1. report_by_transfers
        response_transfers = MockResponse()
        filter_transfers = json.dumps({'report_type': 'report_by_transfers'})
        lines_transfers = json.dumps([{
            'name': 'WH/IN/0001',
            'scheduled_date': '2026-10-26 10:00:00',
            'origin': 'PO001',
            'company': 'Company Test',
            'partner': 'Partner Test',
            'state': 'done',
        }])
        report.get_inventory_xlsx_report(
            filter_transfers, response_transfers, lines_transfers, '{}'
        )
        self.assertGreater(len(response_transfers.stream.getvalue()), 0)

        # 2. report_by_categories
        response_categ = MockResponse()
        filter_categ = json.dumps({'report_type': 'report_by_categories'})
        lines_categ = json.dumps([{
            'category': 'All',
            'name': {'en_US': 'Test Product'},
            'create_date': '2026-10-26 10:00:00',
            'value_float': {'standard_price': 100.0},
            'location': 'WH/Stock',
            'quantity': 10.0,
        }])
        report.get_inventory_xlsx_report(
            filter_categ, response_categ, lines_categ, '{}'
        )
        self.assertGreater(len(response_categ.stream.getvalue()), 0)

        # 3. report_by_warehouse
        response_wh = MockResponse()
        filter_wh = json.dumps({'report_type': 'report_by_warehouse'})
        lines_wh = json.dumps([{
            'name': 'WH Test',
            'write_date': '2026-10-26 10:00:00',
            'company': 'Company Test',
            'location': 'WH/Stock',
            'route': {'en_US': 'Receipts Route'},
        }])
        report.get_inventory_xlsx_report(
            filter_wh, response_wh, lines_wh, '{}'
        )
        self.assertGreater(len(response_wh.stream.getvalue()), 0)

        # 4. report_by_location
        response_loc = MockResponse()
        filter_loc = json.dumps({'report_type': 'report_by_location'})
        lines_loc = json.dumps([{
            'complete_name': 'WH/Stock/Internal',
            'location_type': 'internal',
            'create_date': '2026-10-26 10:00:00',
            'company': 'Company Test',
        }])
        report.get_inventory_xlsx_report(
            filter_loc, response_loc, lines_loc, '{}'
        )
        self.assertGreater(len(response_loc.stream.getvalue()), 0)

    def test_06_pdf_report_and_views(self):
        """Test PDF report values computation and view actions."""
        pdf_model = self.env[
            'report.inventory_report_generator.inventory_pdf_report'
        ]
        test_data = {
            'report_data': {
                'report_lines': [{'name': 'Line 1'}],
                'filters': {'report_type': 'Report By Transfers'},
                'orders': {'date_from': self.date_from},
            }
        }

        # With inventory_pdf_report context
        res_pdf = pdf_model.with_context(
            inventory_pdf_report=True
        )._get_report_values([], data=dict(test_data))
        self.assertIn('report_main_line_data', res_pdf)
        self.assertIn('Filters', res_pdf)
        self.assertIn('Dates', res_pdf)
        self.assertIn('company', res_pdf)

        # Without inventory_pdf_report context
        res_raw = pdf_model._get_report_values([], data=dict(test_data))
        self.assertEqual(res_raw, test_data)

        # Test client action and menu exist
        action = self.env.ref(
            'inventory_report_generator.inventory_all_report_action'
        )
        self.assertTrue(action.exists())
        self.assertEqual(action.tag, 'inv_r')

        menu = self.env.ref(
            'inventory_report_generator.inventory_all_in_one_report'
        )
        self.assertTrue(menu.exists())
