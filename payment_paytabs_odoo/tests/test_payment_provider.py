# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
from unittest.mock import MagicMock, patch
import requests

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tools import mute_logger

from odoo.addons.payment_paytabs_odoo.tests.common import PaytabsCommon


@tagged('post_install', '-at_install')
class TestPaymentProvider(PaytabsCommon):

    def test_provider_credentials(self):
        """ Test that the PayTabs provider has the configured credentials. """
        self.assertEqual(self.provider.code, 'paytabs')
        self.assertEqual(self.provider.profile_key, self.profile_id)
        self.assertEqual(self.provider.api_key, self.api_key)
        self.assertEqual(self.provider.domain, self.api_url)

    def test_get_payment_method_information(self):
        """ Test that PayTabs payment method information is correctly registered. """
        res = self.env['payment.provider']._get_payment_method_information()
        self.assertIn('paytabs', res)
        self.assertDictEqual(
            res['paytabs'],
            {'mode': 'unique', 'domain': [('type', '=', 'bank')]}
        )

    def test_paytabs_make_request_success(self):
        """ Test that a successful API request returns the parsed JSON response. """
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'redirect_url': self.redirect_url,
            'tran_ref': self.tran_ref,
        }
        with patch('requests.request', return_value=mock_response) as mock_req:
            res = self.provider._paytabs_make_request(
                self.api_url, data={'test': 'value'}, method='POST', expect_redirect=True
            )
            mock_req.assert_called_once_with(
                'POST',
                self.api_url,
                json={'test': 'value'},
                headers={
                    'Authorization': self.api_key,
                    'Content-Type': 'application/json',
                },
                timeout=60,
            )
            self.assertEqual(res['redirect_url'], self.redirect_url)
            self.assertEqual(res['tran_ref'], self.tran_ref)

    def test_paytabs_make_request_pops_api_url(self):
        """ Test that 'api_url' is safely removed from the request payload before sending. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'status': 'ok'}
        data = {'api_url': 'https://ignore.me', 'cart_id': '123'}
        with patch('requests.request', return_value=mock_response) as mock_req:
            self.provider._paytabs_make_request(self.api_url, data=data)
            sent_payload = mock_req.call_args.kwargs.get('json')
            self.assertNotIn('api_url', sent_payload)
            self.assertIn('cart_id', sent_payload)

    def test_paytabs_make_request_invalid_credentials_code_1(self):
        """ Test that API response with error code 1 raises ValidationError for invalid credentials. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 1, 'message': 'Unauthorized'}
        with patch('requests.request', return_value=mock_response):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={})
            self.assertIn("Check profile ID and Api Key", str(cm.exception))

    def test_paytabs_make_request_currency_not_available_code_206(self):
        """ Test that API response with error code 206 raises ValidationError for currency issue. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 206, 'message': 'Currency not available'}
        with patch('requests.request', return_value=mock_response):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={})
            self.assertIn("Currency not available", str(cm.exception))

    def test_paytabs_make_request_invalid_callback_url_code_210(self):
        """ Test that API response with error code 210 raises ValidationError for invalid callback URL. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 210, 'message': 'http://localhost'}
        with patch('requests.request', return_value=mock_response):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={})
            self.assertIn("Invalid Callback URL", str(cm.exception))
            self.assertIn("http://localhost", str(cm.exception))

    def test_paytabs_make_request_generic_error_code(self):
        """ Test that API response with any generic error code raises a formatted ValidationError. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'code': 500, 'message': 'Internal Server Error'}
        with patch('requests.request', return_value=mock_response):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={})
            self.assertIn("PayTabs API Error (Code 500)", str(cm.exception))

    def test_paytabs_make_request_expect_redirect_missing(self):
        """ Test that missing redirect_url when expect_redirect=True raises ValidationError. """
        mock_response = MagicMock()
        mock_response.json.return_value = {'tran_ref': 'TST123'}  # missing redirect_url
        with patch('requests.request', return_value=mock_response):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={}, expect_redirect=True)
            self.assertIn("Invalid response received from PayTabs API", str(cm.exception))

    @mute_logger('odoo.addons.payment_paytabs_odoo.models.payment_provider')
    def test_paytabs_make_request_connection_error(self):
        """ Test that a network exception raises ValidationError. """
        with patch('requests.request', side_effect=requests.exceptions.ConnectionError):
            with self.assertRaises(ValidationError) as cm:
                self.provider._paytabs_make_request(self.api_url, data={})
            self.assertIn("Could not establish a connection to the API", str(cm.exception))

