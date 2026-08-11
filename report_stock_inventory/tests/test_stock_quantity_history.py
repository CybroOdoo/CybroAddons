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
from datetime import datetime

@tagged('post_install', '-at_install')
class TestStockQuantityHistory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestStockQuantityHistory, cls).setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, lang='en_US'))
        cls.category = cls.env['product.category'].create({'name': 'Test Qty History Category'})
        cls.location = cls.env['stock.location'].create({
            'name': 'Test Location Qty History',
            'usage': 'internal'
        })
        
    def test_action_xlsx_report(self):
        """Test XLSX report data generation."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': datetime.now(),
        })
        wizard.category = [(4, self.category.id)]
        wizard.location = [(4, self.location.id)]
        
        action = wizard.action_xlsx_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'xlsx')
        
        # Test get_xlsx_report
        import json
        options = json.loads(action['data']['options'])
        mock_response = Mock()
        mock_response.stream = Mock()
        
        wizard.get_xlsx_report(options, mock_response)
        self.assertTrue(mock_response.stream.write.called)

    def test_action_print_pdf(self):
        """Test PDF report data generation."""
        wizard = self.env['stock.quantity.history'].create({
            'inventory_datetime': datetime.now(),
        })
        wizard.category = [(4, self.category.id)]
        wizard.location = [(4, self.location.id)]
        
        action = wizard.action_print_pdf()
        self.assertIn(action.get('type'), ('ir.actions.report', 'ir.actions.act_window'))
        
        report_action = action.get('context', {}).get('report_action', action)
        self.assertIn('data', report_action)
        data = report_action['data']
        self.assertIn('loc_name', data)
        self.assertIn('categ_name', data)
