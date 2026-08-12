# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from unittest.mock import patch
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.addons.bitpay_payment_gateway.tests.common import BitPayCommon


@tagged('post_install', '-at_install', 'bitpay_payment_gateway')
class TestPaymentProvider(BitPayCommon):
    """Test Suite for PaymentProvider Model Methods in BitPay Payment Gateway."""

    def test_bitpay_get_api_url(self):
        """Test API URL Resolution for Test and Production Environments."""
        self.provider.state = 'test'
        self.assertEqual(self.provider._bitpay_get_api_url(), 'https://test.bitpay.com')

        self.provider.state = 'enabled'
        self.assertEqual(self.provider._bitpay_get_api_url(), 'https://bitpay.com')

    def test_bitpay_make_request_missing_token(self):
        """Test API Request Validation When POS Token Is Missing."""
        self.provider.bitpay_pos_token = False
        with self.assertRaises(ValidationError):
            self.provider._bitpay_make_request('invoices')

    @patch('requests.request')
    def test_bitpay_make_request_success(self, mock_request):
        """Test Successful BitPay API Request Execution."""
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = {'data': {'id': 'TestInvoice123'}}

        response = self.provider._bitpay_make_request('invoices', payload={'price': 100})
        self.assertEqual(response, {'id': 'TestInvoice123'})
        mock_request.assert_called_once()

    def test_get_default_payment_method_codes(self):
        """Test Default Payment Method Codes List Includes BitPay."""
        codes = self.provider._get_default_payment_method_codes()
        self.assertIn('bitpay', codes)
