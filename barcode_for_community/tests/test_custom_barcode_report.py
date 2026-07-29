# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests.common import TransactionCase
from unittest.mock import patch, MagicMock

class TestBarcodeDataReport(TransactionCase):
    """Test suite for verifying the Custom Barcode PDF Report data generation."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and initialize custom barcode report class instance."""
        super(TestBarcodeDataReport, cls).setUpClass()
        cls.report = cls.env['report.barcode_for_community.barcode_data_report']

    def test_get_report_values_product(self):
        """Test getting report values for product format"""
        # Setup mock product via context data map
        data = {
            'mode': 'product.product'
        }
        res = self.report._get_report_values(docids=[], data=data)
        self.assertEqual(res.get('mode'), 'product.product')
        self.assertIn('items', res)

    def test_get_report_values_stock_location(self):
        """Test getting report values for stock location format"""
        # Setup mock data 
        data = {
            'mode': 'stock.location'
        }
        res = self.report._get_report_values(docids=[], data=data)
        self.assertEqual(res.get('mode'), 'stock.location')
        self.assertIn('items', res)
