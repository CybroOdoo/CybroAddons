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
from unittest.mock import MagicMock, Mock, patch
import json

@tagged('post_install', '-at_install')
class TestReportStockInventoryController(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_get_report_xlsx(self):
        """Test XLSX report controller endpoint logic."""
        import odoo.addons.report_stock_inventory.controllers.report_stock_inventory as cont
        
        # Setup mock environment
        mock_request = Mock()
        mock_env = MagicMock()
        mock_model = Mock()
        mock_env.__getitem__.return_value = mock_model
        mock_model.with_user.return_value = mock_model
        
        mock_request.env = mock_env
        mock_request.session.uid = 1
        from werkzeug.wrappers import Response
        mock_response = Response(b"Test", content_type='application/vnd.ms-excel')
        # mock set_cookie since we are returning a real response object
        mock_response.set_cookie = Mock()
        mock_request.make_response.return_value = mock_response
        
        # Manual monkeypatch to avoid Werkzeug LocalProxy unbound errors
        original_request = getattr(cont, 'request', None)
        cont.request = mock_request
        
        try:
            from odoo.addons.report_stock_inventory.controllers.report_stock_inventory import XLSXReportController
            controller = XLSXReportController()
            
            options = json.dumps({'test': 'data'})
            response = controller.get_report_xlsx(
                model='out.of.stock.report',
                options=options,
                output_format='xlsx'
            )
            
            self.assertTrue(mock_model.get_xlsx_report.called)
            self.assertEqual(response, mock_response)
            
            # Test error handling
            mock_model.get_xlsx_report.side_effect = Exception("Test Error")
            
            with patch('odoo.http.serialize_exception') as mock_serialize:
                mock_serialize.return_value = 'Serialized Error'
                error_response = controller.get_report_xlsx(
                    model='out.of.stock.report',
                    options=options,
                    output_format='xlsx'
                )
                self.assertTrue(mock_request.make_response.called)
        finally:
            if original_request is not None:
                cont.request = original_request
