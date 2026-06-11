# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.addons.myfatoorah_payment_gateway.controllers.myfatoorah_payment_gateway import PaymentMyFatoorahController
import odoo.addons.myfatoorah_payment_gateway.controllers.myfatoorah_payment_gateway as controller_module


@tagged('post_install', '-at_install')
class TestMyFatoorahController(TransactionCase):
    """Test PaymentMyFatoorahController functions from controllers/myfatoorah_payment_gateway.py"""

    def test_myfatoorah_payment_response(self):
        """Test myfatoorah_payment_response correctly parses data and renders form."""
        mock_request = MagicMock()
        mock_request.render.return_value = "rendered_response"
        
        old_request = controller_module.request
        controller_module.request = mock_request
        try:
            controller = PaymentMyFatoorahController()
            
            payment_data_dict = {
                "CustomerName": "Test User",
                "DisplayCurrencyIso": "USD",
                "CustomerMobile": "123456789",
                "InvoiceValue": 100.0,
                "CustomerAddress": {"Address": "Test Address"},
                "InvoiceURL": "https://test.url",
            }
            data = {"data": str(payment_data_dict)}
            
            result = controller.myfatoorah_payment_response(**data)
            
            self.assertEqual(result.data, b"rendered_response")
            expected_vals = {
                'customer': "Test User",
                'currency': "USD",
                'mobile': "123456789",
                'invoice_amount': 100.0,
                'address': "Test Address",
                'payment_url': "https://test.url",
            }
            mock_request.render.assert_called_once_with("myfatoorah_payment_gateway.myfatoorah_payment_gateway_form", expected_vals)
        finally:
            controller_module.request = old_request

    def test_myfatoorah_checkout(self):
        """Test myfatoorah_checkout correctly calls models and redirects."""
        mock_request = MagicMock()
        mock_request.redirect.return_value = "redirected_status"
        
        mock_tx_sudo = MagicMock()
        mock_request.env.__getitem__.return_value.sudo.return_value._get_tx_from_notification_data.return_value = mock_tx_sudo
        
        old_request = controller_module.request
        controller_module.request = mock_request
        try:
            controller = PaymentMyFatoorahController()
            test_data = {"some_key": "some_value"}
            
            result = controller.myfatoorah_checkout(**test_data)
            
            self.assertEqual(result.data, b"redirected_status")
            
            mock_request.env.__getitem__.return_value.sudo.return_value._get_tx_from_notification_data.assert_called_once_with('myfatoorah', test_data)
            mock_tx_sudo._handle_notification_data.assert_called_once_with('myfatoorah', test_data)
            mock_request.redirect.assert_called_once_with('/payment/status')
        finally:
            controller_module.request = old_request

    def test_payment_failed(self):
        """Test payment_failed correctly renders the failed form."""
        mock_request = MagicMock()
        mock_request.render.return_value = "rendered_failed"
        
        old_request = controller_module.request
        controller_module.request = mock_request
        try:
            controller = PaymentMyFatoorahController()
            result = controller.payment_failed()
            
            self.assertEqual(result.data, b"rendered_failed")
            mock_request.render.assert_called_once_with("myfatoorah_payment_gateway.myfatoorah_payment_gateway_failed_form")
        finally:
            controller_module.request = old_request
