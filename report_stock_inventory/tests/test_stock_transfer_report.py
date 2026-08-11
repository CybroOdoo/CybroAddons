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
from unittest.mock import Mock

@tagged('post_install', '-at_install')
class TestStockTransferReport(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockTransferReport, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))
        cls.company = cls.env.company
        cls.category = cls.env['product.category'].create({'name': 'Test Transfer Category'})
        cls.location = cls.env['stock.location'].create({
            'name': 'Test Location Transfer',
            'usage': 'internal'
        })
        
    def test_action_print_pdf_report(self):
        """Test PDF report generation."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.category.id,
            'company_id': self.company.id,
            'location_id': self.location.id,
        })
        action = wizard.action_print_pdf_report()
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))
        report_action = action.get('context', {}).get('report_action', action)
        data = report_action.get('data', {})
        self.assertIn('stock_picking', data)

    def test_action_print_xls_report(self):
        """Test XLSX report generation."""
        wizard = self.env['stock.transfer.report'].create({
            'product_category_id': self.category.id,
            'company_id': self.company.id,
            'location_id': self.location.id,
        })
        action = wizard.action_print_xls_report()
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))
        
        report_action = action.get('context', {}).get('report_action', action)
        import json
        options = json.loads(report_action['data']['options'])
        mock_response = Mock()
        mock_response.stream = Mock()
        
        wizard.get_xlsx_report(options, mock_response)
        self.assertTrue(mock_response.stream.write.called)
