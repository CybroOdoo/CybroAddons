# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anshad Ahammed M (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (
#    OPL-1) It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from datetime import datetime

@tagged('post_install', '-at_install')
class TestReportStockInventoryReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestReportStockInventoryReport, cls).setUpClass()
        cls.category = cls.env['product.category'].create({'name': 'Report Category'})
        cls.location = cls.env['stock.location'].create({
            'name': 'Report Location',
            'usage': 'internal'
        })
        
    def test_get_report_values(self):
        """Test the report values generation logic."""
        report_model = self.env['report.report_stock_inventory.report_stock_pdf']
        data = {
            'category': [self.category.id],
            'location': [self.location.id],
            'date': datetime.today(),
            'loc_name': self.location.name,
            'categ_name': self.category.name,
            'inventory_date': datetime.today().strftime('%Y-%m-%d')
        }
        
        res = report_model._get_report_values(docids=[], data=data)
        
        self.assertIn('docs', res)
        self.assertIn('loc_name', res)
        self.assertIn('categ_name', res)
        self.assertIn('report_date', res)
