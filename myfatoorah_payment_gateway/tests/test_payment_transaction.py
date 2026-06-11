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

from unittest.mock import patch, MagicMock
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestPaymentTransaction(TransactionCase):
    """Test PaymentTransaction model functions from models/payment_transaction.py"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        providers = cls.env['payment.provider'].search([('code', '=', 'myfatoorah')])
        if len(providers) > 1:
            providers[1:].unlink()
            
        cls.provider = providers[0] if providers else cls.env['payment.provider'].create({
            'name': 'Test MyFatoorah',
            'code': 'myfatoorah',
            'state': 'test',
            'myfatoorah_token': 'fake_token_123',
        })
        cls.provider.write({
            'state': 'test',
            'myfatoorah_token': 'fake_token_123',
        })
        cls.other_provider = cls.env['payment.provider'].create({
            'name': 'Other Provider',
            'code': 'none',
            'state': 'test',
        })
        cls.country = cls.env['res.country'].search([], limit=1)
        cls.country.phone_code = 999
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Partner',
            'phone': '+99912345678',
            'email': 'test@example.com',
            'country_id': cls.country.id,
            'street': 'Test Street',
            'city': 'Test City',
            'zip': '12345',
        })
        cls.currency = cls.env.company.currency_id

        cls.payment_method = cls.env['payment.method'].create({
            'name': 'Test Method',
            'code': 'test_method',
            'primary_payment_method_id': False,
        })

        cls.tx = cls.env['payment.transaction'].create({
            'amount': 100.0,
            'currency_id': cls.currency.id,
            'provider_id': cls.provider.id,
            'payment_method_id': cls.payment_method.id,
            'reference': 'TEST-REF-123',
            'partner_id': cls.partner.id,
        })
        cls.other_tx = cls.env['payment.transaction'].create({
            'amount': 50.0,
            'currency_id': cls.currency.id,
            'provider_id': cls.other_provider.id,
            'payment_method_id': cls.payment_method.id,
            'reference': 'TEST-REF-OTHER',
            'partner_id': cls.partner.id,
        })

    def test_get_specific_rendering_values_not_myfatoorah(self):
        """Test non-myfatoorah provider bypasses send_payment."""
        res = self.other_tx._get_specific_rendering_values({})
        self.assertNotIn('api_url', res)

    @patch('odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request')
    def test_send_payment_missing_phone(self, mock_request):
        """Test ValueError when phone is missing."""
        self.partner.phone = False
        self.tx.partner_phone = False
        with self.assertRaises(ValueError) as cm:
            self.tx.send_payment()
        self.assertIn("Please provide the phone number.", str(cm.exception))
        
        self.partner.phone = '+99912345678'
        self.tx.partner_phone = '+99912345678'

    @patch('odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request')
    def test_send_payment_api_error(self, mock_request):
        """Test ValidationError raised when MyFatoorah API returns an error."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'IsSuccess': False,
            'ValidationErrors': [{'Error': 'Invalid token'}]
        }
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError) as cm:
            self.tx.send_payment()
        self.assertIn("Invalid token", str(cm.exception))

    @patch('odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request')
    def test_send_payment_success(self, mock_request):
        """Test successful send_payment returns expected dictionary."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'IsSuccess': True,
            'Data': {'InvoiceURL': 'https://test.myfatoorah.com/checkout'}
        }
        mock_request.return_value = mock_response

        res = self.tx.send_payment()
        
        self.assertIn('api_url', res)
        self.assertIn('data', res)
        self.assertEqual(res['data']['InvoiceURL'], 'https://test.myfatoorah.com/checkout')
        self.assertEqual(res['data']['CustomerName'], 'Test Partner')
        self.assertEqual(res['data']['CustomerMobile'], '12345678')

    @patch('odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request')
    def test_get_tx_from_notification_data_success(self, mock_request):
        """Test fetching transaction on successful notification."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Data': {'CustomerReference': 'TEST-REF-123'}
        }
        mock_request.return_value = mock_response

        tx = self.env['payment.transaction']._get_tx_from_notification_data('myfatoorah', {'paymentId': '12345'})
        self.assertEqual(tx.id, self.tx.id)

    @patch('odoo.addons.myfatoorah_payment_gateway.models.payment_transaction.requests.request')
    def test_get_tx_from_notification_data_error(self, mock_request):
        """Test ValidationError when transaction not found."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'Data': {'CustomerReference': 'WRONG-REF'}
        }
        mock_request.return_value = mock_response

        with self.assertRaises(ValidationError) as cm:
            self.env['payment.transaction']._get_tx_from_notification_data('myfatoorah', {'paymentId': '12345'})
        self.assertIn("No transaction found matching reference", str(cm.exception))

    def test_process_notification_data(self):
        """Test that processing sets transaction to done."""
        self.tx.state = 'draft'
        self.tx._process_notification_data({})
        self.assertEqual(self.tx.state, 'done')
