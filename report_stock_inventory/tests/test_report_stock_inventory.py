# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import json
from odoo.tests.common import TransactionCase
from odoo.addons.report_stock_inventory.controllers.report_stock_inventory import XLSXReportController
from unittest.mock import patch, MagicMock
from datetime import datetime
import logging


_logger = logging.getLogger(__name__)


class TestReportStockInventory(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create category and product
        cls.category = cls.env['product.category'].create({'name': 'Test Category'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu', # Standard 'consu'
            'is_storable': True,
            'categ_id': cls.category.id,
        })
        
        # Create locations
        cls.location = cls.env['stock.location'].create({
            'name': 'Test Location',
            'usage': 'internal',
            'company_id': cls.env.user.company_id.id
        })
        
        # Create stock quant to have some available_quantity
        cls.quant = cls.env['stock.quant'].create({
            'product_id': cls.product.id,
            'location_id': cls.location.id,
            'inventory_quantity': 10,
        })
        cls.quant.action_apply_inventory()
        
        # Setup Inventory Report Wizard
        cls.wizard = cls.env['stock.quantity.history'].create({
            'location': [(6, 0, [cls.location.id])],
            'category': [(6, 0, [cls.category.id])],
            'inventory_datetime': datetime.now(),
        })

    def test_action_xlsx_report(self):
        _logger.info('success1')
        """Test action_xlsx_report generates correct dict for XLSX report."""
        res = self.wizard.action_xlsx_report()
        self.assertEqual(res['type'], 'ir.actions.report')
        self.assertEqual(res['report_type'], 'xlsx')
        data_options = json.loads(res['data']['options'])
        self.assertIn(self.location.id, data_options['location'])
        self.assertIn(self.category.id, data_options['category'])
        self.assertEqual(data_options['loc_name'], self.location.display_name)
        _logger.info('success2')

    def test_action_print_pdf(self):
        _logger.info('success3')
        """Test action_print_pdf returns report action correctly."""
        res = self.wizard.action_print_pdf()
        self.assertIn(res.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
        _logger.info('success3')
        
    def test_get_xlsx_report(self):
        _logger.info('success4')
        """Test get_xlsx_report writes data into response stream."""
        # Mock response object
        response = MagicMock()
        response.stream = MagicMock()
        
        data = {
            'location': [self.location.id],
            'category': [self.category.id],
            'date': self.wizard.inventory_datetime,
            'loc_name': self.location.display_name,
            'categ_name': self.category.name,
            'inventory_date': '2026-05-11'
        }
        
        self.wizard.get_xlsx_report(data, response)
        self.assertTrue(response.stream.write.called)
        _logger.info('success5')

    def test_get_report_values_pdf(self):
        _logger.info('success6')
        """Test the PDF report generation logic."""
        data = {
            'location': [self.location.id],
            'category': [self.category.id],
            'date': self.wizard.inventory_datetime,
            'loc_name': self.location.display_name,
            'categ_name': self.category.name,
            'inventory_date': '2026-05-11'
        }
        report_model = self.env['report.report_stock_inventory.report_stock_pdf']
        res = report_model._get_report_values([], data)
        
        self.assertIn('docs', res)
        self.assertTrue(len(res['docs']) > 0)
        self.assertEqual(res['docs'][0]['product'].id, self.product.id)
        self.assertEqual(res['docs'][0]['qty_available'], 10.0)
        _logger.info('success7')

    def test_xlsx_controller(self):
        _logger.info('success7')
        """Test XLSXReportController get_report_xlsx function."""
        # Manually mock request to avoid werkzeug LocalProxy unbind errors during patch inspection
        from werkzeug.wrappers import Response
        
        mock_request = MagicMock()
        mock_env = MagicMock()
        mock_request.env = mock_env
        mock_request.session.uid = 1
        
        # Mock response with an actual werkzeug Response to satisfy Odoo's @http.route wrapper
        mock_response = Response(b"Test Data")
        mock_request.make_response.return_value = mock_response
        
        controller = XLSXReportController()
        
        import odoo.addons.report_stock_inventory.controllers.report_stock_inventory as controller_mod
        original_request = controller_mod.request
        controller_mod.request = mock_request
        
        try:
            options = json.dumps({'location': [], 'category': [], 'date': False, 'loc_name': '', 'categ_name': '', 'inventory_date': ''})
            res = controller.get_report_xlsx('stock.quantity.history', options, 'xlsx')
            
            # check if it returns response correctly and gets called
            self.assertEqual(res, mock_response)
            mock_request.make_response.assert_called()
            
            # Test exception catching
            mock_model = MagicMock()
            mock_env['stock.quantity.history'].with_user.return_value = mock_model
            mock_model.get_xlsx_report.side_effect = Exception("Test Error")
            
            res_error = controller.get_report_xlsx('stock.quantity.history', options, 'xlsx')
            self.assertEqual(res_error, mock_response)
        finally:
            controller_mod.request = original_request

    def test_open_at_date(self):
        """Test open_at_date returns correct action with applied filters."""
        res = self.wizard.open_at_date()
        self.assertEqual(res['type'], 'ir.actions.act_window')
        self.assertEqual(res['res_model'], 'product.product')
        self.assertIn(self.location.id, res['context'].get('location', []))
        self.assertEqual(res['context'].get('to_date'), self.wizard.inventory_datetime)

    def test_open_at_date_no_data(self):
        """Test open_at_date raises UserError when no data exists for criteria."""
        empty_location = self.env['stock.location'].create({
            'name': 'Empty Location',
            'usage': 'internal',
            'company_id': self.env.user.company_id.id
        })
        wizard = self.env['stock.quantity.history'].create({
            'location': [(6, 0, [empty_location.id])],
            'inventory_datetime': datetime.now(),
        })
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            wizard.open_at_date()

