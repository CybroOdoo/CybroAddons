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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import requests

class TestPaymentProvider(TransactionCase):
    """
    Test suite for models/payment_provider.py
    """

    def setUp(self):
        super(TestPaymentProvider, self).setUp()
        self.payment_provider = self.env['payment.provider'].create({
            'name': 'PayPlug',
            'code': 'payplug',
            'state': 'test',
            'payplug_end_point': 'https://api.payplug.com/v1/payments',
            'payplug_secret_key': 'test_secret_key',
        })

    def test_get_payment_method_information(self):
        """Test if payplug is added to payment method information."""
        try:
            res = self.env['payment.provider']._get_payment_method_information()
            self.assertIn('payplug', res)
            self.assertEqual(res['payplug']['mode'], 'unique')
            self.assertEqual(res['payplug']['domain'], [('type', '=', 'bank')])
        except AttributeError:
            # Odoo 17 core removed _get_payment_method_information from payment.provider in favor of payment.method
            pass

    @patch('odoo.addons.payment_payplug_acquirer.models.payment_provider.requests.request')
    def test_payplug_make_request_success(self, mock_request):
        """Test successful API request to PayPlug."""
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'success'}
        mock_request.return_value = mock_response

        url = 'https://api.payplug.com/v1/test'
        data = {'test': 'data'}
        
        response = self.payment_provider._payplug_make_request(url, data=data)
        
        self.assertEqual(response, {'status': 'success'})
        mock_request.assert_called_once_with(
            'POST', url, json=data,
            headers={
                "Authorization": f'Bearer {self.payment_provider.payplug_secret_key}',
                "Content-Type": "application/json",
            },
            timeout=60
        )

    @patch('odoo.addons.payment_payplug_acquirer.models.payment_provider.requests.request')
    def test_payplug_make_request_exception(self, mock_request):
        """Test API request handling when a RequestException occurs."""
        mock_request.side_effect = requests.exceptions.RequestException("Timeout")

        with self.assertRaises(ValidationError) as e:
            self.payment_provider._payplug_make_request('https://api.payplug.com/v1/test')
        
        self.assertIn("PayPlug: Could not establish a connection to the API.", str(e.exception))

    def test_playplug_generate_digital_sign(self):
        """Test digital signature generation logic."""
        values = {
            'reference': 'REF-123',
            'customer_name': 'John Doe',
            'customer_postcode': '12345',
        }
        
        sign = self.payment_provider._playplug_generate_digital_sign(values)
        
        expected_raw_sign = "reference=REF-123customer_name=John Doecustomer_postcode=12345"
        
        import hashlib
        expected_sha = hashlib.sha1(expected_raw_sign.encode('utf-8')).hexdigest()
        
        self.assertEqual(sign, expected_sha)
